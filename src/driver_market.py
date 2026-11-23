"""Driver Market (M10): who is likely to keep their seat, change team or leave F1 next season, and why.

Every driver-season since 1980 (drivers who started at least a third of the races) becomes one row, and the
label is what happened the next year: the same team, another team, or out of F1. The features are what a
team principal looks at:
  age at the end of the season (dates of birth from Jolpica, cached), seasons in F1, seasons with the team
  form: championship position (as a share of the field), finishing rate
  against the teammate: share of the team's points, share of races started ahead of them on the grid
  the team: its championship position, and whether it went backwards this year
A renamed or sold team counts as the same team (Toro Rosso to AlphaTauri to RB, Sauber to Audi, ...).
Contracts would help most, but there is no free source of contract lengths, so the model goes without.

The model is a multinomial logistic regression on standardised features, so every prediction comes with
its reasons: each feature's push towards staying, moving or leaving. Tested out of sample: each season from
2010 on predicted by a model trained only on the seasons before it.

Saves data/processed/driver_market.json
    python src/driver_market.py
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent.parent
HIST = ROOT / "data" / "processed" / "history_results.csv"
DOB = ROOT / "data" / "processed" / "driver_dob.json"
OUT = ROOT / "data" / "processed" / "driver_market.json"
BASE_URL = "https://api.jolpi.ca/ergast/f1"
FIRST = 1980
CLASSES = ["stay", "move", "out"]
FEATURES = {
    "age": "age", "age2": "late career", "career": "F1 seasons", "tenure": "years at the team",
    "champ_share": "championship place", "finish_rate": "finishing rate", "pts_share": "share of team points",
    "grid_h2h": "grid vs teammate", "team_rank": "team's position", "team_drop": "team slipping", "rookie": "rookie",
}


LINEAGE = {   # renamed or sold teams are one team: staying through a rename is staying
    **dict.fromkeys(["toleman", "benetton", "renault", "lotus_f1", "alpine"], "enstone"),
    **dict.fromkeys(["jordan", "mf1", "spyker_mf1", "spyker", "force_india", "racing_point", "aston_martin"], "silverstone"),
    **dict.fromkeys(["stewart", "jaguar", "red_bull"], "milton_keynes"),
    **dict.fromkeys(["minardi", "toro_rosso", "alphatauri", "rb"], "faenza"),
    **dict.fromkeys(["tyrrell", "bar", "honda", "brawn", "mercedes"], "brackley"),
    **dict.fromkeys(["sauber", "bmw_sauber", "audi"], "hinwil"),
    **dict.fromkeys(["arrows", "footwork"], "arrows"), **dict.fromkeys(["virgin", "marussia", "manor"], "banbury"),
    **dict.fromkeys(["lotus_racing", "caterham"], "hingham"), **dict.fromkeys(["ligier", "prost"], "magny_cours"),
}


def lineage(team, season):
    if team == "alfa" and season >= 2019:                  # Alfa Romeo 2019-23 was Sauber (not the 1980s works team)
        return "hinwil"
    return LINEAGE.get(team, team)


def dates_of_birth():
    """{driver id: 'YYYY-MM-DD'} from Jolpica, fetched once and cached."""
    have = json.loads(DOB.read_text()) if DOB.exists() else {}
    if len(have) > 800:
        return have
    offset = 0
    while True:
        data = requests.get(f"{BASE_URL}/drivers.json", params={"limit": 100, "offset": offset}, timeout=30).json()
        table = data["MRData"]["DriverTable"]["Drivers"]
        for d in table:
            if d.get("dateOfBirth"):
                have[d["driverId"]] = d["dateOfBirth"]
        offset += 100
        if offset >= int(data["MRData"]["total"]):
            break
        time.sleep(0.4)
    DOB.write_text(json.dumps(have, indent=0, sort_keys=True))
    return have


def seasons_table(hist, dob):
    """One row per driver-season: features and the next season's outcome."""
    hist = hist[hist["season"] >= FIRST - 10].copy()
    hist["finished"] = hist["status"].astype(str).str.match(r"^(Finished|\+\d+ Laps?)$")
    races = hist.groupby("season")["round"].nunique()
    rows = []
    # each driver's main team in each season: the one they started most races for
    starts = hist.groupby(["season", "driver", "constructor"]).size().rename("n").reset_index()
    main = starts.sort_values("n").groupby(["season", "driver"]).tail(1).set_index(["season", "driver"])
    main["line"] = [lineage(t, s) for (s, _), t in zip(main.index, main["constructor"])]
    team_pts = hist.groupby(["season", "constructor"])["points"].sum()
    team_rank = team_pts.groupby(level=0).rank(ascending=False, method="min")
    n_teams = team_pts.groupby(level=0).size()
    drv_pts = hist.groupby(["season", "driver"])["points"].sum()
    drv_rank = drv_pts.groupby(level=0).rank(ascending=False, method="min")
    n_drv = drv_pts.groupby(level=0).size()
    first_season = hist.groupby("driver")["season"].min()
    seasons_by_driver = hist.groupby("driver")["season"].apply(lambda s: sorted(set(s)))
    for (season, driver), m in main.iterrows():
        if season < FIRST or m["n"] < races[season] / 3:
            continue
        team = m["constructor"]
        mine = hist[(hist["season"] == season) & (hist["driver"] == driver)]
        mates = hist[(hist["season"] == season) & (hist["constructor"] == team) & (hist["driver"] != driver)]
        both = mine.merge(mates[["round", "grid", "points"]], on="round", suffixes=("", "_mate"))
        valid = both[(both["grid"] > 0) & (both["grid_mate"] > 0)]
        grid_h2h = float((valid["grid"] < valid["grid_mate"]).mean()) if len(valid) else 0.5
        tp = team_pts.get((season, team), 0.0)
        pts_share = float(mine.loc[mine["constructor"] == team, "points"].sum() / tp) if tp > 0 else 0.5
        past = [s for s in seasons_by_driver[driver] if s <= season]
        tenure = 0
        for s in range(season, FIRST - 30, -1):
            if (s, driver) in main.index and main.loc[(s, driver), "line"] == lineage(team, season):
                tenure += 1
            else:
                break
        prev_rank = team_rank.get((season - 1, team), np.nan)
        b = dob.get(driver)
        age = (pd.Timestamp(f"{season}-12-01") - pd.Timestamp(b)).days / 365.25 if b else np.nan
        if (season + 1, driver) in main.index and main.loc[(season + 1, driver), "n"] >= 1:
            nxt = "stay" if main.loc[(season + 1, driver), "line"] == lineage(team, season) else "move"
        elif season + 1 in races.index:
            nxt = "out"
        else:
            nxt = None                                          # the latest season: what we predict
        rows.append({
            "season": int(season), "driver": driver, "name": mine["driver_name"].iloc[0], "team": team,
            "team_name": mine.loc[mine["constructor"] == team, "constructor_name"].iloc[0], "age": age,
            "career": len(past), "tenure": tenure,
            "champ_share": float(drv_rank[(season, driver)] / n_drv[season]),
            "finish_rate": float(mine["finished"].mean()), "pts_share": pts_share, "grid_h2h": grid_h2h,
            "team_rank": float(team_rank.get((season, team), n_teams[season]) / n_teams[season]),
            "team_drop": float(team_rank.get((season, team), 0) > prev_rank) if not np.isnan(prev_rank) else 0.0,
            "rookie": float(first_season[driver] == season), "next": nxt,
        })
    df = pd.DataFrame(rows)
    df["age"] = df["age"].fillna(df["age"].median())
    df["age2"] = np.maximum(df["age"] - 32, 0) ** 2
    return df


def fit(train):
    sc = StandardScaler().fit(train[list(FEATURES)])
    model = LogisticRegression(max_iter=2000, C=0.5).fit(sc.transform(train[list(FEATURES)]), train["next"])
    return sc, model


def predict(sc, model, rows):
    z = sc.transform(rows[list(FEATURES)])
    p = model.predict_proba(z)
    cls = list(model.classes_)
    out = pd.DataFrame(p, columns=cls, index=rows.index)[CLASSES]
    contrib = {c: z * model.coef_[cls.index(c)] for c in CLASSES}
    return out, contrib


def reasons(contrib, i, top=3):
    """The features pushing hardest towards leaving the seat (move or out) vs staying, for row i."""
    push = (np.logaddexp(contrib["move"][i], contrib["out"][i]) - contrib["stay"][i])
    order = np.argsort(-np.abs(push))[:top]
    names = list(FEATURES)
    return [{"feature": FEATURES[names[k]], "push": round(float(push[k]), 2)} for k in order]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    hist = pd.read_csv(HIST)
    df = seasons_table(hist, dates_of_birth())
    known = df[df["next"].notna()]
    latest = int(df["season"].max())
    # out of sample, season by season
    tests = []
    for y in range(2010, latest):
        tr, te = known[known["season"] < y], known[known["season"] == y]
        if te.empty:
            continue
        sc, model = fit(tr)
        p, _ = predict(sc, model, te)
        base = tr["next"].value_counts(normalize=True).reindex(CLASSES).fillna(1e-3)
        idx = [CLASSES.index(c) for c in te["next"]]
        pv = p.to_numpy()[np.arange(len(te)), idx]
        tests.append({"season": y, "n": len(te), "log_loss": float(-np.mean(np.log(np.clip(pv, 1e-6, 1)))),
                      "base_log_loss": float(-np.mean(np.log(base.to_numpy()[idx]))),
                      "accuracy": float((p.idxmax(axis=1) == te["next"]).mean()),
                      "base_accuracy": float((te["next"] == "stay").mean()),
                      "drivers": [{"driver": r.driver, "name": r["name"], "team": r.team_name, "actual": r.next,
                                   **{c: round(float(p.loc[i, c]), 3) for c in CLASSES}}
                                  for i, r in te.iterrows()]})
        print(f"{y}: log loss {tests[-1]['log_loss']:.3f} (base {tests[-1]['base_log_loss']:.3f}), "
              f"accuracy {tests[-1]['accuracy']:.0%} (always 'stay' {tests[-1]['base_accuracy']:.0%})")
    # the live prediction for next season
    sc, model = fit(known)
    now = df[df["season"] == latest].reset_index(drop=True)
    p, contrib = predict(sc, model, now)
    live = []
    for i, r in now.iterrows():
        live.append({"driver": r.driver, "name": r["name"], "team": r.team, "team_name": r.team_name,
                     "age": round(float(r.age), 1), "tenure": int(r.tenure), "pts_share": round(float(r.pts_share), 3),
                     "grid_h2h": round(float(r.grid_h2h), 3), **{c: round(float(p.loc[i, c]), 3) for c in CLASSES},
                     "why": reasons(contrib, i)})
    coef = {c: dict(zip(FEATURES.values(), np.round(model.coef_[list(model.classes_).index(c)], 3).tolist())) for c in CLASSES}
    OUT.write_text(json.dumps({"season": latest, "live": sorted(live, key=lambda x: x["stay"]), "tests": tests,
                               "coef": coef, "rows": int(len(known))}, ensure_ascii=False), encoding="utf-8")
    print(f"saved {OUT.name}: {len(live)} drivers for {latest + 1}")


if __name__ == "__main__":
    main()
