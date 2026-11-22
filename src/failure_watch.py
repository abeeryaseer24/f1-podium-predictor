"""Failure Watch: did a car's lap times show trouble before it retired?

For every driver in every prepared race, each clean racing lap is compared with what that driver should
have done: their own typical pace, corrected for fuel and tyre age with the race's Tyre Lab fit. The gap
is the RESIDUAL. A car with a developing problem (power loss, damage, overheating) often runs a string
of slow laps before it stops.

THE WARNING fires when a driver's residual averages more than THRESHOLD seconds over three clean laps in
a row. It's an anomaly detector: it knows nothing about why.

THE HONEST TEST, over every race:
  caught    retirements that had a warning in the 15 laps before the car stopped
  precision of all warnings, how many were followed by that car retiring within 15 laps
Many retirements are sudden (crashes, collisions, instant failures), so no lap-time detector can see
them coming; and many slow laps are just traffic or a driver saving tyres. Both numbers are shown.
"""
import re
import unicodedata

import numpy as np
import pandas as pd

import race_story as R
import tyres as TY
from predictor import RESULTS_CSV

THRESHOLD = 2.0        # s per lap slower than expected, on average over three clean laps
WINDOW = 3
HORIZON = 15           # laps before a retirement in which a warning counts


def _plain(t):
    return re.sub(r"[^a-z]", "", unicodedata.normalize("NFKD", str(t)).encode("ascii", "ignore").decode().lower())


def statuses(info, results):
    """car number -> official status (Finished, +1 Lap, Engine, Collision...)."""
    race = results[(results["season"] == info["season"]) & (results["round"] == info["round"])]
    out = {}
    for d in info.get("drivers", []):
        surname = _plain(str(d.get("name", "")).split()[-1]) if d.get("name") else ""
        hit = race[race["driver"].map(lambda x: _plain(x).endswith(surname))] if surname else race.iloc[0:0]
        if len(hit) == 1:
            out[int(d["number"])] = str(hit["status"].iloc[0])
    return out


def finished(status):
    return status == "Finished" or status.startswith("+") or status == "Lapped"


def analyse(folder, results=None, threshold=THRESHOLD):
    results = results if results is not None else pd.read_csv(RESULTS_CSV)
    laps, pits, control, info = R.load(folder)
    fit = TY.analyse(folder)
    comps = {c["name"]: c for c in fit["compounds"]}
    fuel = fit["fuel"] or -0.06
    neutral = R.neutral_laps(laps, control)
    stops = R.pit_laps(laps)
    status = statuses(info, results)
    who = R.drivers(info)
    d = laps.dropna(subset=["lap_duration"]).copy()
    d = d[(d["lap_number"] > 1) & ~d["lap_number"].isin(neutral)]
    d = d[[l not in stops.get(int(n), set()) for n, l in zip(d["driver_number"], d["lap_number"])]]
    d["expected_part"] = (fuel * d["lap_number"] + d["compound"].map(lambda c: comps.get(c, {}).get("offset", 0.0))
                          + d["tyre_age"].fillna(0) * d["compound"].map(lambda c: max(comps.get(c, {}).get("wear", 0.05), 0)))
    d["adj"] = d["lap_duration"] - d["expected_part"]
    d["residual"] = d["adj"] - d.groupby("driver_number")["adj"].transform("median")
    d = d[d["residual"] < 30]                                         # ignore laps with a spin or a stop we missed
    rows, drivers = [], []
    last_lap = laps.groupby("driver_number")["lap_number"].max()
    race_laps = int(laps["lap_number"].max())
    for num, g in d.sort_values("lap_number").groupby("driver_number"):
        num = int(num)
        g = g.reset_index(drop=True)
        roll = g["residual"].rolling(WINDOW).mean()
        alerts = g.loc[roll > threshold, "lap_number"].astype(int).tolist()
        st = status.get(num, "Finished" if last_lap.get(num, 0) >= race_laps - 1 else "Retired")
        retired = not finished(st)
        stop = int(last_lap.get(num, race_laps))
        first_alert = next((a for a in alerts if retired and stop - HORIZON <= a <= stop), None)
        drivers.append({"driver_number": num, "code": who.get(num, {}).get("code", str(num)),
                        "name": who.get(num, {}).get("name", ""), "team": who.get(num, {}).get("team", ""),
                        "colour": who.get(num, {}).get("colour") or "#8a8a96", "status": st, "retired": retired,
                        "stop_lap": stop, "alerts": alerts, "warned_lap": first_alert,
                        "warning_laps": (stop - first_alert) if first_alert else None})
        for lap, r, rr in zip(g["lap_number"], g["residual"], roll):
            rows.append({"driver_number": num, "lap": int(lap), "residual": float(r),
                         "rolling": float(rr) if pd.notna(rr) else None})
    return {"info": info, "drivers": pd.DataFrame(drivers), "laps": pd.DataFrame(rows), "race_laps": race_laps}


def evaluate(threshold=THRESHOLD):
    """Over every prepared race: how many retirements were caught, and how often a warning meant trouble."""
    results = pd.read_csv(RESULTS_CSV)
    caught = retirements = alerts = true_alerts = 0
    per = []
    for path in sorted(R.RACES_DIR.glob("*_*")):
        if not (path / "laps.parquet").exists():
            continue
        try:
            a = analyse(path.name, results, threshold)
        except Exception:
            continue
        drv = a["drivers"]
        for _, r in drv.iterrows():
            n_alert_runs = _runs(r["alerts"])
            alerts += n_alert_runs
            if r["retired"]:
                retirements += 1
                caught += r["warned_lap"] is not None and pd.notna(r["warned_lap"])
                true_alerts += sum(1 for a in _run_starts(r["alerts"]) if r["stop_lap"] - HORIZON <= a <= r["stop_lap"])
        per.append(path.name)
    return {"races": len(per), "retirements": retirements, "caught": int(caught), "alerts": alerts,
            "true_alerts": true_alerts}


def _run_starts(alerts):
    out, prev = [], None
    for a in alerts:
        if prev is None or a - prev > 1:
            out.append(a)
        prev = a
    return out


def _runs(alerts):
    return len(_run_starts(alerts))


def tradeoff(thresholds=(0.8, 1.2, 2.0, 3.0, 5.0)):
    rows = []
    for t in thresholds:
        e = evaluate(t)
        rows.append({"threshold": t, "caught": e["caught"] / max(e["retirements"], 1),
                     "precision": e["true_alerts"] / max(e["alerts"], 1), "alerts_per_race": e["alerts"] / max(e["races"], 1),
                     "retirements": e["retirements"]})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    t = tradeoff()
    print(t.round(3).to_string(index=False))
    out = R.RACES_DIR.parent / "processed" / "failure_tradeoff.csv"
    t.to_csv(out, index=False)
