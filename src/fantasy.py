"""Fantasy Optimizer: the best budget-capped fantasy team for a race, from the model's predictions.

THE GAME (our own rules in the style of the usual F1 fantasy games; prices are ours too, since the official
ones aren't public data):
  a team is 5 drivers and 2 constructors within a budget (100 by default), and one driver is captain
  (double points)
  a driver scores race points (25, 18, 15, 12, 10, 8, 6, 4, 2, 1), plus 1 for every place gained on the
  grid and minus 1 for every place lost (at most 10 either way), and -20 for not finishing
  a constructor scores its two drivers' race points
PRICES come from form: each driver's (and team's) average race points over their last 8 races, on a scale
from 4.5 set so the five dearest drivers and two dearest teams cost 1.4 budgets (the dream team never fits).

EXPECTED POINTS. The model gives every driver a strength; the race is replayed 20,000 times the way the
predictor does (Plackett-Luce: strength plus Gumbel noise), with each driver failing to finish at their
own rate (their career and recent DNF rates). For a past race the strengths come from the backtest (a
model trained only on earlier seasons): under Plackett-Luce a driver's win chance is proportional to
exp(strength), so log(win chance) is the strength.

THE OPTIMIZER is an integer program (scipy's milp): binary pick and captain variables, maximise expected
points subject to the budget, 5 drivers, 2 constructors and a captain who is in the team.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, milp

sys.path.insert(0, str(Path(__file__).resolve().parent))
from predictor import FEATURES_CSV, ROOT, clean_name

BACKTEST = ROOT / "data" / "predictions" / "backtest_probs.csv"
POINTS = np.array([25, 18, 15, 12, 10, 8, 6, 4, 2, 1] + [0] * 30, dtype=float)
DNF_PTS = -20.0
PLACES_CAP = 10
N_DRIVERS, N_TEAMS, BUDGET = 5, 2, 100.0
FORM_RACES = 8
PRICE_LO, PRICE_HI = 4.5, 35.0
STRETCH = 1.4                  # the dream team costs 1.4 budgets
SIMS = 20000
COLS = ["season", "round", "race_name", "driver", "constructor", "grid", "finish_position", "dnf",
        "driver_dnf_rate", "driver_form_dnf"]


def results():
    return pd.read_csv(FEATURES_CSV, usecols=COLS)


def score_rows(finish, grid, dnf):
    """Fantasy points for real (or simulated) results. Arrays of equal shape."""
    finish, grid = np.asarray(finish, dtype=float), np.asarray(grid, dtype=float)
    grid = np.where((grid <= 0) | np.isnan(grid), 20, grid)                # pit-lane starts count as P20
    race = POINTS[np.clip(finish, 1, len(POINTS)).astype(int) - 1]
    places = np.clip(grid - finish, -PLACES_CAP, PLACES_CAP)
    driver = np.where(dnf, DNF_PTS, race + places)
    return driver, np.where(dnf, 0.0, race)                                  # (driver score, race points)


def actual_points(race):
    """Each driver's real fantasy score, and each team's."""
    d, rp = score_rows(race["finish_position"].fillna(len(race)), race["grid"], race["dnf"].astype(bool))
    drivers = pd.Series(d, index=race["driver"].to_numpy())
    teams = pd.Series(rp, index=race["constructor"].to_numpy()).groupby(level=0).sum()
    return drivers, teams


def prices(season, rnd, data=None, field=None):
    """Prices before (season, rnd), from each driver's and team's race points in their last FORM_RACES races
    (place bonuses and DNF penalties left out: they swing too much to price on). The scale is set so the five
    dearest drivers and two dearest teams together cost STRETCH times the budget: the best team never fits.
    `field` = (drivers, teams) in this race: anyone without recent races (a rookie) gets the lowest price."""
    df = results() if data is None else data
    before = df[(df["season"] < season) | ((df["season"] == season) & (df["round"] < rnd))]
    keys = before[["season", "round"]].drop_duplicates().sort_values(["season", "round"]).tail(FORM_RACES * 3)
    d_hist, t_hist = {}, {}
    for _, race in before.merge(keys).sort_values(["season", "round"]).groupby(["season", "round"]):
        _, rp = score_rows(race["finish_position"].fillna(len(race)), race["grid"], race["dnf"].astype(bool))
        for k, v in zip(race["driver"], rp):
            d_hist.setdefault(k, []).append(v)
        for k, v in pd.Series(rp, index=race["constructor"].to_numpy()).groupby(level=0).sum().items():
            t_hist.setdefault(k, []).append(v)
    d_form = {k: float(np.mean(v[-FORM_RACES:])) for k, v in d_hist.items()}
    t_form = {k: float(np.mean(v[-FORM_RACES:])) for k, v in t_hist.items()}
    if field is not None:
        d_form = {k: d_form.get(k, 0.0) for k in field[0]}
        t_form = {k: t_form.get(k, 0.0) for k in field[1]}

    def scale(form, n, target):
        top = sorted(form.values(), reverse=True)[:n]
        k = max(target - PRICE_LO * n, 1) / max(sum(top), 1)
        return {key: float(min(PRICE_HI, round((PRICE_LO + k * v) * 2) / 2)) for key, v in form.items()}

    total = STRETCH * BUDGET
    return scale(d_form, N_DRIVERS, total * 0.65), scale(t_form, N_TEAMS, total * 0.35), d_form, t_form


def expected_points(race, strength, seed=0):
    """Expected driver and team fantasy points from strengths (in Plackett-Luce units), by simulation."""
    rng = np.random.default_rng(seed)
    n = len(race)
    p_dnf = np.clip(0.5 * (race["driver_dnf_rate"].fillna(0.1) + race["driver_form_dnf"].fillna(0.1)), 0.03, 0.35).to_numpy()
    g = np.asarray(strength)[None, :] + rng.gumbel(size=(SIMS, n))
    out = rng.random((SIMS, n)) < p_dnf
    g = np.where(out, -1e9 + g, g)                                          # retirements drop to the back
    finish = (-g).argsort(axis=1).argsort(axis=1) + 1
    grid = np.broadcast_to(race["grid"].to_numpy(dtype=float), (SIMS, n))
    d, rp = score_rows(finish, grid, out)
    exp_d = pd.Series(d.mean(axis=0), index=race["driver"].to_numpy())
    teams = race["constructor"].to_numpy()
    exp_t = pd.Series({t: rp[:, teams == t].sum(axis=1).mean() for t in np.unique(teams)})
    return exp_d, exp_t


def backtest_strength(race_bt):
    """Strengths from out-of-sample win chances: log(win chance); never-winners keep the model's order."""
    w = race_bt["win_chance"].to_numpy(dtype=float)
    floor = max(w[w > 0].min() if (w > 0).any() else 1e-3, 1e-4)
    s = np.log(np.where(w > 0, w, floor / 2))
    order = race_bt["predicted_position"].to_numpy(dtype=float)
    return s - 0.05 * (order - order.min()) * (w <= 0)


def optimise(exp_d, exp_t, price_d, price_t, budget=BUDGET, must=(), never=()):
    """The best team: (drivers, teams, captain, expected points, cost), or None if none fits."""
    drivers = [d for d in exp_d.index if d in price_d and d not in never]
    teams = [t for t in exp_t.index if t in price_t and t not in never]
    nd, nt = len(drivers), len(teams)
    if nd < N_DRIVERS or nt < N_TEAMS:
        return None
    # variables: x (drivers), y (teams), c (captain among drivers)
    ed = np.array([exp_d[d] for d in drivers])
    et = np.array([exp_t[t] for t in teams])
    obj = -np.r_[ed, et, ed]
    pd_, pt = np.array([price_d[d] for d in drivers]), np.array([price_t[t] for t in teams])
    z = lambda k: np.zeros(k)
    A = [np.r_[pd_, pt, z(nd)], np.r_[np.ones(nd), z(nt), z(nd)], np.r_[z(nd), np.ones(nt), z(nd)],
         np.r_[z(nd), z(nt), np.ones(nd)]]
    lo, hi = [0, N_DRIVERS, N_TEAMS, 1], [budget, N_DRIVERS, N_TEAMS, 1]
    for i in range(nd):                                                       # captain must be picked
        row = z(2 * nd + nt)
        row[nd + nt + i] = 1
        row[i] = -1
        A.append(row); lo.append(-np.inf); hi.append(0)
    lb, ub = np.zeros(2 * nd + nt), np.ones(2 * nd + nt)
    for k in must:
        if k in drivers:
            lb[drivers.index(k)] = 1
        elif k in teams:
            lb[nd + teams.index(k)] = 1
    res = milp(obj, constraints=LinearConstraint(np.array(A), lo, hi), integrality=np.ones(2 * nd + nt),
               bounds=Bounds(lb, ub))
    if not res.success:
        return None
    x = np.round(res.x).astype(bool)
    picked_d = [d for d, on in zip(drivers, x[:nd]) if on]
    picked_t = [t for t, on in zip(teams, x[nd:nd + nt]) if on]
    captain = next(d for d, on in zip(drivers, x[nd + nt:]) if on)
    cost = sum(price_d[d] for d in picked_d) + sum(price_t[t] for t in picked_t)
    return {"drivers": picked_d, "teams": picked_t, "captain": captain, "expected": float(-res.fun), "cost": cost}


def team_score(team, pts_d, pts_t):
    return float(sum(pts_d.get(d, 0) for d in team["drivers"]) + pts_d.get(team["captain"], 0)
                 + sum(pts_t.get(t, 0) for t in team["teams"]))


def past_race(season, rnd, budget=BUDGET, data=None, backtest=None):
    """Everything for a race that's been run: prices, expected points (out of sample), the optimiser's team,
    what it scored, and the best team in hindsight."""
    df = results() if data is None else data
    bt = pd.read_csv(BACKTEST) if backtest is None else backtest
    race = df[(df["season"] == season) & (df["round"] == rnd)].reset_index(drop=True)
    rb = bt[(bt["season"] == season) & (bt["round"] == rnd)].set_index("driver").reindex(race["driver"]).reset_index()
    if race.empty or rb["win_chance"].isna().all():
        return None
    price_d, price_t, _, _ = prices(season, rnd, df, (race["driver"].tolist(), race["constructor"].unique().tolist()))
    exp_d, exp_t = expected_points(race, backtest_strength(rb), seed=season * 100 + rnd)
    real_d, real_t = actual_points(race)
    pick = optimise(exp_d, exp_t, price_d, price_t, budget)
    hindsight = optimise(real_d.astype(float), real_t.astype(float), price_d, price_t, budget)
    return {"race": race, "price_d": price_d, "price_t": price_t, "exp_d": exp_d, "exp_t": exp_t,
            "real_d": real_d, "real_t": real_t, "pick": pick, "hindsight": hindsight,
            "scored": team_score(pick, real_d, real_t) if pick else None,
            "best": team_score(hindsight, real_d, real_t) if hindsight else None}


def upcoming_race(table, season, rnd, luck, budget=BUDGET):
    """A race not yet run, from the live model's table (predictor.predict_upcoming): strength / luck is the
    Plackett-Luce strength the predictor itself simulates with."""
    race = table.reset_index(drop=True)
    price_d, price_t, _, _ = prices(season, rnd, None, (race["driver"].tolist(), race["constructor"].unique().tolist()))
    exp_d, exp_t = expected_points(race, race["strength"].to_numpy() / luck, seed=season * 100 + rnd)
    return {"race": race, "price_d": price_d, "price_t": price_t, "exp_d": exp_d, "exp_t": exp_t,
            "pick": optimise(exp_d, exp_t, price_d, price_t, budget)}


def season_backtest(season, budget=BUDGET, samples=200):
    """Race by race: the optimiser's team, the best in hindsight, and the average random team that fits."""
    df, bt = results(), pd.read_csv(BACKTEST)
    rows = []
    rng = np.random.default_rng(season)
    for rnd in sorted(df.loc[df["season"] == season, "round"].unique()):
        r = past_race(season, int(rnd), budget, df, bt)
        if not r or not r["pick"]:
            continue
        drivers, teams = list(r["price_d"]), list(r["price_t"])
        drivers = [d for d in drivers if d in r["real_d"].index]
        teams = [t for t in teams if t in r["real_t"].index]
        rand = []
        for _ in range(samples * 5):
            if len(rand) >= samples:
                break
            ds = list(rng.choice(drivers, N_DRIVERS, replace=False))
            ts = list(rng.choice(teams, N_TEAMS, replace=False))
            if sum(r["price_d"][d] for d in ds) + sum(r["price_t"][t] for t in ts) <= budget:
                cap = max(ds, key=lambda d: r["price_d"][d])
                rand.append(team_score({"drivers": ds, "teams": ts, "captain": cap}, r["real_d"], r["real_t"]))
        rows.append({"round": int(rnd), "race_name": r["race"]["race_name"].iloc[0], "model": r["scored"],
                     "best": r["best"], "random": float(np.mean(rand)) if rand else np.nan,
                     "expected": r["pick"]["expected"]})
    return pd.DataFrame(rows)


def name(key):
    return clean_name(key) if "_" in key or key.islower() else key


if __name__ == "__main__":
    s = int(sys.argv[1]) if len(sys.argv) > 1 else 2025
    bt = season_backtest(s)
    print(bt.round(1).to_string())
    print(bt[["model", "best", "random"]].sum().round(0).to_dict())
