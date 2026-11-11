"""Pit stops and tyre strategy, read from the race files the project already prepares.

Everything here comes from data/races/<season>_<round>/, so it only covers the races
that have been prepared (2023 onwards, because that is where OpenF1's data begins).

The pit time is the stationary time in the box, not the whole lap lost, so the numbers
are the ones teams quote when they talk about a "2.1 second stop".
"""
import json
from pathlib import Path

import pandas as pd

from teaminfo import openf1_team_id

ROOT = Path(__file__).resolve().parent.parent
RACES_DIR = ROOT / "data" / "races"

SLOWEST_REAL_STOP = 10.0    # anything longer was a repair or a penalty served, not a stop


def race_folders(season=None):
    """Every prepared race folder, newest last."""
    out = []
    for folder in sorted(RACES_DIR.glob("*_*")):
        info_file = folder / "info.json"
        if not info_file.exists():
            continue
        info = json.loads(info_file.read_text(encoding="utf-8"))
        if season is None or info.get("season") == season:
            out.append((folder, info))
    return out


def entry_map(info):
    """Car number -> (driver name, team id, team name as OpenF1 writes it)."""
    out = {}
    for entry in info.get("drivers", []):
        out[int(entry["number"])] = (entry.get("name", ""),
                                     openf1_team_id(entry.get("team", "")),
                                     entry.get("team", ""))
    return out


def race_stops(folder, info):
    """Every pit stop in one race, with the team that made it."""
    path = folder / "pits.parquet"
    if not path.exists():
        return pd.DataFrame()
    try:
        pits = pd.read_parquet(path)
    except Exception:                      # a half-written file must not break the page
        return pd.DataFrame()
    if pits.empty or "pit_duration" not in pits.columns:
        return pd.DataFrame()
    entries = entry_map(info)
    pits = pits.copy()
    pits["driver_name"] = pits["driver_number"].map(lambda n: entries.get(int(n), ("", None, ""))[0])
    pits["constructor"] = pits["driver_number"].map(lambda n: entries.get(int(n), ("", None, ""))[1])
    pits["season"] = info["season"]
    pits["round"] = info["round"]
    pits["race_name"] = info["race_name"]
    pits = pits[pits["pit_duration"].notna() & (pits["pit_duration"] <= SLOWEST_REAL_STOP)]
    return pits.dropna(subset=["constructor"])


def season_stops(season):
    """Every pit stop of one season, from the races that have been prepared."""
    frames = [race_stops(folder, info) for folder, info in race_folders(season)]
    frames = [f for f in frames if not f.empty]
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def team_stop_summary(season):
    """Per team: how many stops, the typical time and the quickest of the season."""
    stops = season_stops(season)
    if stops.empty:
        return pd.DataFrame()
    grouped = stops.groupby("constructor")
    table = pd.DataFrame({
        "stops": grouped.size(),
        "median_stop": grouped["pit_duration"].median().round(2),
        "best_stop": grouped["pit_duration"].min().round(2),
        "worst_stop": grouped["pit_duration"].max().round(2),
    })
    return table.sort_values("median_stop").reset_index()


def race_stints(folder, info):
    """Who ran which tyre and for how long, worked out from the lap data."""
    path = folder / "laps.parquet"
    if not path.exists():
        return pd.DataFrame()
    try:
        laps = pd.read_parquet(path)
    except Exception:
        return pd.DataFrame()
    if laps.empty or "compound" not in laps.columns:
        return pd.DataFrame()
    laps = laps.sort_values(["driver_number", "lap_number"]).copy()
    changed = (laps["compound"] != laps.groupby("driver_number")["compound"].shift(1))
    restarted = laps["tyre_age"] < laps.groupby("driver_number")["tyre_age"].shift(1)
    laps["stint"] = (changed | restarted.fillna(False)).groupby(laps["driver_number"]).cumsum()

    entries = entry_map(info)
    grouped = laps.groupby(["driver_number", "stint"], as_index=False).agg(
        compound=("compound", "first"),
        start_lap=("lap_number", "min"),
        end_lap=("lap_number", "max"),
        laps=("lap_number", "size"))
    grouped["driver_name"] = grouped["driver_number"].map(
        lambda n: entries.get(int(n), ("", None, ""))[0])
    grouped["constructor"] = grouped["driver_number"].map(
        lambda n: entries.get(int(n), ("", None, ""))[1])
    return grouped.dropna(subset=["compound"])


def team_compound_use(season):
    """How many laps each team ran on each tyre over a season."""
    rows = []
    for folder, info in race_folders(season):
        stints = race_stints(folder, info)
        if not stints.empty:
            rows.append(stints)
    if not rows:
        return pd.DataFrame()
    all_stints = pd.concat(rows, ignore_index=True)
    return (all_stints.dropna(subset=["constructor"])
            .groupby(["constructor", "compound"], as_index=False)["laps"].sum())
