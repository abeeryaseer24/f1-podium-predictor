"""Pit Wall strategist: for every driver, at the end of every lap, compare four plans
(pit now, pit in 3 laps, pit in 6 laps, stay out) by simulating the rest of the race.

THE NO-FUTURE RULE: calls for lap L are made by calls_for_lap(), which only ever receives
laps 1 to L. checks.py recomputes stored calls from past laps only, to prove it.

Simple, stated assumptions:
- at most one more pit stop is considered
- dry races must use two different dry compounds; laps on wet tyres get no call
- a safety car starts on 2.5% of laps and lasts 4 laps; stopping under it costs 55% of a stop
- rivals follow the plan that's best for them on average

Usage:
  python src/strategy.py 2026 19               one race (prints how it compares with reality)
  python src/strategy.py --missing --limit 10  races that don't have a strategy file yet
"""
import argparse

import numpy as np
import pandas as pd

from predictor import RACES_DIR
from tyres import MIN_LAPS, clean_laps, fit, pit_loss

DRY = ["SOFT", "MEDIUM", "HARD"]
PRIOR_OFFSET = {"SOFT": -0.5, "MEDIUM": 0.0, "HARD": 0.4}     # typical, used until the race shows more
PRIOR_WEAR = {"SOFT": 0.09, "MEDIUM": 0.05, "HARD": 0.03}
PRIOR_FUEL = -0.06
PRIOR_PIT_LOSS = 22.0
PRIOR_WEIGHT = 40          # how many laps of evidence the typical values are worth
LAP_NOISE = 0.6            # seconds of random variation per lap
SC_CHANCE, SC_LAPS, SC_PIT_FACTOR = 0.025, 4, 0.55
RUNS = 300
OPTIONS = [("Pit now", 0), ("Pit in 3 laps", 3), ("Pit in 6 laps", 6), ("Stay out", None)]


# ---------- what the race has shown so far ----------

def tyre_model(laps):
    """Fuel, compound offsets and wear, from the laps so far, blended with typical values."""
    model = {"fuel": PRIOR_FUEL, "offset": dict(PRIOR_OFFSET), "wear": dict(PRIOR_WEAR),
             "pit_loss": pit_loss(laps) or PRIOR_PIT_LOSS}
    clean = clean_laps(laps)
    counts = clean["compound"].value_counts()
    comps = [c for c in DRY if counts.get(c, 0) >= MIN_LAPS]
    if not comps or len(clean) < 60:
        return model

    data = clean[clean["compound"].isin(comps)]
    drivers = sorted(data["driver_number"].unique())
    coef = fit(data, drivers, comps)
    nd, nc = len(drivers), len(comps)
    offsets = [0.0] + list(coef[nd + 1: nd + nc])
    wear = coef[nd + nc:]

    w = len(data) / (len(data) + PRIOR_WEIGHT)
    model["fuel"] = w * coef[nd] + (1 - w) * PRIOR_FUEL
    shift = PRIOR_OFFSET[comps[0]]            # put the fitted offsets on the same scale as the priors
    for c, o, wr in zip(comps, offsets, wear):
        wc = counts[c] / (counts[c] + PRIOR_WEIGHT)
        model["offset"][c] = wc * (o + shift) + (1 - wc) * PRIOR_OFFSET[c]
        model["wear"][c] = max(0.0, wc * wr + (1 - wc) * PRIOR_WEAR[c])
    return model


def base_pace(laps, model):
    """Each driver's pace with fuel and tyres taken out (median of their last 5 clean laps)."""
    clean = clean_laps(laps)
    clean = clean[clean["compound"].isin(DRY)]
    if clean.empty:
        return {}, laps["lap_duration"].median()
    adj = (clean["lap_duration"] - model["fuel"] * clean["lap_number"]
           - clean["compound"].map(model["offset"])
           - clean["compound"].map(model["wear"]) * clean["tyre_age"])
    clean = clean.assign(adj=adj)
    recent = clean.sort_values("lap_number").groupby("driver_number").tail(5)
    return recent.groupby("driver_number")["adj"].median().to_dict(), float(adj.median())


def current_states(laps, L):
    """Each car at the end of lap L: tyre, tyre age, when it finished the lap, compounds used."""
    states = {}
    for d, mine in laps.groupby("driver_number"):
        now = mine[mine["lap_number"] == L]
        if now.empty:
            continue
        r = now.iloc[0]
        just_pitted = pd.notna(r["is_pit_out_lap"]) and bool(r["is_pit_out_lap"])
        if (r["compound"] not in DRY or pd.isna(r["tyre_age"]) or pd.isna(r["lap_duration"])
                or pd.isna(r["t_start"]) or just_pitted):
            continue
        states[d] = {"compound": r["compound"], "age": float(r["tyre_age"]),
                     "end": float(r["t_start"] + r["lap_duration"]),
                     "used": set(mine["compound"].dropna()) & set(DRY)}
    return states


# ---------- simulating the rest of the race ----------

def lap_times(st, model, base, k, L, pit_after, new_comp):
    """Predicted times for laps k, with an optional stop at the end of lap pit_after."""
    off, wear, cur = model["offset"], model["wear"], st["compound"]
    if pit_after is None:
        return base + model["fuel"] * k + off[cur] + wear[cur] * (st["age"] + (k - L))
    before = k <= pit_after
    age = np.where(before, st["age"] + (k - L), k - pit_after)
    o = np.where(before, off[cur], off[new_comp])
    w = np.where(before, wear[cur], wear[new_comp])
    return base + model["fuel"] * k + o + w * age


def remaining(st, model, base, L, total, pit_after, new_comp):
    """Expected seconds from the end of lap L to the flag, for one plan."""
    k = np.arange(L + 1, total + 1)
    t = float(lap_times(st, model, base, k, L, pit_after, new_comp).sum())
    return t + (model["pit_loss"] if pit_after is not None else 0.0)


def plans_for(st, model, base, L, total):
    """The valid plans for one car: (label, pit_after, new_compound, expected time)."""
    done_rule = len(st["used"]) >= 2

    def best_tyre(p):
        allowed = [c for c in DRY if done_rule or c != st["compound"]]
        return min(allowed, key=lambda c: remaining(st, model, base, L, total, p, c))

    plans = []
    for label, wait in OPTIONS:
        if wait is None:
            if done_rule:
                plans.append(("Stay out", None, None))
            else:
                later = list(range(L + 7, total - 1))
                if later:
                    p = min(later, key=lambda p: remaining(st, model, base, L, total, p, best_tyre(p)))
                    plans.append((f"Stay out, pit lap {p}", p, best_tyre(p)))
        elif L + wait <= total - 2:
            p = L + wait
            plans.append((label, p, best_tyre(p)))
    return [(lab, p, c, remaining(st, model, base, L, total, p, c)) for lab, p, c in plans]


def calls_for_lap(laps, L, total):
    """Every driver's plans and call at the end of lap L.
    `laps` must contain laps 1..L only: that is the no-future rule."""
    if laps["lap_number"].max() > L:
        raise ValueError("calls_for_lap was given future laps")
    model = tyre_model(laps)
    base, fallback = base_pace(laps, model)
    states = current_states(laps, L)
    if len(states) < 2:
        return pd.DataFrame()

    R = total - L
    plans = {d: plans_for(st, model, base.get(d, fallback), L, total) for d, st in states.items()}
    best = {d: st["end"] + min(x[3] for x in plans[d]) for d, st in states.items() if plans[d]}
    order = sorted(states, key=lambda d: states[d]["end"])
    position_now = {d: i + 1 for i, d in enumerate(order)}

    rows = []
    for d, st in states.items():
        if not plans[d]:
            continue
        rivals = [r for r in best if r != d]
        rng = np.random.default_rng(int(d) * 1000 + L)            # same draws every time
        noise = rng.normal(0, LAP_NOISE, (RUNS, R)).sum(axis=1)
        safety_car = rng.random((RUNS, R)) < SC_CHANCE
        rival_times = (np.array([best[r] for r in rivals])
                       + rng.normal(0, LAP_NOISE * np.sqrt(R), (RUNS, len(rivals))))
        for label, p, comp, expected in plans[d]:
            own = st["end"] + expected + noise
            if p is not None and p > L:                           # cheaper stop under a safety car?
                j = p - L - 1
                covered = safety_car[:, max(0, j - SC_LAPS + 1): j + 1].any(axis=1)
                own = own - covered * model["pit_loss"] * (1 - SC_PIT_FACTOR)
            finish = 1 + (rival_times < own[:, None]).sum(axis=1)
            rows.append({"driver_number": int(d), "lap": L, "plan": label,
                         "pit_lap": p, "compound": comp,
                         "exp_position": round(float(finish.mean()), 3),
                         "best_position": int(np.percentile(finish, 10)),
                         "worst_position": int(np.percentile(finish, 90)),
                         "exp_time": round(expected, 3), "position_now": position_now[d]})

    df = pd.DataFrame(rows)
    df["call"] = False
    for _, g in df.groupby("driver_number"):
        df.loc[g.sort_values(["exp_position", "exp_time"]).index[0], "call"] = True

    calls = df[df["call"]].set_index("driver_number")["plan"]
    df["undercut_by"] = pd.NA
    for i, d in enumerate(order[:-1]):
        behind = order[i + 1]
        close = states[behind]["end"] - states[d]["end"] < 2.5
        if close and calls.get(behind) == "Pit now" and calls.get(d) != "Pit now":
            df.loc[df["driver_number"] == d, "undercut_by"] = int(behind)
    return df


# ---------- whole races ----------

def build_strategy(folder):
    laps = pd.read_parquet(RACES_DIR / folder / "laps.parquet")
    total = int(laps["lap_number"].max())
    frames = [calls_for_lap(laps[laps["lap_number"] <= L], L, total) for L in range(2, total - 1)]
    result = pd.concat([f for f in frames if not f.empty], ignore_index=True)
    result["undercut_by"] = result["undercut_by"].astype("Int64")
    result.to_parquet(RACES_DIR / folder / "strategy.parquet", index=False)
    return result


def real_stops(laps):
    """The lap each real pit stop was made on (the lap before an out-lap)."""
    laps = laps.sort_values(["driver_number", "lap_number"])
    next_is_out = laps.groupby("driver_number")["is_pit_out_lap"].shift(-1)
    stops = laps[next_is_out.fillna(False).astype(bool)]
    return stops[["driver_number", "lap_number"]].rename(columns={"lap_number": "lap"})


def summary(folder):
    """How the strategist's 'pit now' calls line up with the real stops."""
    laps = pd.read_parquet(RACES_DIR / folder / "laps.parquet")
    strat = pd.read_parquet(RACES_DIR / folder / "strategy.parquet")
    pit_now = strat[strat["call"] & (strat["plan"] == "Pit now")]
    stops = real_stops(laps)
    matched = sum(
        not pit_now[(pit_now["driver_number"] == s.driver_number)
                    & pit_now["lap"].between(s.lap - 2, s.lap)].empty
        for s in stops.itertuples())
    return {"stops": len(stops), "matched": int(matched), "pit_now_calls": len(pit_now)}


def main():
    parser = argparse.ArgumentParser(description="Run the Pit Wall strategist")
    parser.add_argument("season", type=int, nargs="?")
    parser.add_argument("round", type=int, nargs="?")
    parser.add_argument("--missing", action="store_true")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    if args.missing:
        todo = [p.name for p in sorted(RACES_DIR.glob("*_*"), reverse=True)
                if (p / "info.json").exists() and not (p / "strategy.parquet").exists()]
        print(f"{len(todo)} races need a strategy; doing up to {args.limit}.")
        folders = todo[:args.limit]
    elif args.season and args.round:
        folders = [f"{args.season}_{args.round:02d}"]
    else:
        parser.error("give a season and a round, or use --missing")

    for folder in folders:
        try:
            result = build_strategy(folder)
            s = summary(folder)
            print(f"  {folder}: {result['lap'].nunique()} laps of calls, {s['pit_now_calls']} 'pit now' calls; "
                  f"real stops: {s['stops']}, called within 2 laps before: {s['matched']}")
        except Exception as error:
            print(f"  Skipped {folder}: {error}")


if __name__ == "__main__":
    main()