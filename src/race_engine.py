"""Race engine: a whole Grand Prix simulated lap by lap, hundreds of times.

Every car, every lap:
  lap time = driver's base pace + fuel effect x lap + tyre (compound offset + wear x age + cliff)
             + random lap-to-lap noise (+ a random "form" for this run)
  pit stop  adds the circuit's pit loss on the in-lap (55 % of it under a safety car)

Everything is measured from the real race's own laps (OpenF1): each driver's base pace with fuel and
tyres taken out (the same fit as the Tyre Lab), the fuel effect, each compound's speed and wear, and
the pit loss. The race starts from the real grid, and by default each driver uses their real strategy.

TRAFFIC AND OVERTAKING. Cars are processed in running order. A faster car that catches the one ahead
must get past: it succeeds with a probability that rises with its pace advantage and falls with how
hard overtaking is at this circuit. Difficulty comes from data: how much a grid place costs at the
circuit (penalties.py, from every race since 2016). If it fails, it stays 0.3 s behind and loses time.

SAFETY CARS. Each lap has a chance of a safety car, from how often safety cars came out at this circuit
in the prepared races (shrunk towards the average, since each circuit has few races). Under a safety car
the field bunches up and laps are slow, and pit stops are cheaper. A safety car can be forced on a lap.

RETIREMENTS. A small chance per car per lap, from the overall retirement rate.

Run many times (vectorised across runs), it gives each driver's chance of every finishing position.
It's a teaching model: no tyre temperatures, no undercut subtleties beyond pace, no team orders, no
weather (the Race Simulator says so).

Test from the terminal:
  python src/race_engine.py 2025 12
"""
import json
import sys

import numpy as np
import pandas as pd

import penalties
import race_story as R
import tyres as TY
from predictor import RACES_DIR, RESULTS_CSV
from strategy import CLIFF_RATE, CLIFF_START, SC_FACTOR

NOISE = 0.35            # s, lap-to-lap randomness
FORM = 0.12             # s, a driver's random pace offset for a whole run
MIN_GAP = 0.3           # s, how close a car can follow when it can't pass
SC_LAPS = 4             # laps a safety car stays out
SC_SLOW = 1.40          # safety-car laps are this much slower
SC_GAP = 0.8            # s between cars when the field is bunched
DNF_PER_LAP = 0.0012    # chance per car per lap (about one or two retirements a race)
TYRE_LIFE = {"SOFT": 22, "MEDIUM": 32, "HARD": 42, "INTERMEDIATE": 30, "WET": 30}


def safety_car_rates():
    """circuit location -> safety cars per race, from race control in every prepared race."""
    rows = []
    for path in sorted(RACES_DIR.glob("*_*")):
        if not (path / "race_control.parquet").exists():
            continue
        info = json.loads((path / "info.json").read_text())
        rc = pd.read_parquet(path / "race_control.parquet")
        msgs = rc["message"].fillna("").str.upper()
        n = int(msgs.str.contains(r"^SAFETY CAR DEPLOYED|\bSAFETY CAR DEPLOYED", regex=True).sum())
        rows.append((info.get("location", ""), n))
    df = pd.DataFrame(rows, columns=["location", "sc"])
    overall = float(df["sc"].mean()) if len(df) else 0.6
    out = {}
    for loc, d in df.groupby("location"):
        k = 3.0                                                # shrink towards the overall average
        out[loc] = (d["sc"].sum() + k * overall) / (len(d) + k)
    return out, overall


def real_strategy(laps, num):
    """[(compound, last lap of the stint)] for one driver, from their real laps."""
    d = laps[laps["driver_number"] == num].sort_values("lap_number")
    if d.empty:
        return []
    stints, current, start = [], None, None
    outs = set(d.loc[d["is_pit_out_lap"].fillna(False).astype(bool), "lap_number"].astype(int))
    for _, r in d.iterrows():
        lap = int(r["lap_number"])
        comp = r["compound"] if isinstance(r["compound"], str) else (current or "MEDIUM")
        if current is None:
            current, start = comp, lap
        elif lap in outs:
            stints.append((current, lap - 1))
            current, start = comp, lap
    stints.append((current, int(d["lap_number"].max())))
    return stints


def build(folder):
    """Everything the engine needs for one race, measured from its real laps."""
    laps, pits, control, info = R.load(folder)
    fit = TY.analyse(folder)
    comps = {c["name"]: c for c in fit["compounds"]}
    fuel = fit["fuel"] or -0.06
    clean = TY.clean_laps(laps)
    ref_comp = fit["ref"]
    base = {}
    for num, d in clean.groupby("driver_number"):
        adj = d["lap_duration"] - fuel * d["lap_number"]
        adj -= d["compound"].map(lambda c: comps.get(c, {}).get("offset", 0.0))
        adj -= d["tyre_age"] * d["compound"].map(lambda c: comps.get(c, {}).get("wear", 0.05))
        base[int(num)] = float(adj.median())
    results = pd.read_csv(RESULTS_CSV)
    grid = R.grid_for(info, results)
    who = R.drivers(info)
    drivers = [n for n in sorted(grid, key=grid.get) if n in base and n in who]
    order = R.finishing_order(laps)
    real_pos = {n: order.index(n) + 1 for n in drivers if n in order}
    sc_rates, sc_overall = safety_car_rates()
    place = penalties.place_costs()
    circuit = results[(results["season"] == info["season"]) & (results["round"] == info["round"])]["circuit"]
    difficulty = place.get(circuit.iloc[0] if len(circuit) else "", penalties.DEFAULT_SLOPE)
    return {
        "folder": folder, "info": info, "drivers": drivers, "who": who, "grid": grid, "base": base,
        "fuel": fuel, "compounds": comps, "ref": ref_comp, "pit_loss": fit["pit_loss"] or 22.0,
        "laps": int(info.get("laps") or laps["lap_number"].max()),
        "strategies": {n: real_strategy(laps, n) for n in drivers}, "real_pos": real_pos,
        "sc_rate": sc_rates.get(info.get("location", ""), sc_overall), "difficulty": difficulty,
    }


def tyre_cost(comps, comp, age):
    c = comps.get(comp) or {"offset": 0.5, "wear": 0.06}
    life = TYRE_LIFE.get(comp, 30)
    over = np.maximum(0, age - CLIFF_START * life)
    return c["offset"] + max(c["wear"], 0.0) * age + CLIFF_RATE * over * (over + 1) / 2


def simulate(race, runs=300, strategies=None, force_sc_lap=None, sc_enabled=True, seed=0, pace_offsets=None):
    """Run the race `runs` times. Returns positions (runs x drivers, 0 = retired/unclassified) and laps led."""
    rng = np.random.default_rng(seed)
    drv = race["drivers"]
    n, L = len(drv), race["laps"]
    strategies = {**race["strategies"], **(strategies or {})}
    base = np.array([race["base"][d] + (pace_offsets or {}).get(d, 0.0) for d in drv])
    form = rng.normal(0, FORM, (runs, n))
    # Per-lap tyre and pit plan for every driver (same in every run)
    tyre = np.zeros((L + 1, n))
    pit_lap = np.zeros((L + 1, n), dtype=bool)
    for j, d in enumerate(drv):
        stints = strategies.get(d) or [(race["ref"] or "MEDIUM", L)]
        lap0 = 1
        for k, (comp, end) in enumerate(stints):
            end = min(end, L) if k < len(stints) - 1 else L
            for lap in range(lap0, end + 1):
                tyre[lap, j] = tyre_cost(race["compounds"], comp, lap - lap0)
            if k < len(stints) - 1:
                pit_lap[end, j] = True
            lap0 = end + 1
    # Start: grid order, 0.25 s apart, lap 1 slower and messier
    cum = np.tile(np.arange(n) * 0.25, (runs, 1)).astype(float)
    alive = np.ones((runs, n), dtype=bool)
    sc_left = np.zeros(runs, dtype=int)
    hazard = race["sc_rate"] / max(L, 1) if sc_enabled else 0.0
    diff = race["difficulty"]
    threshold = 0.25 + 2.0 * (diff - 0.4)          # pace advantage (s/lap) for a 50 % pass chance
    order = np.tile(np.arange(n), (runs, 1))       # running order (indices into drivers)
    for lap in range(1, L + 1):
        # safety cars
        new_sc = (rng.random(runs) < hazard) & (sc_left == 0) & (lap > 1) & (lap < L - 2)
        if force_sc_lap is not None and lap == force_sc_lap:
            new_sc |= sc_left == 0
        sc_left[new_sc] = SC_LAPS
        under_sc = sc_left > 0
        # intended lap times
        t = base[None, :] + form + race["fuel"] * lap + tyre[lap][None, :] + rng.normal(0, NOISE, (runs, n))
        if lap == 1:
            t += 2.0 + rng.normal(0, 0.8, (runs, n))
        stop = pit_lap[lap][None, :] * np.where(under_sc, SC_FACTOR["SC"], 1.0)[:, None] * race["pit_loss"]
        t_sc = np.median(t, axis=1, keepdims=True) * SC_SLOW
        t = np.where(under_sc[:, None], t_sc, t) + stop
        # retirements
        alive &= rng.random((runs, n)) > DNF_PER_LAP
        want = cum + t
        # traffic, in running order
        rows = np.arange(runs)
        prev_cum = np.full(runs, -np.inf)
        for pos in range(n):
            j = order[:, pos]
            w = want[rows, j]
            ok = alive[rows, j]
            if pos > 0:
                lead_t = t[rows, order[:, pos - 1]]
                adv = lead_t - t[rows, j]
                p_pass = 1 / (1 + np.exp(-(adv - threshold) / 0.25))
                blocked = ok & (w < prev_cum + MIN_GAP) & ~under_sc & ~pit_lap[lap][j]
                passed = rng.random(runs) < p_pass
                hold = blocked & ~passed
                w = np.where(hold, prev_cum + MIN_GAP, w)
                if lap > 1:                                 # under a safety car nobody passes and the field bunches
                    w = np.where(under_sc & ok, np.maximum(w, prev_cum + SC_GAP), w)
            want[rows, j] = w
            prev_cum = np.where(ok, np.maximum(prev_cum, w), prev_cum)
        cum = want
        sc_left = np.maximum(sc_left - 1, 0)
        key = np.where(alive, cum, np.inf)
        order = np.argsort(key, axis=1)
    final = np.argsort(np.where(alive, cum, np.inf), axis=1)
    positions = np.zeros((runs, n), dtype=int)
    for r in range(runs):
        for p, j in enumerate(final[r]):
            positions[r, j] = p + 1 if alive[r, j] else 0
    return positions


def summary(race, positions):
    """One row per driver: average finish, win %, podium %, points-finish %, retirement %."""
    drv = race["drivers"]
    rows = []
    for j, d in enumerate(drv):
        pos = positions[:, j]
        fin = pos[pos > 0]
        rows.append({"driver_number": d, "code": race["who"][d].get("code", str(d)),
                     "name": race["who"][d].get("name", ""), "team": race["who"][d].get("team", ""),
                     "colour": race["who"][d].get("colour") or "#8a8a96", "grid": race["grid"].get(d),
                     "expected": float(fin.mean()) if len(fin) else np.nan,
                     "win": float((pos == 1).mean()), "podium": float(((pos >= 1) & (pos <= 3)).mean()),
                     "points": float(((pos >= 1) & (pos <= 10)).mean()), "dnf": float((pos == 0).mean()),
                     "real": race["real_pos"].get(d)})
    return pd.DataFrame(rows).sort_values("expected").reset_index(drop=True)


def agreement(table):
    """Spearman correlation between expected finish and the real finish (finishers only)."""
    t = table.dropna(subset=["real", "expected"])
    return float(t["expected"].rank().corr(t["real"].rank())) if len(t) > 3 else float("nan")


if __name__ == "__main__":
    import time
    folder = f"{int(sys.argv[1])}_{int(sys.argv[2]):02d}" if len(sys.argv) == 3 else "2025_12"
    t0 = time.time()
    race = build(folder)
    t1 = time.time()
    pos = simulate(race, runs=300)
    t2 = time.time()
    table = summary(race, pos)
    print(f"{race['info']['race_name']} {race['info']['season']}: build {t1 - t0:.1f}s, 300 runs {t2 - t1:.1f}s, "
          f"SC rate {race['sc_rate']:.2f}/race, overtaking difficulty {race['difficulty']:.2f}, pit loss {race['pit_loss']:.1f}s")
    print(f"Agreement with the real result (Spearman): {agreement(table):.2f}")
    print(table[["code", "grid", "expected", "win", "podium", "dnf", "real"]].head(10).round(2).to_string(index=False))
