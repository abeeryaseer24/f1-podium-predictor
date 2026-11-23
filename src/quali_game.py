"""Qualifying Game data: every timed lap of real qualifying sessions, split into Q1, Q2 and Q3.

For each prepared race since 2024 this fetches the qualifying session's laps from OpenF1 (two requests a
race) and keeps, per driver: the best lap in each segment and when it was set. The segments are read from
the knockout itself (the pause after which only the cars still in it set laps), with the schedule (Q1 18
minutes, a 7-minute break, Q2 15, an 8-minute break, Q3 12) as a fallback. Sessions that still don't show
a believable number of cars in each segment are skipped.

TRACK EVOLUTION: for every driver, their push laps (within 2% of their best) against the minute they were
set; the median of the drivers' slopes is how much faster the track gets each minute, in seconds.

Saves data/processed/quali_game.json.
  python src/quali_game.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import duel
from prepare_race import get, to_dt

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "processed" / "quali_game.json"
EDGES = (21.5, 44.0)          # minutes from the session start splitting Q1 | Q2 | Q3


def knockout_edges(laps):
    """Where Q1 and Q2 end, read from the knockout itself: Q1 ends at the first pause in running after which
    only 13 to n-4 cars still set laps, Q2 at the first later pause after which ten or fewer do. Falls back
    to the schedule (EDGES) when the session doesn't show it cleanly (a red flag, say)."""
    m = np.sort(laps["min"].to_numpy())
    n = laps["driver_number"].nunique()
    gaps = [(a + b) / 2 for a, b in zip(m, m[1:]) if b - a > 3.0]
    after = lambda g: laps.loc[laps["min"] > g, "driver_number"].nunique()
    e1 = next((g for g in gaps if 13 <= after(g) <= n - 4), None)
    e2 = next((g for g in gaps if e1 is not None and g > e1 + 5 and after(g) <= 10), None)
    if e1 is None or e2 is None:
        return EDGES
    return e1, e2


def build(folder):
    info = duel.race_info(folder)
    key = duel.session_key(folder, "Qualifying")
    sess = get("sessions", {"session_key": key})
    laps = pd.DataFrame(get("laps", {"session_key": key}))
    if laps.empty or not sess:
        return None
    start = to_dt(pd.Series([sess[0]["date_start"]])).iloc[0]
    laps["t"] = to_dt(laps["date_start"])
    laps = laps.dropna(subset=["t", "lap_duration"])
    laps = laps[~laps["is_pit_out_lap"].fillna(False).astype(bool)]
    laps["min"] = (laps["t"] - start).dt.total_seconds() / 60
    e1, e2 = knockout_edges(laps)
    laps["seg"] = np.where(laps["min"] < e1, 1, np.where(laps["min"] < e2, 2, 3))
    who = {int(d["number"]): d for d in info["drivers"]}
    drivers = []
    for num, g in laps.groupby("driver_number"):
        d = who.get(int(num))
        if not d:
            continue
        best = {}
        for seg, gs in g.groupby("seg"):
            b = gs.loc[gs["lap_duration"].idxmin()]
            best[int(seg)] = {"time": round(float(b["lap_duration"]), 3), "min": round(float(b["min"]), 1)}
        drivers.append({"code": d["code"], "name": d["name"].title(), "team": d["team"], "colour": d.get("colour") or "#8a8a96",
                        "best": best})
    counts = [sum(str(s) in map(str, x["best"]) or s in x["best"] for x in drivers) for s in (1, 2, 3)]
    n = len(drivers)
    if not (counts[1] >= 13 and 8 <= counts[2] <= 10 and counts[0] >= n - 1):
        print(f"  {folder}: segments look wrong {counts}, skipped")
        return None
    # track evolution: each driver's push laps against time
    slopes = []
    for num, g in laps.groupby("driver_number"):
        push = g[g["lap_duration"] <= g["lap_duration"].min() * 1.02]
        if len(push) >= 3 and push["min"].max() - push["min"].min() > 10:
            slopes.append(np.polyfit(push["min"], push["lap_duration"], 1)[0])
    return {"folder": folder, "race_name": info["race_name"], "season": info["season"], "round": info["round"],
            "evolution": round(float(np.median(slopes)), 4) if slopes else -0.02,
            "q2": counts[1], "q3": counts[2], "drivers": drivers}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    done = {}
    if OUT.exists():
        done = {r["folder"]: r for r in json.loads(OUT.read_text(encoding="utf-8"))}
    folders = sorted(p.name for p in duel.RACES_DIR.glob("*_*") if (p / "info.json").exists() and p.name >= "2024")
    for f in folders:
        if f in done:
            continue
        try:
            r = build(f)
            if r:
                done[f] = r
                print(f"{f}: {len(r['drivers'])} drivers, evolution {r['evolution']:+.3f} s/min", flush=True)
        except Exception as error:
            print(f"{f}: failed ({error})", flush=True)
        OUT.write_text(json.dumps(sorted(done.values(), key=lambda r: r["folder"]), ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
