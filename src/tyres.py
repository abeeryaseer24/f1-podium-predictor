"""Tyre Lab engine: how much each tyre compound slows down as it wears, for one race.

Fitted on clean racing laps only:
  lap time = driver's base pace + fuel effect x lap number + compound offset + wear rate x tyre age
The lap number stands in for fuel (cars get lighter every lap), while tyre age resets at every
pit stop. That is how the model can tell fuel and tyre wear apart.

Test from the terminal:
  python src/tyres.py 2026 19
"""
import sys

import numpy as np
import pandas as pd

from predictor import RACES_DIR

COMPOUNDS = ["SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"]
MIN_LAPS = 15          # a compound needs at least this many clean laps to get a curve
SLOW_LIMIT = 1.07      # laps more than 7% slower than normal are left out


def clean_laps(laps):
    """Racing laps only: no lap 1, no pit in/out laps, no safety-car or very slow laps."""
    laps = laps.sort_values(["driver_number", "lap_number"]).copy()
    out_lap = laps["is_pit_out_lap"].fillna(False).astype(bool)
    in_lap = (laps.groupby("driver_number")["is_pit_out_lap"].shift(-1)
              .fillna(False).astype(bool))
    keep = (laps["lap_duration"].notna() & laps["compound"].isin(COMPOUNDS)
            & laps["tyre_age"].notna() & (laps["lap_number"] > 1) & ~out_lap & ~in_lap)
    clean = laps[keep].copy()
    normal = clean.groupby("driver_number")["lap_duration"].transform("median")
    clean = clean[clean["lap_duration"] <= normal * SLOW_LIMIT]
    return clean[clean["lap_duration"] <= clean["lap_duration"].median() * SLOW_LIMIT]


def design(data, drivers, compounds):
    """The model's inputs as a table of numbers: one column per thing it estimates."""
    cols = [(data["driver_number"] == d).astype(float).to_numpy() for d in drivers]
    cols.append(data["lap_number"].to_numpy(dtype=float))                         # fuel
    for c in compounds[1:]:                                                        # offsets
        cols.append((data["compound"] == c).astype(float).to_numpy())
    for c in compounds:                                                            # wear
        cols.append(((data["compound"] == c) * data["tyre_age"]).to_numpy(dtype=float))
    return np.column_stack(cols)


def fit(data, drivers, compounds):
    X, y = design(data, drivers, compounds), data["lap_duration"].to_numpy(dtype=float)
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    return coef


def pit_loss(laps):
    """Typical time lost by a pit stop: (in-lap + out-lap) minus two normal laps."""
    losses = []
    for _, g in laps.sort_values(["driver_number", "lap_number"]).groupby("driver_number"):
        g = g.reset_index(drop=True)
        normal = g["lap_duration"].median()
        out_laps = g.index[g["is_pit_out_lap"].fillna(False).astype(bool) & (g["lap_number"] > 1)]
        for k in out_laps:
            if k == 0:
                continue
            pair = g.loc[k - 1, "lap_duration"] + g.loc[k, "lap_duration"]
            if pd.notna(pair):
                losses.append(pair - 2 * normal)
    losses = [x for x in losses if 10 <= x <= 45]                 # ignore odd ones (SC stops, penalties)
    return float(np.median(losses)) if losses else None


def analyse(folder):
    laps = pd.read_parquet(RACES_DIR / folder / "laps.parquet")
    clean = clean_laps(laps)
    counts = clean["compound"].value_counts()
    compounds = [c for c in COMPOUNDS if counts.get(c, 0) >= MIN_LAPS]
    result = {"compounds": [], "fuel": None, "error": None, "ref": None,
              "points": pd.DataFrame(), "pit_loss": pit_loss(laps), "clean_laps": len(clean)}
    if not compounds:
        return result

    data = clean[clean["compound"].isin(compounds)].reset_index(drop=True)
    drivers = sorted(data["driver_number"].unique())

    # Honesty check: fit on 80% of the laps, measure the error on the other 20%
    test = np.random.default_rng(0).random(len(data)) < 0.2
    coef = fit(data[~test], drivers, compounds)
    predicted = design(data[test], drivers, compounds) @ coef
    error = float(np.mean(np.abs(predicted - data.loc[test, "lap_duration"].to_numpy())))

    # Final model on all clean laps
    coef = fit(data, drivers, compounds)
    nd, nc = len(drivers), len(compounds)
    base = dict(zip(drivers, coef[:nd]))
    fuel = float(coef[nd])
    offsets = dict(zip(compounds, [0.0] + list(coef[nd + 1: nd + nc])))
    wear = dict(zip(compounds, coef[nd + nc:]))

    for c in compounds:
        laps_c = data[data["compound"] == c]
        result["compounds"].append({
            "name": c, "offset": float(offsets[c]), "wear": float(wear[c]),
            "laps": int(len(laps_c)), "max_age": int(laps_c["tyre_age"].max()),
        })

    # Each clean lap with driver pace and fuel taken out: what's left is tyre + noise
    data["adjusted"] = (data["lap_duration"] - data["driver_number"].map(base)
                        - fuel * data["lap_number"])
    result.update(fuel=fuel, error=error, ref=compounds[0],
                  points=data[["compound", "tyre_age", "adjusted"]])
    return result


if __name__ == "__main__":
    season, rnd = int(sys.argv[1]), int(sys.argv[2])
    r = analyse(f"{season}_{rnd:02d}")
    print(f"Clean laps used: {r['clean_laps']}")
    if r["compounds"]:
        print(f"Fuel effect: {r['fuel']:+.3f} s per lap   Model error: ±{r['error']:.2f} s per lap")
        for c in r["compounds"]:
            print(f"  {c['name']:<12} fresh: {c['offset']:+.2f} s vs {r['ref'].title()}   "
                  f"wear: {c['wear']:+.3f} s/lap   ({c['laps']} laps, longest stint {c['max_age']})")
    print(f"Pit stop loss: {r['pit_loss']:.1f} s" if r["pit_loss"] else "Pit stop loss: not enough stops")