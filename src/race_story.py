"""Where the race was won, and what happens on lap one. Built from the prepared race files
(OpenF1 laps, pit stops and race control, 2023 onwards).

WHERE THE RACE WAS WON
For two drivers, the gap at the flag is the sum of what changed on every lap. Each lap's
change goes into one bucket:
  start      lap 1, which includes where each car started on the grid
  pit stops  either driver's in-lap or out-lap (the time a stop costs, including the pit lane,
             any penalty served at the stop, and the saving of stopping under a safety car)
  safety car any other lap run under a safety car, virtual safety car or red flag
  racing     every other lap: pure pace, tyres, traffic and fuel together
The buckets add up exactly to the real gap, because they are built from the real lap times.
Laps are matched by number, so a lapped driver is compared only over the laps they ran.

LAP ONE
Places gained or lost between the grid and the end of lap 1, for every driver in every
prepared race. Grid positions come from the official results (Jolpica); pit-lane starts
count as starting from the back.

Test from the terminal:
  python src/race_story.py 2025 12
"""
import json
import re
import sys
import unicodedata

import numpy as np
import pandas as pd

from predictor import RACES_DIR, RESULTS_CSV
from strategy import neutralised

BUCKETS = ["Start (lap 1)", "Pit stops", "Safety car laps", "Racing laps"]
LAP_ONE_COLUMNS = ["season", "round", "race_name", "location", "driver_number", "code", "name", "team",
                   "colour", "grid", "after_lap1", "gained"]


def load(folder):
    path = RACES_DIR / folder
    laps = pd.read_parquet(path / "laps.parquet")
    pits = pd.read_parquet(path / "pits.parquet")
    control = pd.read_parquet(path / "race_control.parquet")
    control = control.dropna(subset=["t"]) if len(control) else control
    info = json.loads((path / "info.json").read_text())
    return laps, pits, control, info


def drivers(info):
    """number -> {code, name, team, colour}"""
    return {int(d["number"]): d for d in info.get("drivers", [])}


def lap_end_times(laps):
    """Time (s) each driver crossed the line at the end of each lap: a table of drivers x laps."""
    laps = laps.sort_values(["driver_number", "lap_number"]).copy()
    nxt = laps.groupby("driver_number")["t_start"].shift(-1)
    end = laps["t_start"] + laps["lap_duration"]
    laps["end"] = end.fillna(nxt)                           # a missing duration: use the next lap's start
    laps = laps.dropna(subset=["end"])                       # a lap with no finish time wasn't completed
    return laps.pivot_table(index="driver_number", columns="lap_number", values="end", aggfunc="first")


def neutral_laps(laps, control):
    """Lap numbers (of the leader) that were run under a safety car, VSC or red flag."""
    if control.empty:
        return set()
    lead = laps.sort_values("t_start").groupby("lap_number")["t_start"].min()
    out = set()
    nums = list(lead.index)
    for i, lap in enumerate(nums):
        start = lead[lap]
        end = lead[nums[i + 1]] if i + 1 < len(nums) else start + 120
        checks = np.linspace(start, end, 5)
        window = control[(control["t"] >= start) & (control["t"] <= end)]["message"].fillna("").str.upper()
        deployed = window.str.contains("SAFETY CAR DEPLOYED|VSC DEPLOYED|RED FLAG").any()
        if deployed or any(neutralised(control, t) for t in checks):
            out.add(int(lap))
    return out


def pit_laps(laps):
    """{driver: set of lap numbers that were in-laps or out-laps}"""
    out = {}
    for num, d in laps.groupby("driver_number"):
        outs = set(d.loc[d["is_pit_out_lap"].fillna(False).astype(bool), "lap_number"].astype(int))
        out[int(num)] = outs | {lap - 1 for lap in outs if lap > 1}
    return out


def completed_laps(laps):
    """{driver: laps completed with a finish time}"""
    return lap_end_times(laps).notna().sum(axis=1).astype(int).to_dict()


def finishing_order(laps):
    """Drivers in finishing order: most laps first, then who finished those laps first."""
    ends = lap_end_times(laps)
    last = ends.notna().sum(axis=1)
    final = ends.apply(lambda row: row.dropna().iloc[-1] if row.notna().any() else np.inf, axis=1)
    return pd.DataFrame({"laps": last, "end": final}).sort_values(["laps", "end"],
                                                                  ascending=[False, True]).index.tolist()


def breakdown(folder, a, b, data=None):
    """How the gap between drivers a and b (car numbers) built up. Positive = b ahead of a's... see below.

    Every value is "time driver a gained on driver b" in seconds, so positive means a was better.
    Returns (buckets dict, per-lap DataFrame with lap, gap, bucket)."""
    laps, pits, control, info = data or load(folder)
    ends = lap_end_times(laps)
    common = [c for c in ends.columns if pd.notna(ends.at[a, c]) and pd.notna(ends.at[b, c])] \
        if a in ends.index and b in ends.index else []
    if not common:
        return {k: 0.0 for k in BUCKETS}, pd.DataFrame(columns=["lap", "gap", "change", "bucket"])
    gap = (ends.loc[b, common] - ends.loc[a, common]).astype(float)   # > 0: a is ahead by that much
    change = gap.diff()
    change.iloc[0] = gap.iloc[0]
    neutral = neutral_laps(laps, control)
    stops = pit_laps(laps)
    rows = []
    for lap, delta in change.items():
        lap = int(lap)
        if lap == 1:
            bucket = BUCKETS[0]
        elif lap in stops.get(a, set()) or lap in stops.get(b, set()):
            bucket = BUCKETS[1]
        elif lap in neutral:
            bucket = BUCKETS[2]
        else:
            bucket = BUCKETS[3]
        rows.append({"lap": lap, "gap": float(gap[lap]), "change": float(delta), "bucket": bucket})
    per_lap = pd.DataFrame(rows)
    totals = per_lap.groupby("bucket")["change"].sum().reindex(BUCKETS).fillna(0.0).to_dict()
    return totals, per_lap


def field_breakdown(folder, data=None):
    """Every finisher on the lead lap against the winner: time lost in each bucket."""
    data = data or load(folder)
    laps = data[0]
    order = finishing_order(laps)
    winner = order[0]
    done = completed_laps(laps)
    rows = []
    for pos, num in enumerate(order[1:], start=2):
        if done.get(num, 0) < done.get(winner, 0):
            break
        totals, _ = breakdown(folder, winner, num, data)
        rows.append({"position": pos, "driver_number": num, **totals, "total": sum(totals.values())})
    return winner, pd.DataFrame(rows)


# ---------- lap one ----------

def _plain(text):
    text = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z]", "", text)


def grid_for(info, results):
    """car number -> grid slot, by matching OpenF1 names to the official results."""
    race = results[(results["season"] == info["season"]) & (results["round"] == info["round"])]
    if race.empty:
        return {}
    field = len(race)
    out = {}
    for d in info.get("drivers", []):
        surname = _plain(str(d.get("name", "")).split()[-1]) if d.get("name") else ""
        if not surname:
            continue
        hit = race[race["driver"].map(lambda x: _plain(x).endswith(surname))]
        if len(hit) == 1:
            g = int(hit["grid"].iloc[0])
            out[int(d["number"])] = g if g > 0 else field       # 0 = pit-lane start
    return out


def lap_one(folder, results, data=None):
    """One row per driver: grid, position after lap 1, places gained."""
    laps, _, _, info = data or load(folder)
    grid = grid_for(info, results)
    first = laps[laps["lap_number"] == 1].dropna(subset=["position"])
    who = drivers(info)
    rows = []
    for _, r in first.iterrows():
        num = int(r["driver_number"])
        if num not in grid:
            continue
        d = who.get(num, {})
        rows.append({"season": info["season"], "round": info["round"], "race_name": info["race_name"],
                     "location": info.get("location", ""), "driver_number": num, "code": d.get("code", str(num)),
                     "name": d.get("name", ""), "team": d.get("team", ""), "colour": d.get("colour", "#8a8a96"),
                     "grid": grid[num], "after_lap1": int(r["position"]),
                     "gained": grid[num] - int(r["position"])})
    return pd.DataFrame(rows, columns=LAP_ONE_COLUMNS)


def all_lap_ones():
    results = pd.read_csv(RESULTS_CSV)
    frames = []
    for path in sorted(RACES_DIR.glob("*_*")):
        if (path / "laps.parquet").exists() and (path / "info.json").exists():
            one = lap_one(path.name, results)
            if len(one):
                frames.append(one)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=LAP_ONE_COLUMNS)


if __name__ == "__main__":
    folder = f"{int(sys.argv[1])}_{int(sys.argv[2]):02d}" if len(sys.argv) == 3 else "2025_12"
    data = load(folder)
    winner, field = field_breakdown(folder, data)
    who = drivers(data[3])
    print(f"{data[3]['race_name']} {data[3]['season']}: winner {who[winner]['code']}")
    for _, r in field.iterrows():
        parts = ", ".join(f"{k} {-r[k]:+.1f}s" for k in BUCKETS)
        print(f"  P{r['position']} {who[r['driver_number']]['code']}: {-r['total']:+.1f}s  ({parts})")
    l1 = lap_one(folder, pd.read_csv(RESULTS_CSV), data)
    print(l1.sort_values("gained", ascending=False)[["code", "grid", "after_lap1", "gained"]].head(5).to_string())
