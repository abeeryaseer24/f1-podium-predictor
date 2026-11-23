"""Series Compare (S13): the same circuit lapped by an F1, F2, F3, Formula E and IndyCar-style car.

Every car runs on the lap simulator (lapsim.py) with its own mass, power, downforce and drag:
  F1          the circuit's own calibrated car (as on the Lap Simulator page)
  F2, F3      published basics (weight with driver, engine power, a share of F1's downforce and drag), and
              one fitted number each, the tyre grip, tuned so the simulated lap matches the REAL pole lap of
              the F2 or F3 race held on the same weekend (from Wikipedia's round articles). It's checked by
              leaving each circuit out of the fit in turn and predicting its pole.
  Formula E   published Gen3 numbers only (it never races on these circuits): 350 kW in qualifying, about
              860 kg, little downforce and grooved all-weather tyres
  IndyCar     published road-course numbers only: about 530 kW, 850 kg with driver and fuel, a road-course
              aero kit
Each car uses the F1 car's wing level for that circuit, so the comparison is about the cars, not the setup.

Saves data/processed/series_compare.json.
  python src/series_compare.py
"""
import json
import re
import sys
import time
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ladder as L
import lapsim

OUT = L.ROOT / "data" / "processed" / "series_compare.json"
WET_GAP = 0.10          # a pole more than 10% slower than a dry lap predicts: treated as a wet session

# Published basics. The F2 and F3 grip is fitted; everything else is fixed.
CARS = {
    "F2": {"label": "Formula 2", "colour": "#3a7bd5", "fit": True,
           "car": dict(mass=800, power_kw=430, downforce_scale=0.6, drag_scale=0.85, grip=1.8),
           "source": "Dallara F2 2024: about 800 kg with driver, a 3.4-litre turbo V6 of about 620 hp"},
    "F3": {"label": "Formula 3", "colour": "#c0392b", "fit": True,
           "car": dict(mass=690, power_kw=260, downforce_scale=0.42, drag_scale=0.7, grip=1.7),
           "source": "Dallara F3 2019: about 690 kg with driver, a 3.4-litre V6 of about 380 hp"},
    "FE": {"label": "Formula E", "colour": "#1fd6a0", "fit": False,
           "car": dict(mass=860, power_kw=340, downforce_scale=0.35, drag_scale=0.75, grip=1.35),
           "source": "Gen3: 350 kW in qualifying, about 860 kg with driver, grooved all-weather tyres"},
    "Indy": {"label": "IndyCar", "colour": "#e8b33a", "fit": False,
             "car": dict(mass=850, power_kw=520, downforce_scale=0.7, drag_scale=1.05, grip=1.75),
             "source": "Dallara IR-18 road-course kit: about 700 hp, about 850 kg with driver and fuel"},
}
# Wikipedia names F2/F3 rounds by place; where it differs from our race's location
PLACE = {"Monte Carlo": "Monte Carlo", "Monaco": "Monte Carlo", "Yas Island": "Yas Island", "Yas Marina": "Yas Island",
         "Spa-Francorchamps": "Spa-Francorchamps", "Spa": "Spa-Francorchamps", "Spielberg": "Spielberg",
         "Montmeló": "Barcelona", "Barcelona": "Barcelona", "Catalunya": "Barcelona", "Lusail": "Lusail"}


def lap_seconds(text):
    m = re.match(r"\s*(?:(\d+):)?(\d+\.\d+)", str(text))
    return (int(m.group(1) or 0) * 60 + float(m.group(2))) if m else None


def pole(series, season, place):
    name = {"F2": "Formula 2", "F3": "Formula 3"}[series]
    html = L.fetch(f"{season} {place} {name} round")
    if not html:
        return None
    for t in L.tables(html):
        cols = L.flat(t.columns)
        if cols and cols[0].startswith("Pos") and any(c.startswith("Time") for c in cols) and "Laps" not in cols:
            tc = next(c for c in cols if c.startswith("Time"))
            t.columns = cols
            first = t[pd.to_numeric(t[cols[0]], errors="coerce") == 1]
            if len(first):
                return lap_seconds(first.iloc[0][tc])
    return None


def car_for(series, folder, cal, grip=None):
    base = lapsim.calibrated_car(folder, cal)
    spec = CARS[series]["car"]
    return replace(base, mass=spec["mass"], power_kw=spec["power_kw"], downforce_scale=spec["downforce_scale"],
                   drag_scale=spec["drag_scale"], grip=grip if grip is not None else spec["grip"])


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    cal = lapsim.load_calibration()
    poles = []
    for folder, c in sorted(cal.items()):
        if not c.get("usable"):
            continue
        info = json.loads((lapsim.RACES_DIR / folder / "info.json").read_text(encoding="utf-8"))
        place = PLACE.get(info.get("location", ""), info.get("location", ""))
        for series in ("F2", "F3"):
            t = pole(series, info["season"], place)
            if t:
                poles.append({"folder": folder, "series": series, "season": info["season"], "place": place,
                              "race_name": info["race_name"], "pole": t})
    poles = pd.DataFrame(poles)
    print(poles.groupby("series").size().to_dict())
    tracks = {f: lapsim.build_track(pd.read_parquet(lapsim.RACES_DIR / f / "track.parquet")) for f in poles["folder"].unique()}

    def sim_lap(series, folder, grip):
        return lapsim.simulate(car_for(series, folder, cal, grip), tracks[folder])["lap_time"]

    def best_grip(rows, series):
        from scipy.optimize import minimize_scalar
        err = lambda g: float(np.mean([(sim_lap(series, r.folder, g) / r.pole - 1) ** 2 for r in rows.itertuples()]))
        return float(minimize_scalar(err, bounds=(1.0, 3.0), method="bounded", options={"xatol": 1e-3}).x)

    # A pole far slower than the dry-weather simulator can explain is almost always a wet session: a first
    # pass finds them (more than WET_GAP slower than predicted), and they are left out of the fit and the check.
    poles["wet"] = False
    for series in ("F2", "F3"):
        rows = poles[poles["series"] == series]
        g = best_grip(rows, series)
        pred = np.array([sim_lap(series, r.folder, g) for r in rows.itertuples()])
        poles.loc[rows.index, "wet"] = (rows["pole"].to_numpy() / pred - 1) > WET_GAP
    print("left out as likely wet:", poles[poles["wet"]][["series", "place", "season"]].values.tolist())

    fitted, checks = {}, []
    for series in ("F2", "F3"):
        rows = poles[(poles["series"] == series) & ~poles["wet"]]
        fitted[series] = best_grip(rows, series)
        places = rows["place"].unique()
        for place in places:                          # leave each circuit out and predict its pole(s)
            g = best_grip(rows[rows["place"] != place], series)
            for r in rows[rows["place"] == place].itertuples():
                checks.append({"series": series, "folder": r.folder, "place": place, "season": r.season,
                               "pole": r.pole, "predicted": round(sim_lap(series, r.folder, g), 3)})
        print(series, "grip", round(fitted[series], 3))
    chk = pd.DataFrame(checks)
    chk["error_pct"] = (chk["predicted"] / chk["pole"] - 1) * 100
    out = {"cars": {k: {**v, "car": {**v["car"], **({"grip": round(fitted[k], 3)} if k in fitted else {})}}
                    for k, v in CARS.items()},
           "check": {s: {"mean_abs_pct": round(float(g["error_pct"].abs().mean()), 2), "circuits": int(g["place"].nunique()),
                         "poles": int(len(g))} for s, g in chk.groupby("series")},
           "poles": chk.round(3).to_dict("records"),
           "wet": poles[poles["wet"]][["series", "folder", "place", "season", "pole"]].to_dict("records"),
           "built": time.strftime("%Y-%m-%d")}
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    for s, v in out["check"].items():
        print(f"{s}: off by {v['mean_abs_pct']}% on average predicting {v['poles']} poles at {v['circuits']} circuits left out")


if __name__ == "__main__":
    main()
