"""Who's driving? Telling teammates apart from one lap of telemetry.

THE DATA: for every prepared race since 2023, OpenF1's car data (speed, throttle, brake, gear, rpm,
about four samples a second) for each driver's clean racing laps. Each lap is cut out by its start
time and duration, its distance is found by integrating the speed, and it is put on a common grid of
GRID points from the line round to the line.

THE CAR CANCELS OUT: the two drivers of a team share the car, the circuit, the weather and the
tyres on offer. So every habit below is measured against the team's own average for that race
(the plain average of all the team's laps that race, so it needs no labels). What is left is how one driver uses the same
car differently from the other: earlier or later braking, a sharper or softer throttle, more or less
coasting, shorter or longer shifts.

THE MODEL: a multinomial logistic regression over every driver, trained on those team-centred
habits. To answer "which of these two drove this lap?" its probabilities are cut down to the two
teammates and renormalised. It is tested on whole races it never saw (grouped cross-validation by
race), so it can't memorise a weekend.

Build or extend the data from the terminal (resumable, one file per race):
  python src/driving_style.py --missing --limit 10
Then train and score:
  python src/driving_style.py --train
The pipeline does both for new races, retraining only when one was added:
  python src/driving_style.py --missing --limit 2 --train
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RACES_DIR = ROOT / "data" / "races"
STYLE_DIR = ROOT / "data" / "processed" / "style"
MODEL_JSON = ROOT / "data" / "processed" / "style_model.json"
GAME_LAPS = ROOT / "data" / "processed" / "style_game.parquet"

GRID = 300                 # points round the lap
LAPS_PER_DRIVER = 12       # clean laps kept per driver per race
GAME_PER_DRIVER = 2        # of those, laps kept at full detail for the game

FEATURES = {
    "full_throttle": "Share of the lap at full throttle",
    "part_throttle": "Share of the lap on part throttle",
    "coasting": "Share of the lap off both pedals",
    "braking": "Share of the lap on the brake",
    "overlap": "Share of the lap on throttle and brake together",
    "brake_point": "How late the braking starts (m after the team's average)",
    "brake_release": "How late the brake comes off (m after the team's average)",
    "throttle_pickup": "How early the throttle goes back down (m before the team's average)",
    "throttle_rate": "How fast the throttle is opened (% per 10 m)",
    "lift_rate": "How sharply the throttle is closed (% per 10 m)",
    "lifts_per_km": "Lifts off full throttle per km",
    "min_speed": "Average minimum corner speed (km/h)",
    "mean_speed": "Average speed (km/h)",
    "shift_rpm": "Average rpm at an upshift",
    "mean_gear": "Average gear",
    "throttle_jitter": "Throttle wobble (how much it moves when meant to be steady)",
}

# How each habit reads in words, (more of it, less of it), and how to print a team-centred value.
WORDS = {
    "full_throttle": ("more time flat out", "less time flat out"),
    "part_throttle": ("more part throttle", "less part throttle"),
    "coasting": ("coasts more", "coasts less"),
    "braking": ("longer on the brakes", "shorter on the brakes"),
    "overlap": ("overlaps the pedals more", "overlaps the pedals less"),
    "brake_point": ("brakes later", "brakes earlier"),
    "brake_release": ("holds the brake longer", "lets the brake off sooner"),
    "throttle_pickup": ("back on the power earlier", "back on the power later"),
    "throttle_rate": ("opens the throttle faster", "opens the throttle more gently"),
    "lift_rate": ("lifts more sharply", "lifts more gently"),
    "lifts_per_km": ("lifts more often", "lifts less often"),
    "min_speed": ("carries more corner speed", "carries less corner speed"),
    "mean_speed": ("faster on average", "slower on average"),
    "shift_rpm": ("shifts up later", "shifts up earlier"),
    "mean_gear": ("runs higher gears", "runs lower gears"),
    "throttle_jitter": ("busier on the throttle", "smoother on the throttle"),
}


def show(feature, value):
    """A team-centred value in plain units, with its sign."""
    if feature in ("full_throttle", "part_throttle", "coasting", "braking", "overlap"):
        return f"{value * 100:+.1f} pts"
    if feature in ("brake_point", "brake_release", "throttle_pickup"):
        return f"{value:+.1f} m"
    if feature in ("min_speed", "mean_speed"):
        return f"{value:+.1f} km/h"
    if feature == "shift_rpm":
        return f"{value:+.0f} rpm"
    if feature == "lifts_per_km":
        return f"{value:+.2f}"
    return f"{value:+.2f}"


def lap_clock(seconds):
    """83.456 -> '1:23.456'"""
    minutes, secs = divmod(float(seconds), 60)
    return f"{int(minutes)}:{secs:06.3f}"


# ---------- one lap ----------

def lap_grid(car, t0, duration):
    """One lap of car data on GRID points evenly spaced by distance.
    car: one driver's car data with t (s from session start). Returns a dict of arrays, or None."""
    part = car[(car["t"] >= t0 - 0.5) & (car["t"] <= t0 + duration + 0.5)]
    if len(part) < duration * 2:                 # sparse data: skip
        return None
    t = part["t"].to_numpy() - t0
    speed = part["speed"].to_numpy(float)
    dist = np.concatenate([[0], np.cumsum(np.diff(t) * (speed[1:] + speed[:-1]) / 2 / 3.6)])
    d0, d1 = np.interp([0, duration], t, dist)
    if d1 - d0 < 1000:
        return None
    s = np.linspace(d0, d1, GRID)
    out = {"length": d1 - d0}
    for col in ("speed", "throttle", "rpm", "n_gear"):
        out[col] = np.interp(s, dist, part[col].to_numpy(float))
    out["brake"] = np.interp(s, dist, (part["brake"].to_numpy(float) > 0).astype(float))
    return out


def zones(on):
    """Start and end indexes of each run of True in a boolean array."""
    on = np.r_[False, on, False].astype(int)
    edges = np.diff(on)
    return np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)


def habits(g):
    """The raw (not yet team-centred) habits of one lap on the grid."""
    thr, brk, spd = g["throttle"], g["brake"] > 0.5, g["speed"]
    step = g["length"] / (GRID - 1)
    full, braking = thr >= 98, brk
    out = {
        "full_throttle": full.mean(), "part_throttle": ((thr > 10) & (thr < 98) & ~brk).mean(),
        "coasting": ((thr <= 10) & ~brk).mean(), "braking": brk.mean(),
        "overlap": ((thr > 10) & brk).mean(),
        "mean_speed": spd.mean(), "mean_gear": g["n_gear"].mean(),
    }
    d = np.diff(thr) / step * 10
    out["throttle_rate"] = d[d > 2].mean() if (d > 2).any() else 0.0
    out["lift_rate"] = -d[d < -2].mean() if (d < -2).any() else 0.0
    s0, s1 = zones(full)
    out["lifts_per_km"] = max(len(s0) - 1, 0) / (g["length"] / 1000)
    steady = (thr > 15) & (thr < 95)
    out["throttle_jitter"] = np.abs(np.diff(thr, 2))[steady[1:-1]].mean() if steady[1:-1].any() else 0.0
    # corner minimum speeds: lowest point of each braking-to-full-throttle stretch
    b0, b1 = zones(brk)
    mins = [spd[a:min(b + 15, GRID)].min() for a, b in zip(b0, b1)]
    out["min_speed"] = float(np.mean(mins)) if mins else spd.min()
    gear, rpm = g["n_gear"], g["rpm"]
    up = np.flatnonzero(np.diff(np.round(gear)) >= 1)
    out["shift_rpm"] = rpm[up].mean() if len(up) else rpm.mean()
    return out


def zone_points(g):
    """Where each braking zone starts and ends, and where full throttle returns, in metres round the lap."""
    step = g["length"] / (GRID - 1)
    b0, b1 = zones(g["brake"] > 0.5)
    full = g["throttle"] >= 98
    pickups = []
    for b in b1:
        later = np.flatnonzero(full[b:])
        pickups.append((b + later[0]) * step if len(later) else np.nan)
    return b0 * step, b1 * step, np.array(pickups)


def match_offsets(points, reference, tol=60):
    """Average distance (m) between each point and the nearest reference point within tol."""
    if len(points) == 0 or len(reference) == 0:
        return np.nan
    gaps = [p - reference[np.argmin(np.abs(reference - p))] for p in points if np.isfinite(p)]
    gaps = [x for x in gaps if abs(x) <= tol]
    return float(np.mean(gaps)) if gaps else np.nan


# ---------- one race ----------

def clean_laps(laps):
    """Green-flag racing laps: not lap 1, not in or out laps, within 4% of the driver's median."""
    laps = laps[(laps["lap_number"] > 1) & ~laps["is_pit_out_lap"].fillna(False).astype(bool)
                & laps["lap_duration"].notna()].copy()
    nxt = laps.sort_values("lap_number").groupby("driver_number")["is_pit_out_lap"].shift(-1)
    laps = laps[nxt.reindex(laps.index).fillna(False).astype(bool) == False]     # drop in-laps
    med = laps.groupby("driver_number")["lap_duration"].transform("median")
    return laps[laps["lap_duration"] < med * 1.04]


def build_race(folder):
    """Fetch and measure every driver of one race. Writes data/processed/style/{folder}.parquet."""
    from prepare_race import get, to_dt
    info = json.loads((RACES_DIR / folder / "info.json").read_text(encoding="utf-8"))
    laps = clean_laps(pd.read_parquet(RACES_DIR / folder / "laps.parquet"))
    start = pd.Timestamp(info["session_start"])
    drivers = {int(d["number"]): d for d in info.get("drivers", [])}
    rows, game = [], []
    for num, d in drivers.items():
        mine = laps[laps["driver_number"] == num]
        if len(mine) < 5:
            continue
        car = pd.DataFrame(get("car_data", {"session_key": info["openf1_session_key"], "driver_number": num}))
        if car.empty:
            continue
        car["t"] = (to_dt(car["date"]) - start).dt.total_seconds()
        car = car.sort_values("t")
        picked = mine.iloc[np.linspace(0, len(mine) - 1, min(LAPS_PER_DRIVER, len(mine))).astype(int)]
        kept = 0
        for _, lap in picked.iterrows():
            g = lap_grid(car, float(lap["t_start"]), float(lap["lap_duration"]))
            if g is None:
                continue
            b0, b1, pk = zone_points(g)
            row = {"folder": folder, "season": info["season"], "round": info["round"],
                   "race_name": info["race_name"], "team": d["team"], "colour": d.get("colour") or "#8a8a96",
                   "driver": d["code"], "name": d["name"], "number": num,
                   "lap": int(lap["lap_number"]), "lap_time": float(lap["lap_duration"]),
                   "compound": lap.get("compound"), "tyre_age": lap.get("tyre_age"),
                   "_brake_on": json.dumps(np.round(b0, 1).tolist()),
                   "_brake_off": json.dumps(np.round(b1, 1).tolist()),
                   "_pickup": json.dumps(np.round(pk, 1).tolist()),
                   **habits(g)}
            rows.append(row)
            if kept < GAME_PER_DRIVER and len(picked) > 2 and lap["lap_number"] > 5:
                game.append({**{k: row[k] for k in ("folder", "team", "driver", "lap", "lap_time", "compound")},
                             "speed": np.round(g["speed"]).astype(int).tolist(),
                             "throttle": np.round(g["throttle"]).astype(int).tolist(),
                             "brake": np.round(g["brake"]).astype(int).tolist(),
                             "gear": np.round(g["n_gear"]).astype(int).tolist(),
                             "length": float(g["length"])})
                kept += 1
    STYLE_DIR.mkdir(parents=True, exist_ok=True)
    out = pd.DataFrame(rows)
    out.to_parquet(STYLE_DIR / f"{folder}.parquet", index=False)
    if game:
        pd.DataFrame(game).to_parquet(STYLE_DIR / f"{folder}_game.parquet", index=False)
    return out


# ---------- team-centring ----------

def load_laps():
    files = sorted(p for p in STYLE_DIR.glob("*.parquet") if not p.stem.endswith("_game"))
    if not files:
        return pd.DataFrame()
    return pd.concat([pd.read_parquet(p) for p in files], ignore_index=True)


def centred(df):
    """Every habit minus the team's average for that race (all its laps, whoever drove them).
    The braking-point habits are measured against the teammate's zones directly.
    Only team-races with two drivers are kept."""
    df = df.copy()
    pairs = df.groupby(["folder", "team"])["driver"].transform("nunique")
    df = df[pairs == 2].copy()
    # braking and pickup points: offset of each lap's zones from the team's pooled zones
    for col, feat in (("_brake_on", "brake_point"), ("_brake_off", "brake_release"), ("_pickup", "throttle_pickup")):
        vals = []
        for (folder, team), grp in df.groupby(["folder", "team"], sort=False):
            pooled = {}
            for drv, g2 in grp.groupby("driver"):
                pooled[drv] = np.concatenate([np.array(json.loads(x)) for x in g2[col]])
            ref_all = np.sort(np.concatenate(list(pooled.values())))
            for idx, row in grp.iterrows():
                pts = np.array(json.loads(row[col]))
                vals.append((idx, match_offsets(pts, ref_all)))
        s = pd.Series(dict(vals))
        df[feat] = s.reindex(df.index)
        if feat == "throttle_pickup":
            df[feat] = -df[feat]                  # positive = earlier on the throttle
    feats = list(FEATURES)
    # a plain average of all the team's laps in that race: it needs no knowledge of whose lap is whose
    tm = df.groupby(["folder", "team"])[feats].transform("mean").to_numpy()
    df[feats] = df[feats].to_numpy() - tm
    df[feats] = df[feats].fillna(0.0)
    return df


# ---------- model ----------

def fit(df):
    """Standardise the team-centred habits and fit a multinomial logistic regression over drivers."""
    from sklearn.linear_model import LogisticRegression
    feats = list(FEATURES)
    mu, sd = df[feats].mean(), df[feats].std().replace(0, 1)
    X = ((df[feats] - mu) / sd).to_numpy()
    model = LogisticRegression(C=0.5, max_iter=3000)
    model.fit(X, df["driver"])
    return model, mu, sd


def pair_score(model, mu, sd, rows, a, b):
    """Log-odds that each row was driven by a rather than b (0 when either driver is unknown)."""
    feats = list(FEATURES)
    X = ((rows[feats] - mu) / sd).to_numpy()
    classes = list(model.classes_)
    if a not in classes or b not in classes:
        return np.zeros(len(rows))
    logit = model.decision_function(X)
    return logit[:, classes.index(a)] - logit[:, classes.index(b)]


def pair_proba(model, mu, sd, rows, a, b):
    """P(lap was driven by a) for each row, using only drivers a and b."""
    return 1 / (1 + np.exp(-pair_score(model, mu, sd, rows, a, b)))


def evaluate(df, folds=6):
    """Grouped cross-validation by race. Scores the teammate question on unseen races:
    one lap at a time, and on a vote over all of a driver's laps in that race."""
    rng = np.random.default_rng(7)
    races = np.array(sorted(df["folder"].unique()))
    rng.shuffle(races)
    groups = np.array_split(races, folds)
    preds = []
    for test_races in groups:
        train = df[~df["folder"].isin(test_races)]
        test = df[df["folder"].isin(test_races)]
        model, mu, sd = fit(train)
        for (folder, team), grp in test.groupby(["folder", "team"]):
            a, b = sorted(grp["driver"].unique())
            score = pair_score(model, mu, sd, grp, a, b)
            p = 1 / (1 + np.exp(-score))
            for (idx, row), pa, sc in zip(grp.iterrows(), p, score):
                preds.append({"idx": idx, "lap": row["lap"], "score_a": sc,
                              "folder": folder, "team": team, "driver": row["driver"], "a": a, "b": b,
                              "p_true": pa if row["driver"] == a else 1 - pa,
                              "known": a in model.classes_ and b in model.classes_})
    pr = pd.DataFrame(preds)
    oof = pr.set_index("idx")["score_a"]
    pr = pr[pr["known"]]
    lap_acc = float((pr["p_true"] > 0.5).mean())
    vote = pr.groupby(["folder", "team", "driver"])["p_true"].apply(lambda s: np.log(s.clip(1e-6)).sum()
                                                                     - np.log((1 - s).clip(1e-6)).sum())
    race_acc = float((vote > 0).mean())
    by_team = (pr.assign(ok=pr["p_true"] > 0.5).groupby("team")["ok"].agg(["mean", "size"])
               .sort_values("mean", ascending=False))
    return {"lap_accuracy": lap_acc, "race_accuracy": race_acc, "laps": int(len(pr)),
            "races": int(pr["folder"].nunique()),
            "by_team": {t: {"accuracy": float(r["mean"]), "laps": int(r["size"])} for t, r in by_team.iterrows()},
            "_oof": oof}


def signatures(model, mu, sd, df, top=3):
    """Each driver's strongest habits relative to their teammates: the average team-centred value
    of each habit in standard deviations, and the habits the model leans on most."""
    feats = list(FEATURES)
    z = (df[feats] - mu) / sd
    out = {}
    for drv, grp in z.groupby(df["driver"]):
        mean = grp.mean()
        n = len(grp)
        order = mean.abs().sort_values(ascending=False).index[:top]
        out[drv] = {"laps": n, "habits": [{"feature": f, "z": round(float(mean[f]), 2),
                                           "raw": round(float(df.loc[grp.index, f].mean()), 3)} for f in order]}
    return out


def train_and_save():
    df = centred(load_laps())
    if df.empty:
        print("No laps yet. Run with --missing first.")
        return
    score = evaluate(df)
    df["oof_score_a"] = score.pop("_oof").reindex(df.index).fillna(0.0)
    model, mu, sd = fit(df)
    sig = signatures(model, mu, sd, df)
    latest = df.sort_values(["season", "round"]).drop_duplicates("driver", keep="last").set_index("driver")
    names = latest["name"].to_dict()
    teams = {d: {"team": r["team"], "colour": r["colour"]} for d, r in latest.iterrows()}
    payload = {
        "features": FEATURES, "classes": list(model.classes_),
        "coef": np.round(model.coef_, 5).tolist(), "intercept": np.round(model.intercept_, 5).tolist(),
        "mu": mu.round(6).to_dict(), "sd": sd.round(6).to_dict(),
        "score": score, "signatures": sig, "names": names, "teams": teams,
        "built": time.strftime("%Y-%m-%d"),
    }
    MODEL_JSON.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    # game laps, with the team-centred habits attached so the page needs no OpenF1 calls
    game_files = sorted(STYLE_DIR.glob("*_game.parquet"))
    if game_files:
        game = pd.concat([pd.read_parquet(p) for p in game_files], ignore_index=True)
        keyed = df.set_index(["folder", "team", "driver", "lap"])[list(FEATURES) + ["oof_score_a", "colour", "name", "race_name", "season", "round", "number"]]
        game = game.join(keyed, on=["folder", "team", "driver", "lap"], how="inner")
        pairs = game.groupby(["folder", "team"])["driver"].transform("nunique")
        game = game[pairs == 2]
        game.to_parquet(GAME_LAPS, index=False)
        print(f"Game laps: {len(game)}")
    print(f"Lap accuracy {score['lap_accuracy']:.1%} · race vote {score['race_accuracy']:.1%} "
          f"on {score['laps']} laps from {score['races']} unseen races")


# ---------- loading for the page ----------

def load_model():
    return json.loads(MODEL_JSON.read_text(encoding="utf-8"))


def page_pair_proba(model, row, a, b):
    """The saved model's P(a) for one lap (row has the team-centred habits)."""
    feats = list(model["features"])
    x = np.array([(row[f] - model["mu"][f]) / model["sd"][f] for f in feats])
    classes = model["classes"]
    if a not in classes or b not in classes:
        return 0.5, []
    ca, cb = np.array(model["coef"][classes.index(a)]), np.array(model["coef"][classes.index(b)])
    ia, ib = model["intercept"][classes.index(a)], model["intercept"][classes.index(b)]
    contrib = (ca - cb) * x
    logit = float(contrib.sum() + ia - ib)
    reasons = sorted(zip(feats, contrib), key=lambda t: -abs(t[1]))
    return 1 / (1 + np.exp(-logit)), reasons


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("folders", nargs="*")
    parser.add_argument("--missing", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--train", action="store_true")
    args = parser.parse_args()
    if args.train and not args.missing and not args.folders:
        train_and_save()
        return
    folders = args.folders or sorted(p.name for p in RACES_DIR.iterdir() if (p / "laps.parquet").exists())
    if args.missing:
        folders = [f for f in folders if not (STYLE_DIR / f"{f}.parquet").exists()]
    if args.limit:
        folders = folders[:args.limit]
    built = 0
    for f in folders:
        t = time.time()
        try:
            out = build_race(f)
            built += 1
            print(f"{f}: {len(out)} laps ({time.time() - t:.0f} s)", flush=True)
        except Exception as error:
            print(f"{f}: failed ({error})", flush=True)
    if args.train and built:                      # --missing --train: retrain only when a race was added
        train_and_save()


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
