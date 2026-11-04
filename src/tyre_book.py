"""What the strategist learns from earlier races.

1. The tyre book: for every circuit, how hard it is on tyres and how long teams really run
   them (compared with typical values), how much a pit stop costs and when teams usually stop.
2. The pit-timing model: from thousands of past laps, how likely a real team is to pit on a lap,
   given the tyre's age, how far into the race it is, the safety car, and so on.

THE NO-FUTURE RULE again: the book and the model used for a race only ever come from races
that happened BEFORE it (the pit-timing model: only from earlier seasons).

Usage:
  python src/tyre_book.py          rebuild the book and the pit-timing models, and print how they score
"""
import json
import re

import numpy as np
import pandas as pd

from predictor import RACES_DIR
from tyres import clean_laps, fit, pit_loss

ROOT = RACES_DIR.parent.parent
HISTORY_DIR = RACES_DIR.parent / "history"
BOOK_FILE = RACES_DIR.parent / "processed" / "tyre_book.csv"
PIT_MODEL_FILE = ROOT / "models" / "pit_timing.json"

DRY = ["SOFT", "MEDIUM", "HARD"]
RED_FLAG = re.compile(r"\bRED FLAG\b")
RED_FLAG_LANE = 45
GENERIC = {"offset": {"SOFT": -0.5, "MEDIUM": 0.0, "HARD": 0.4},     # typical values, before any learning
           "wear": {"SOFT": 0.09, "MEDIUM": 0.05, "HARD": 0.03},
           "life": {"SOFT": 35, "MEDIUM": 45, "HARD": 55},
           "pit_loss": 22.0, "first_stop": 0.4}
MIN_STINTS = 6                  # stints a race needs before its stint lengths are used
FIRST_MODEL_SEASON = 2024       # the pit-timing model needs at least one earlier season


# ---------- reading the races ----------

def race_list():
    """Every race we have laps for, from the full race folders and the light history."""
    races = {}
    for p in sorted(HISTORY_DIR.glob("*_*")):
        if (p / "meta.json").exists():
            races[p.name] = dict(json.loads((p / "meta.json").read_text()), path=p)
    for p in sorted(RACES_DIR.glob("*_*")):
        if (p / "info.json").exists():
            info = json.loads((p / "info.json").read_text())
            races[p.name] = {k: info.get(k) for k in ("season", "round", "race_name", "location", "laps")} | {"path": p}
    return [dict(r, folder=f) for f, r in sorted(races.items())]


def load(race):
    laps = pd.read_parquet(race["path"] / "laps.parquet")
    pits = pd.read_parquet(race["path"] / "pits.parquet")
    control = pd.read_parquet(race["path"] / "race_control.parquet")
    if len(control):
        control = control.dropna(subset=["t"])
    return laps, pits, control


def real_pits(pits, laps=None):
    """Real pit stops (driver, in-lap): no red-flag stoppages, no lap 1, back-to-back laps once.
    If OpenF1 has no pit records for a race (early 2023), they are worked out from the laps."""
    if (pits.empty or "lane_duration" not in pits) and laps is not None and len(laps):
        out = laps[laps["is_pit_out_lap"].fillna(False).astype(bool) & (laps["lap_number"] > 1)]
        normal = laps["lap_duration"].median()
        slow = laps.set_index(["driver_number", "lap_number"])["lap_duration"]
        rows = []
        for d, L in zip(out["driver_number"], out["lap_number"]):
            durations = [slow.get((d, L - 1)), slow.get((d, L))]
            if any(pd.notna(x) and x > 3 * normal for x in durations):
                continue                                    # a red-flag stoppage, not a stop
            rows.append({"driver_number": d, "lap_number": L - 1, "lane_duration": 0.0})
        pits = pd.DataFrame(rows, columns=["driver_number", "lap_number", "lane_duration"])
    if pits.empty or "lane_duration" not in pits:
        return pd.DataFrame(columns=["driver_number", "lap"])
    p = pits.dropna(subset=["lap_number", "lane_duration"])
    p = p[(p["lap_number"] > 1) & (p["lane_duration"] <= RED_FLAG_LANE)]
    p = p.sort_values(["driver_number", "lap_number"])
    p = p[~(p.groupby("driver_number")["lap_number"].diff() == 1)]
    return (p[["driver_number", "lap_number"]].rename(columns={"lap_number": "lap"})
            .astype(int).reset_index(drop=True))


def neutral_laps(laps, control):
    """For every (driver, lap): was a safety car, VSC or red flag out when the car finished it?"""
    if control.empty:
        return set(), set()
    events = []
    for t, msg in zip(control["t"], control["message"].fillna("").str.upper()):
        if RED_FLAG.search(msg):
            events.append((t, "RED"))
        elif "VSC DEPLOYED" in msg or "VIRTUAL SAFETY CAR DEPLOYED" in msg:
            events.append((t, "VSC"))
        elif "SAFETY CAR DEPLOYED" in msg:
            events.append((t, "SC"))
        elif any(w in msg for w in ("VSC ENDING", "VIRTUAL SAFETY CAR ENDING", "SAFETY CAR IN THIS LAP",
                                    "TRACK CLEAR", "RESUM")):
            events.append((t, None))
    events.sort(key=lambda e: e[0])
    times = np.array([e[0] for e in events])
    kinds = [e[1] for e in events]
    sc, red = set(), set()
    ends = laps["t_start"] + laps["lap_duration"]
    for d, L, end in zip(laps["driver_number"], laps["lap_number"], ends):
        if pd.isna(end):
            continue
        i = np.searchsorted(times, end, side="right") - 1
        if i >= 0 and kinds[i] in ("SC", "VSC"):
            sc.add((d, L))
        elif i >= 0 and kinds[i] == "RED":
            red.add((d, L))
    return sc, red


# ---------- the tyre book ----------

def race_rows(race):
    """What one race tells us: how hard it was on tyres and how long teams ran them,
    compared with typical values, plus the pit stop loss and when teams first stopped."""
    laps, pits, _ = load(race)
    total = int(laps["lap_number"].max())
    stops = real_pits(pits, laps)

    # tyre wear compared with typical: fitted on the whole race (it is in the past now)
    clean = clean_laps(laps)
    clean = clean[clean["compound"].isin(DRY)]
    counts = clean["compound"].value_counts()
    comps = [c for c in DRY if counts.get(c, 0) >= 30
             and clean.loc[clean["compound"] == c, "driver_number"].nunique() >= 3]
    wear_factor = np.nan
    if comps and len(clean) >= 200:
        data = clean[clean["compound"].isin(comps)]
        drivers = sorted(data["driver_number"].unique())
        coef = fit(data, drivers, comps)
        wear = coef[len(drivers) + len(comps):]
        ratios = [max(w, 0.0) / GENERIC["wear"][c] for c, w in zip(comps, wear)]
        wear_factor = float(np.clip(np.median(ratios), 0.3, 3.0))

    # stint lengths compared with typical: stints that ended with a real stop
    ratios = []
    for d, mine in laps.groupby("driver_number"):
        for lap in stops.loc[stops["driver_number"] == d, "lap"]:
            row = mine[mine["lap_number"] == lap]
            if len(row) and row["compound"].iloc[0] in DRY and pd.notna(row["tyre_age"].iloc[0]):
                ratios.append((float(row["tyre_age"].iloc[0]) + 1) / GENERIC["life"][row["compound"].iloc[0]])

    first = stops.groupby("driver_number")["lap"].min()
    first = first[first > 3]
    return [{"folder": race["folder"], "season": int(race["season"]), "round": int(race["round"]),
             "location": race.get("location"), "laps": total, "pit_loss": pit_loss(laps),
             "first_stop": float((first / total).median()) if len(first) else np.nan,
             "wear_factor": wear_factor,
             "stint_factor": float(np.percentile(ratios, 90)) if len(ratios) >= MIN_STINTS else np.nan,
             "stints": len(ratios)}]


def build_book():
    rows = []
    for race in race_list():
        try:
            rows += race_rows(race)
        except Exception as error:
            print(f"  Skipped {race['folder']} in the tyre book: {error}")
    book = pd.DataFrame(rows)
    BOOK_FILE.parent.mkdir(parents=True, exist_ok=True)
    book.to_csv(BOOK_FILE, index=False)
    return book


def read_book():
    return pd.read_csv(BOOK_FILE) if BOOK_FILE.exists() else pd.DataFrame()


def book_for(season, rnd, location, book=None):
    """The starting knowledge for one race, from races strictly before it.
    The circuit's own races count most; all circuits fill the gaps."""
    book = read_book() if book is None else book
    out = {k: (dict(v) if isinstance(v, dict) else v) for k, v in GENERIC.items()}
    out.update(source="typical values", wear_factor=1.0, stint_factor=1.0)
    if book.empty:
        return out
    before = book[(book["season"] < season) | ((book["season"] == season) & (book["round"] < rnd))]
    if before.empty:
        return out
    here = before[before["location"] == location]

    def mix(col):
        overall, local = before[col].median(), here[col].median()
        if pd.isna(local):
            return overall
        k = here[col].notna().sum()
        w = k / (k + 1.0)                                 # one race at this circuit = half the weight
        return w * local + (1 - w) * overall if pd.notna(overall) else local

    # the circuit compared with an average circuit (1.0 = average, 1.5 = 50% more)
    factors = {col: mix(col) for col in ("wear_factor", "stint_factor", "pit_loss", "first_stop")}
    for col, key, limits in (("wear_factor", "wear", (0.4, 2.5)), ("stint_factor", "life", (0.6, 1.8))):
        average = before[col].median()
        if pd.notna(factors[col]) and pd.notna(average) and average > 0:
            out[col] = float(np.clip(factors[col] / average, *limits))
            out[key] = {c: GENERIC[key][c] * out[col] for c in DRY}
    for col in ("pit_loss", "first_stop"):
        if pd.notna(factors[col]):
            out[col] = float(factors[col])
    n = here["folder"].nunique()
    out["source"] = f"{n} earlier race{'s' if n != 1 else ''} here, {before['folder'].nunique()} in all"
    return out


# ---------- the pit-timing model ----------

FEATURES = ["age_life", "age_life2", "progress", "reach", "need_stop", "stops", "window", "window2",
            "neutral", "soft", "hard"]


def features(age, comp, k, total, stops, need_stop, neutral, book):
    """The model's inputs, in the order of FEATURES. `age` and `k` can be arrays (future laps of one stint)."""
    k = np.atleast_1d(np.asarray(k, dtype=float))
    age = np.broadcast_to(np.asarray(age, dtype=float), k.shape)
    a = age / book["life"].get(comp, 40)
    progress = k / total
    reach = (total - k) / max(book["life"].values())
    window = (progress - book["first_stop"]) if stops == 0 else np.zeros_like(k)
    const = lambda v: np.full(k.shape, float(v))
    cols = [a, a ** 2, progress, reach, const(need_stop), const(min(stops, 2)), window, window ** 2,
            np.broadcast_to(np.asarray(neutral, dtype=float), k.shape),
            const(comp == "SOFT"), const(comp == "HARD")]
    return np.column_stack(cols)


def training_rows(race, book):
    """One row per racing lap: the features, and whether the car really pitted at the end of it."""
    laps, pits, control = load(race)
    total = int(laps["lap_number"].max())
    stops = real_pits(pits, laps)
    stop_set = set(zip(stops["driver_number"], stops["lap"]))
    sc, red = neutral_laps(laps, control)
    X, y = [], []
    for d, mine in laps.sort_values("lap_number").groupby("driver_number"):
        made, used = 0, set()
        out_laps = set(mine.loc[mine["is_pit_out_lap"].fillna(False).astype(bool), "lap_number"])
        for r in mine.itertuples():
            L = int(r.lap_number)
            if r.compound in DRY:
                used.add(r.compound)
            ok = (r.compound in DRY and pd.notna(r.tyre_age) and 3 < L <= total - 2
                  and L not in out_laps and (d, L) not in red)
            if ok:
                X.append(features(r.tyre_age, r.compound, L, total, made, float(len(used) < 2),
                                  float((d, L) in sc), book)[0])
                y.append((d, L) in stop_set)
            if (d, L) in stop_set:
                made += 1
    return np.array(X), np.array(y, dtype=float)


def fit_logistic(X, y, l2=1.0, steps=400):
    """A small logistic regression (no extra libraries needed to use it later)."""
    mean, scale = X.mean(axis=0), X.std(axis=0) + 1e-9
    Z = (X - mean) / scale
    w, b = np.zeros(Z.shape[1]), np.log(y.mean() / (1 - y.mean()))
    lr = 0.5
    for _ in range(steps):                                  # plain gradient descent, it is a tiny model
        p = 1 / (1 + np.exp(-(Z @ w + b)))
        w -= lr * (Z.T @ (p - y) / len(y) + l2 * w / len(y))
        b -= lr * float(np.mean(p - y))
    return {"mean": mean.tolist(), "scale": scale.tolist(), "w": w.tolist(), "b": float(b)}


def hazard(model, X):
    """Chance that a team pits at the end of each lap."""
    Z = (X - np.array(model["mean"])) / np.array(model["scale"])
    return 1 / (1 + np.exp(-(Z @ np.array(model["w"]) + model["b"])))


def log_loss(p, y):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def build_pit_models(book):
    """One model per season, each trained only on the seasons before it."""
    races = race_list()
    data = {}
    for race in races:
        b = book_for(int(race["season"]), int(race["round"]), race.get("location"), book)
        try:
            data[race["folder"]] = (int(race["season"]), *training_rows(race, b))
        except Exception as error:
            print(f"  Skipped {race['folder']} in the pit-timing data: {error}")
    seasons = sorted({s for s, _, _ in data.values()})
    models = {}
    for season in [s for s in seasons + [max(seasons, default=0) + 1] if s >= FIRST_MODEL_SEASON]:
        train = [(X, y) for s, X, y in data.values() if s < season and len(y)]
        if not train:
            continue
        X = np.vstack([t[0] for t in train]); y = np.concatenate([t[1] for t in train])
        model = fit_logistic(X, y)
        model["trained_on"] = f"{len(train)} races before {season} ({len(y):,} laps, {int(y.sum()):,} pit stops)"
        test = [(X, y) for s, X, y in data.values() if s == season and len(y)]
        if test:
            Xt = np.vstack([t[0] for t in test]); yt = np.concatenate([t[1] for t in test])
            model["test"] = {"races": len(test), "log_loss": log_loss(hazard(model, Xt), yt),
                             "baseline": log_loss(np.full(len(yt), y.mean()), yt)}
        models[str(season)] = model
    PIT_MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    PIT_MODEL_FILE.write_text(json.dumps({"features": FEATURES, "models": models}, indent=2))
    return models


def pit_model_for(season):
    """The pit-timing model for a race in this season (trained on earlier seasons), or None."""
    if not PIT_MODEL_FILE.exists():
        return None
    models = json.loads(PIT_MODEL_FILE.read_text())["models"]
    usable = [int(s) for s in models if int(s) <= season]
    return models[str(max(usable))] if usable else None


def main():
    book = build_book()
    print(f"Tyre book: {book['folder'].nunique()} races, {book['location'].nunique()} circuits -> {BOOK_FILE.name}")
    models = build_pit_models(book)
    for season, m in models.items():
        line = f"  Pit-timing model for {season}: trained on {m['trained_on']}"
        if "test" in m:
            t = m["test"]
            line += (f"; tested on {t['races']} races of {season}: log loss {t['log_loss']:.4f} "
                     f"(guessing the average: {t['baseline']:.4f}, lower is better)")
        print(line)


if __name__ == "__main__":
    main()
