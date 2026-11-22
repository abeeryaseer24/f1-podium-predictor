"""Classic Races: famous Grands Prix since 1996, rebuilt from Jolpica's lap times so they can be replayed.

OpenF1 only starts in 2023, but Jolpica (the Ergast successor) has every driver's lap time and position
for every race since 1996, and pit stops since 2011. From those this rebuilds what the race engine needs:

  base pace    each driver's median clean lap (no lap 1, no pit laps, no safety-car laps)
  pit stops    from Jolpica's pit-stop list (2011+), or found in the lap times before that
               (an in-lap and out-lap pair much slower than the driver's normal laps)
  safety cars  laps where the whole field was more than 15 % slower than normal
  degradation  how much a stint's laps slow down with age, fitted across the field
  fuel         the field's lap-time trend over the race; in the refuelling era (until 2009) cars only
               got lighter within each stint, so fuel is counted from each driver's last stop

There are no tyre compounds or weather in this data: every stint is one generic tyre. The replays say so.

Usage:
  python src/classic.py --fetch      download every race in CLASSICS that isn't saved yet
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

import penalties
from predictor import BASE_URL, RESULTS_CSV

DIR = Path(__file__).resolve().parent.parent / "data" / "classic"

CLASSICS = {
    "1998_12": {"title": "Hungary 1998: three stops to beat McLaren",
                "story": "Ferrari switched Schumacher to a three-stop plan mid-race and asked him for 19 qualifying-pace laps; "
                         "he jumped both McLarens and won. Could a two-stop have done it?"},
    "2005_18": {"title": "Japan 2005: Räikkönen from 17th",
                "story": "Räikkönen started 17th and took the lead from Fisichella on the final lap. Try other strategies for "
                         "the McLaren, or for Fisichella's Renault, to see how close it really was."},
    "2014_3": {"title": "Bahrain 2014: the duel in the desert",
               "story": "Hamilton and Rosberg fought wheel to wheel for laps; a late safety car bunched them up. "
                        "What if Mercedes had split their strategies?"},
    "2016_5": {"title": "Spain 2016: Verstappen's first win",
               "story": "Both Mercedes crashed on lap 1; Red Bull and Ferrari split strategies and the 18-year-old Verstappen "
                        "held off Räikkönen on a two-stop. Was Ricciardo's three-stop the faster plan?"},
    "2019_9": {"title": "Austria 2019: Verstappen hunts down Leclerc",
               "story": "Verstappen dropped to seventh at the start, then charged on fresher tyres and passed Leclerc with three "
                        "laps to go. How much did the tyre offset matter?"},
    "2021_22": {"title": "Abu Dhabi 2021: the title decider",
                "story": "Hamilton led until a late safety car; Verstappen pitted for fresh tyres and passed on the final lap. "
                         "Replay it with and without that safety car, or pit Hamilton too."},
}


# ---------- downloading ----------

def _get(url):
    for attempt in range(5):
        r = requests.get(url, timeout=60)
        if r.status_code == 429:
            time.sleep(5 * (attempt + 1))
            continue
        r.raise_for_status()
        time.sleep(0.4)                            # be polite to the free API
        return r.json()["MRData"]
    raise RuntimeError(f"Jolpica kept refusing: {url}")


def _secs(text):
    m, _, s = text.rpartition(":")
    return float(m or 0) * 60 + float(s)


def fetch(key):
    season, rnd = key.split("_")
    out = DIR / key
    out.mkdir(parents=True, exist_ok=True)
    rows, offset = [], 0
    while True:
        mr = _get(f"{BASE_URL}/{season}/{rnd}/laps.json?limit=100&offset={offset}")
        for lap in mr["RaceTable"]["Races"][0]["Laps"] if mr["RaceTable"]["Races"] else []:
            for t in lap["Timings"]:
                rows.append({"driver": t["driverId"], "lap": int(lap["number"]), "position": int(t["position"]),
                             "time": _secs(t["time"])})
        offset += 100
        if offset >= int(mr["total"]):
            break
    pd.DataFrame(rows).to_parquet(out / "laps.parquet", index=False)
    stops = []
    if int(season) >= 2011:
        mr = _get(f"{BASE_URL}/{season}/{rnd}/pitstops.json?limit=100")
        for p in mr["RaceTable"]["Races"][0]["PitStops"] if mr["RaceTable"]["Races"] else []:
            stops.append({"driver": p["driverId"], "lap": int(p["lap"])})
    pd.DataFrame(stops, columns=["driver", "lap"]).to_parquet(out / "pits.parquet", index=False)
    res = _get(f"{BASE_URL}/{season}/{rnd}/results.json?limit=40")["RaceTable"]["Races"][0]
    info = {"season": int(season), "round": int(rnd), "race_name": res["raceName"], "circuit": res["Circuit"]["circuitId"],
            "drivers": [{"driver": r["Driver"]["driverId"], "code": r["Driver"].get("code") or r["Driver"]["familyName"][:3].upper(),
                         "name": f"{r['Driver']['givenName']} {r['Driver']['familyName']}", "team": r["Constructor"]["name"],
                         "grid": int(r["grid"]) or 99, "position": int(r["position"]),
                         "finished": r["status"] == "Finished" or r["status"].startswith("+")} for r in res["Results"]]}
    (out / "info.json").write_text(json.dumps(info))
    return len(rows)


# ---------- rebuilding a race for the engine ----------

TEAM_COLOURS = {"Ferrari": "#e8002d", "McLaren": "#ff8000", "Mercedes": "#27f4d2", "Red Bull": "#3671c6",
                "Williams": "#64c4ff", "Renault": "#ffd800", "Toyota": "#cc2a2a", "BAR": "#c0c0c0", "Jordan": "#f5c518",
                "Benetton": "#4dc94f", "Alpine": "#ff87bc", "AlphaTauri": "#6692ff", "Aston Martin": "#229971",
                "Alfa Romeo": "#9b0000", "Haas": "#b6babd", "Sauber": "#52e252", "Force India": "#f596c8",
                "Toro Rosso": "#469bff", "Lotus": "#b8a14d", "Prost": "#2b4562", "Stewart": "#ffffff", "Minardi": "#202020",
                "Arrows": "#ff9f1c", "Tyrrell": "#2b6cff", "Jaguar": "#0d6b3f", "Marussia": "#6e0000", "Caterham": "#0d5c2f"}


def colour_for(team):
    for k, v in TEAM_COLOURS.items():
        if k.lower() in team.lower():
            return v
    return "#8a8a96"


def build(key):
    """A race dict in the same shape race_engine.simulate() expects."""
    path = DIR / key
    laps = pd.read_parquet(path / "laps.parquet")
    pits = pd.read_parquet(path / "pits.parquet")
    info = json.loads((path / "info.json").read_text())
    season = info["season"]
    n_laps = int(laps["lap"].max())

    # Safety-car laps: the whole field much slower than its normal pace
    field = laps.groupby("lap")["time"].median()
    normal = field[field.index > 1].median()
    sc_laps = sorted(int(l) for l, t in field.items() if l > 1 and t > normal * 1.15)

    # Pit stops: Jolpica's list, or in-lap/out-lap pairs found in the lap times
    stops = {}
    if len(pits):
        for d, g in pits.groupby("driver"):
            stops[d] = sorted(g["lap"].astype(int).tolist())
    else:
        for d, g in laps.sort_values("lap").groupby("driver"):
            t = g.set_index("lap")["time"]
            med = t[(t.index > 1) & ~t.index.isin(sc_laps)].median()
            found = []
            for lap in t.index:
                if lap <= 1 or lap in sc_laps or lap + 1 not in t.index:
                    continue
                pair = t[lap] + t[lap + 1] - 2 * med
                if pair > 12 and (not found or lap - found[-1] > 3):
                    found.append(int(lap))
            stops[d] = found
    pit_laps = {d: set(s) | {x + 1 for x in s} for d, s in stops.items()}

    # Clean laps, pit loss, fuel and degradation
    clean = laps[(laps["lap"] > 1) & ~laps["lap"].isin(sc_laps)]
    clean = clean[[l not in pit_laps.get(d, set()) for d, l in zip(clean["driver"], clean["lap"])]]
    clean = clean[clean["time"] < clean["time"].median() * 1.07]
    refuel = season <= 2009
    def since_stop(d, lap):
        prev = [s for s in stops.get(d, []) if s < lap]
        return lap - (prev[-1] + 1 if prev else 1)
    clean = clean.assign(age=[since_stop(d, l) for d, l in zip(clean["driver"], clean["lap"])])
    # Fit: time = driver + fuel * (lap or stint lap) + wear * age   (wear only identifiable without refuelling)
    drivers = sorted(clean["driver"].unique())
    X = np.zeros((len(clean), len(drivers) + 2))
    for k, d in enumerate(clean["driver"]):
        X[k, drivers.index(d)] = 1
    fuel_x = clean["age"].to_numpy() if refuel else clean["lap"].to_numpy()
    X[:, -2] = fuel_x
    X[:, -1] = clean["age"].to_numpy()
    if refuel:            # stint age is the same column as fuel here: keep one
        X = X[:, :-1]
    coef, *_ = np.linalg.lstsq(X, clean["time"].to_numpy(), rcond=None)
    base = dict(zip(drivers, coef[:len(drivers)]))
    fuel = float(coef[len(drivers)])
    wear = 0.0 if refuel else float(max(coef[-1], 0.0))
    if refuel:            # fuel burn and tyre wear both follow stint age: one net slope, counted per stint
        wear = 0.0
    pit_loss = []
    for d, s in stops.items():
        t = laps[laps["driver"] == d].set_index("lap")["time"]
        med = t.median()
        for lap in s:
            if lap in t.index and lap + 1 in t.index and lap not in sc_laps:
                pit_loss.append(t[lap] + t[lap + 1] - 2 * med)
    pit_loss = float(np.median([x for x in pit_loss if 8 < x < 45])) if pit_loss else 22.0

    who, grid, real_pos, strategies = {}, {}, {}, {}
    nums = {}
    for k, d in enumerate(info["drivers"]):
        if d["driver"] not in base:
            continue
        num = k + 1
        nums[d["driver"]] = num
        who[num] = {"code": d["code"], "name": d["name"], "team": d["team"], "colour": colour_for(d["team"])}
        grid[num] = d["grid"]
        if d["finished"]:
            real_pos[num] = d["position"]
        st = stops.get(d["driver"], [])
        strategies[num] = [("MEDIUM", s) for s in st] + [("MEDIUM", n_laps)]
    order = sorted(grid, key=grid.get)
    difficulty = penalties.place_costs().get(info["circuit"], penalties.DEFAULT_SLOPE)
    return {"folder": key, "info": {**info, "laps": n_laps}, "drivers": order, "who": who, "grid": grid,
            "base": {nums[d]: v for d, v in base.items() if d in nums}, "fuel": fuel,
            "compounds": {"MEDIUM": {"offset": 0.0, "wear": wear}}, "ref": "MEDIUM", "pit_loss": pit_loss,
            "laps": n_laps, "strategies": strategies, "real_pos": real_pos, "sc_rate": 0.0, "difficulty": difficulty,
            "sc_laps": sc_laps, "refuel": refuel, "stops": {nums[d]: s for d, s in stops.items() if d in nums}}


def saved():
    return [k for k in CLASSICS if (DIR / k / "info.json").exists()]


if __name__ == "__main__":
    if "--fetch" in sys.argv:
        for key in CLASSICS:
            if not (DIR / key / "info.json").exists():
                print(key, fetch(key), "lap timings")
    for key in saved():
        r = build(key)
        print(key, r["info"]["race_name"], f"laps {r['laps']}, SC laps {r['sc_laps'][:6]}..., pit loss {r['pit_loss']:.1f}s, "
              f"fuel {r['fuel']:+.3f}, wear {r['compounds']['MEDIUM']['wear']:.3f}, refuel {r['refuel']}")
