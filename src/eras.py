"""Driver vs car: separating how good each driver was from how good their car was, 1950 to today.

THE MODEL. In every race, every pair of classified finishers is a comparison: who beat whom. Each
driver's performance in a race is
    driver skill (for the whole career) + a small season-by-season change + car strength (team, season)
and the chance that driver i beats driver j is the logistic of the difference (a Bradley-Terry model,
the pairwise form of the Plackett-Luce model the predictor uses). Fitted by penalised maximum likelihood
on about 160,000 comparisons from every race since 1950.

WHY IT CAN COMPARE ERAS. Team-mates share a car, so their results separate driver from car. Drivers
change teams, and careers overlap across decades, which chains the whole history onto one scale.

WHAT IT LEAVES OUT. Retirements are left out (most were mechanical in the early decades, which would
punish drivers for their cars), so crashes aren't punished either. The Indianapolis 500 (part of the
championship 1950-60, with a separate field) is excluded. Early seasons have few races and drivers
switched cars within a race, so their ratings are less certain: the uncertainty is shown.

Ratings are on the model's own scale: a gap of 1.0 means the better driver beats the other in the same
car about 73 % of the time.

Writes data/processed/era_ratings.json. The pipeline refreshes it after new results.

Usage:
  python src/eras.py
"""
import json

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.optimize import minimize
from scipy.sparse.linalg import splu

from archive import RESULTS_FILE

OUT = RESULTS_FILE.parent / "era_ratings.json"
L2_DRIVER, L2_SEASON, L2_CAR = 0.5, 4.0, 0.3     # how strongly each kind of parameter is pulled to zero
MIN_RACES = 15                                    # drivers with fewer classified finishes are left out of rankings


def finishers():
    df = pd.read_csv(RESULTS_FILE)
    df = df[~df["race_name"].str.contains("Indianapolis", na=False)]
    df["pos"] = pd.to_numeric(df["position_text"], errors="coerce")
    df = df.dropna(subset=["pos"])
    df["car"] = df["constructor"] + "_" + df["season"].astype(str)
    df["dseason"] = df["driver"] + "_" + df["season"].astype(str)
    return df


def pairs(df):
    """(winner row, loser row) index pairs for every pair of finishers in every race."""
    w, l = [], []
    for _, race in df.groupby(["season", "round"]):
        idx = race.sort_values("pos").index.to_numpy()
        for a in range(len(idx)):
            w.extend([idx[a]] * (len(idx) - a - 1))
            l.extend(idx[a + 1:])
    return np.array(w), np.array(l)


def fit():
    df = finishers().reset_index(drop=True)
    drivers = sorted(df["driver"].unique())
    dseasons = sorted(df["dseason"].unique())
    cars = sorted(df["car"].unique())
    nd, ns, nc = len(drivers), len(dseasons), len(cars)
    di = {d: k for k, d in enumerate(drivers)}
    si = {d: nd + k for k, d in enumerate(dseasons)}
    ci = {c: nd + ns + k for k, c in enumerate(cars)}
    p = nd + ns + nc
    # each result row -> three parameter columns
    cols = np.stack([df["driver"].map(di), df["dseason"].map(si), df["car"].map(ci)], axis=1)
    w, l = pairs(df)
    m = len(w)
    rows = np.repeat(np.arange(m), 3)
    X = sparse.csr_matrix((np.r_[np.ones(3 * m), -np.ones(3 * m)],
                           (np.r_[rows, rows], np.r_[cols[w].ravel(), cols[l].ravel()])), shape=(m, p))
    lam = np.r_[np.full(nd, L2_DRIVER), np.full(ns, L2_SEASON), np.full(nc, L2_CAR)]

    def f(beta):
        z = X @ beta
        loss = np.logaddexp(0, -z).sum() + 0.5 * (lam * beta * beta).sum()
        grad = -(X.T @ (1 / (1 + np.exp(z)))) + lam * beta
        return loss, grad

    res = minimize(f, np.zeros(p), jac=True, method="L-BFGS-B", options={"maxiter": 400})
    beta = res.x
    # Laplace approximation for driver uncertainty: (X'WX + Lambda)^-1, driver block diagonal
    z = X @ beta
    pr = 1 / (1 + np.exp(-z))
    H = (X.T @ sparse.diags(pr * (1 - pr)) @ X + sparse.diags(lam)).tocsc()
    lu = splu(H)
    se = np.zeros(nd)
    for k in range(nd):
        e = np.zeros(p)
        e[k] = 1
        se[k] = np.sqrt(max(lu.solve(e)[k], 0))

    stats = df.groupby("driver").agg(name=("driver_name", "last"), first=("season", "min"), last=("season", "max"),
                                     races=("pos", "size"), wins=("pos", lambda s: int((s == 1).sum())))
    teams = df.groupby("driver")["constructor_name"].agg(lambda s: s.value_counts().index[0])
    driver_rows = []
    for d in drivers:
        seasons = df[df["driver"] == d]["season"].unique()
        season_vals = {int(s): float(beta[di[d]] + beta[si[f"{d}_{s}"]]) for s in seasons}
        best = max(season_vals, key=season_vals.get)
        driver_rows.append({"driver": d, "name": stats.at[d, "name"], "skill": float(beta[di[d]]), "se": float(se[di[d]]),
                            "peak": season_vals[best], "peak_season": best, "seasons": season_vals,
                            "first": int(stats.at[d, "first"]), "last": int(stats.at[d, "last"]),
                            "races": int(stats.at[d, "races"]), "wins": int(stats.at[d, "wins"]), "team": teams.at[d]})
    car_names = df.drop_duplicates("car").set_index("car")["constructor_name"]
    car_rows = [{"car": c, "constructor": c.rsplit("_", 1)[0], "season": int(c.rsplit("_", 1)[1]),
                 "name": car_names.at[c], "strength": float(beta[ci[c]])} for c in cars]
    out = {"drivers": driver_rows, "cars": car_rows, "comparisons": int(m),
           "min_races": MIN_RACES, "converged": bool(res.success)}
    OUT.write_text(json.dumps(out))
    return out


def load():
    return json.loads(OUT.read_text()) if OUT.exists() else None


# ---------- driver swap ----------

def season_field(season):
    """Every race of a season: list of (driver, car) for the classified finishers, in finishing order."""
    df = finishers()
    df = df[df["season"] == season]
    return [list(zip(r.sort_values("pos")["driver"], r.sort_values("pos")["car"])) for _, r in df.groupby("round")]


def swap(ratings, season, seat_driver, new_driver, runs=2000, use_peak=True, seed=0):
    """Put new_driver in seat_driver's car for a whole season. Returns points and title odds for both."""
    from rules import SYSTEMS
    points_table = SYSTEMS["Today's (25-18-15-12-10-8-6-4-2-1)"]
    dr = {d["driver"]: d for d in ratings["drivers"]}
    car = {c["car"]: c["strength"] for c in ratings["cars"]}

    def skill(d, s):
        info = dr[d]
        if use_peak:
            return info["peak"]
        return info["seasons"].get(str(s), info["seasons"].get(s, info["skill"]))

    races = season_field(season)
    rng = np.random.default_rng(seed)
    results = {}
    for label, sitter in (("real", seat_driver), ("swap", new_driver)):
        totals = {}
        for race in races:
            names = [d for d, _ in race]
            if seat_driver not in names:
                continue
            strength = np.array([(skill(sitter, season) if d == seat_driver else skill(d, season)) + car.get(c, 0.0)
                                 for d, c in race])
            g = strength[None, :] + rng.gumbel(size=(runs, len(race)))
            order = np.argsort(-g, axis=1)
            pts = np.zeros((runs, len(race)))
            for p, v in enumerate(points_table):
                if p < len(race):
                    pts[np.arange(runs), order[:, p]] = v
            for k, d in enumerate(names):
                totals.setdefault(d, np.zeros(runs))
                totals[d] += pts[:, k]
        names = list(totals)
        mat = np.stack([totals[d] for d in names], axis=1)
        champ = np.array(names)[mat.argmax(axis=1)]
        results[label] = {"points": float(totals[seat_driver].mean()),
                          "title": float((champ == seat_driver).mean()),
                          "rank": float((mat > totals[seat_driver][:, None]).sum(axis=1).mean() + 1),
                          "races": sum(1 for r in races if seat_driver in [d for d, _ in r])}
    return results


if __name__ == "__main__":
    import time
    t = time.time()
    out = fit()
    print(f"Fitted on {out['comparisons']:,} comparisons in {time.time() - t:.0f}s (converged: {out['converged']})")
    top = sorted([d for d in out["drivers"] if d["races"] >= MIN_RACES], key=lambda d: -d["skill"])[:20]
    for k, d in enumerate(top, 1):
        print(f"{k:2d}. {d['name']:28s} {d['skill']:+.2f} ±{d['se']:.2f}  peak {d['peak']:+.2f} ({d['peak_season']})  {d['first']}-{d['last']}")
