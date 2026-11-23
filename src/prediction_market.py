"""Prediction Market: trade "who wins the race" with play money, against an automated market maker.

THE MARKET MAKER is Hanson's logarithmic market scoring rule (LMSR). There is one share per driver; a share
pays 100 coins if that driver wins. With q_i shares of driver i sold so far and a prior p0_i,
    price_i = 100 * softmax(log p0 + q / B)_i
    cost of buying shares d = C(q + d) - C(q),   C(q) = 100 * B * log(sum_i p0_i * exp(q_i / B))
so buying pushes a price up and selling pushes it down, and nobody needs someone on the other side.
The prior p0 is our model's win chance for the race: the market opens where the model is, and every trade
moves it towards what visitors think. The gap between the two is the crowd's disagreement with the model.

EACH PLAYER gets 1,000 coins for every race. Trading closes at lights out. After the race the winner's
shares pay 100 coins each, and a player's profit is what they end with minus 1,000. The season table
adds up profit across races.

Trades are stored in the Supabase table `market_trades` (the server-side key, like Beat the AI), or in
data/market_trades_local.json without a database. Every trade is priced on the server.

    create table market_trades (id bigint generated always as identity primary key, player text not null,
      season int not null, round int not null, driver text not null, shares double precision not null,
      cost double precision not null, nickname text, created_at timestamptz default now());
    alter table market_trades enable row level security;
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

import picks

ROOT = Path(__file__).resolve().parent.parent
LOCAL_FILE = ROOT / "data" / "market_trades_local.json"
TABLE = "market_trades"
B = 40.0                  # liquidity: how many shares it takes to move a price a long way
PAYOUT = 100.0
BANK = 1000.0
FLOOR = 0.002             # no driver opens below a 0.2% chance


def prior(chances):
    """{driver: win chance in %} -> normalised probabilities with a floor."""
    p = {d: max(float(c) / 100, FLOOR) for d, c in chances.items()}
    s = sum(p.values())
    return {d: v / s for d, v in p.items()}


def _cost(p0, q):
    drivers = list(p0)
    x = np.array([np.log(p0[d]) + q.get(d, 0.0) / B for d in drivers])
    m = x.max()
    return PAYOUT * B * (m + np.log(np.exp(x - m).sum()))


def prices(p0, q):
    drivers = list(p0)
    x = np.array([np.log(p0[d]) + q.get(d, 0.0) / B for d in drivers])
    e = np.exp(x - x.max())
    return dict(zip(drivers, PAYOUT * e / e.sum()))


def quote(p0, q, driver, shares):
    """Coins it costs to buy `shares` of driver (negative shares = selling, negative cost = coins back)."""
    q2 = dict(q)
    q2[driver] = q2.get(driver, 0.0) + shares
    return float(_cost(p0, q2) - _cost(p0, q))


def shares_for(p0, q, driver, coins):
    """How many shares `coins` buys (bisection on the cost)."""
    lo, hi = 0.0, 1.0
    while quote(p0, q, driver, hi) < coins and hi < 1e5:
        hi *= 2
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if quote(p0, q, driver, mid) < coins else (lo, mid)
    return lo


def book(trades):
    """Total shares sold per driver."""
    q = {}
    for t in trades:
        q[t["driver"]] = q.get(t["driver"], 0.0) + float(t["shares"])
    return q


def position(trades, player):
    """(cash left, {driver: shares held}) for one player."""
    mine = [t for t in trades if t["player"] == player]
    held = {}
    for t in mine:
        held[t["driver"]] = held.get(t["driver"], 0.0) + float(t["shares"])
    return BANK - sum(float(t["cost"]) for t in mine), {d: s for d, s in held.items() if abs(s) > 1e-6}


def settle(trades, winner):
    """{player: (profit, nickname)} once the winner is known."""
    out = {}
    for p in {t["player"] for t in trades}:
        cash, held = position(trades, p)
        nick = next((t.get("nickname") for t in reversed(trades) if t["player"] == p and t.get("nickname")), None)
        out[p] = (cash + PAYOUT * held.get(winner, 0.0) - BANK, nick)
    return out


# ---------- storage ----------

def _read_local():
    return json.loads(LOCAL_FILE.read_text()) if LOCAL_FILE.exists() else []


def trades(season, rnd=None):
    conf = picks._supabase()
    if conf:
        import requests
        url, key = conf
        params = {"season": f"eq.{season}", "select": "*", "order": "id.asc", "limit": 10000}
        if rnd is not None:
            params["round"] = f"eq.{rnd}"
        r = requests.get(f"{url}/rest/v1/{TABLE}", params=params, headers=picks._headers(key), timeout=15)
        r.raise_for_status()
        return r.json()
    return [t for t in _read_local() if t["season"] == season and (rnd is None or t["round"] == rnd)]


def record(player, season, rnd, driver, shares, cost, nickname=""):
    row = {"player": player, "season": int(season), "round": int(rnd), "driver": driver,
           "shares": round(float(shares), 4), "cost": round(float(cost), 2),
           "nickname": (nickname or "").strip()[:20] or None,
           "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    conf = picks._supabase()
    if conf:
        import requests
        url, key = conf
        r = requests.post(f"{url}/rest/v1/{TABLE}", json=row,
                          headers={**picks._headers(key), "Prefer": "return=minimal"}, timeout=15)
        r.raise_for_status()
        return
    rows = _read_local()
    row["id"] = len(rows) + 1
    LOCAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOCAL_FILE.write_text(json.dumps(rows + [row], indent=1))


def trade(player, season, rnd, p0, driver, coins=None, shares=None, nickname=""):
    """Buy with `coins`, or sell `shares` (positive number). Priced against the latest book. Returns
    (shares, cost) or raises ValueError with a sentence for the visitor."""
    all_trades = trades(season, rnd)
    q = book(all_trades)
    cash, held = position(all_trades, player)
    if coins is not None:
        coins = min(float(coins), cash)
        if coins < 1:
            raise ValueError("You've no coins left for this race. Sell something first.")
        n = shares_for(p0, q, driver, coins)
        cost = quote(p0, q, driver, n)
    else:
        n = -min(float(shares), held.get(driver, 0.0))
        if n > -1e-6:
            raise ValueError("You don't hold any shares in that driver.")
        cost = quote(p0, q, driver, n)
    record(player, season, rnd, driver, n, cost, nickname)
    return n, cost
