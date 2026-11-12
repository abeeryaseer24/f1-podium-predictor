"""What happened in a race beyond the result: the weather, the flags, the stewards'
decisions and who actually made up ground.

Everything is read from the race files the project already prepares in data/races/, so
it covers 2023 onwards, which is where OpenF1's data begins. Nothing here calls the
internet.
"""
import json
import re
from pathlib import Path

import pandas as pd

from teaminfo import openf1_team_id

ROOT = Path(__file__).resolve().parent.parent
RACES_DIR = ROOT / "data" / "races"

CAR_IN_MESSAGE = re.compile(r"\bCARS?\s+(\d+)")
RED_FLAG = re.compile(r"\bRED FLAG\b")          # "CHEQUERED FLAG" also contains "RED FLAG"


def load(folder_name, name):
    """One prepared table, or an empty one if it is missing or unreadable."""
    path = RACES_DIR / folder_name / f"{name}.parquet"
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_parquet(path)
    except Exception:
        return pd.DataFrame()


def race_info(folder_name):
    path = RACES_DIR / folder_name / "info.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def entries(info):
    """Car number -> (driver name, team id, team name)."""
    out = {}
    for entry in info.get("drivers", []):
        out[int(entry["number"])] = (entry.get("name", ""),
                                     openf1_team_id(entry.get("team", "")),
                                     entry.get("team", ""))
    return out


# ---------- weather ----------

def weather(folder_name):
    """Every weather reading of the race, about one a minute."""
    table = load(folder_name, "weather")
    if table.empty:
        return table
    table = table.copy()
    if "t" in table.columns:
        table["minute"] = (table["t"] - table["t"].min()) / 60
    else:
        table["minute"] = range(len(table))
    return table


def weather_summary(folder_name):
    """The headline numbers: how hot, how windy, and whether it rained."""
    table = weather(folder_name)
    if table.empty:
        return {}
    wet = False
    if "rainfall" in table.columns:
        wet = bool(pd.to_numeric(table["rainfall"], errors="coerce").fillna(0).max() > 0)
    out = {"wet": wet, "readings": int(len(table))}
    for column, key in (("air_temperature", "air"), ("track_temperature", "track"),
                        ("humidity", "humidity"), ("wind_speed", "wind")):
        if column in table.columns:
            values = pd.to_numeric(table[column], errors="coerce").dropna()
            if len(values):
                out[key] = {"low": round(float(values.min()), 1),
                            "high": round(float(values.max()), 1),
                            "average": round(float(values.mean()), 1)}
    return out


# ---------- race control: flags, safety cars and the stewards ----------

KINDS = [
    # Order matters: the first match wins, so an outcome beats the words around it.
    ("Disqualified", ("DISQUALIFIED", "EXCLUDED")),
    ("No further action", ("NO FURTHER ACTION", "NO FURTHER INVESTIGATION")),
    ("Penalty given", ("TIME PENALTY", "DRIVE THROUGH", "STOP AND GO", "STOP/GO",
                       "GRID PENALTY", "PENALTY FOR", "SECOND PENALTY", "PLACE PENALTY")),
    ("Reprimand", ("REPRIMAND",)),
    ("Warning or black and white flag", ("BLACK AND WHITE", "WARNING")),
    ("Lap time deleted", ("DELETED",)),
    ("Under investigation", ("UNDER INVESTIGATION", "WILL BE INVESTIGATED", "NOTED")),
    ("Safety car", ("SAFETY CAR",)),
    ("Chequered flag", ("CHEQUERED",)),
    ("DRS", ("DRS ENABLED", "DRS DISABLED")),
    ("Flag or track status", ("GREEN LIGHT", "PIT EXIT", "TRACK CLEAR", "YELLOW",
                              "BLUE FLAG", "PIT ENTRY")),
]


def classify(message):
    """Turn a race control message into one plain-English kind."""
    up = str(message).upper()
    if RED_FLAG.search(up):
        return "Red flag"
    for kind, words in KINDS:
        if kind == "Red flag":
            continue
        if any(word in up for word in words):
            return kind
    return "Other"


def control(folder_name):
    """Every race control message with a plain kind, a lap and the driver it names."""
    table = load(folder_name, "race_control")
    if table.empty or "message" not in table.columns:
        return pd.DataFrame()
    info = race_info(folder_name)
    people = entries(info)

    table = table.copy()
    table["message"] = table["message"].fillna("")
    table["kind"] = table["message"].map(classify)

    def car_number(row):
        number = row.get("driver_number")
        if pd.notna(number) and number:
            try:
                return int(number)
            except (TypeError, ValueError):
                pass
        found = CAR_IN_MESSAGE.search(str(row["message"]).upper())
        return int(found.group(1)) if found else None

    table["car"] = table.apply(car_number, axis=1)
    table["driver_name"] = table["car"].map(lambda n: people.get(n, ("", None, ""))[0]
                                            if n else "")
    table["constructor"] = table["car"].map(lambda n: people.get(n, ("", None, ""))[1]
                                            if n else None)
    table["season"] = info.get("season")
    table["round"] = info.get("round")
    table["race_name"] = info.get("race_name", "")
    if "lap_number" not in table.columns:
        table["lap_number"] = pd.NA
    keep = ["season", "round", "race_name", "lap_number", "kind", "car", "driver_name",
            "constructor", "category", "flag", "scope", "message"]
    return table[[c for c in keep if c in table.columns]]


STEWARD_KINDS = ("Disqualified", "Penalty given", "Reprimand",
                 "Warning or black and white flag", "Lap time deleted",
                 "Under investigation", "No further action")


def penalties(folder_name):
    """Only the stewards' decisions, not flags and safety cars."""
    table = control(folder_name)
    if table.empty:
        return table
    return table[table["kind"].isin(STEWARD_KINDS)].reset_index(drop=True)


def race_folders(season=None):
    """Prepared race folders, oldest first, optionally for one season."""
    out = []
    for folder in sorted(RACES_DIR.glob("*_*")):
        if not (folder / "info.json").exists():
            continue
        info = json.loads((folder / "info.json").read_text(encoding="utf-8"))
        if season is None or info.get("season") == season:
            out.append((folder.name, info))
    return out


def season_penalties(season):
    """Every stewards' decision of one season, from the races that have been prepared."""
    frames = [penalties(name) for name, _ in race_folders(season)]
    frames = [f for f in frames if not f.empty]
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


# ---------- who actually made up ground ----------

def position_flow(folder_name):
    """Every driver's position at the end of every lap."""
    laps = load(folder_name, "laps")
    if laps.empty or "position" not in laps.columns:
        return pd.DataFrame()
    info = race_info(folder_name)
    people = entries(info)
    table = laps[["driver_number", "lap_number", "position"]].dropna().copy()
    table["driver_name"] = table["driver_number"].map(
        lambda n: people.get(int(n), ("", None, ""))[0])
    table["constructor"] = table["driver_number"].map(
        lambda n: people.get(int(n), ("", None, ""))[1])
    table["position"] = table["position"].astype(int)
    table["lap_number"] = table["lap_number"].astype(int)

    # Some laps come back with a position for only a handful of cars, usually around a
    # red flag or a timing glitch. Drawn as they are, every line dives to the front and
    # back out again, which looks like the whole field overtook each other on one lap.
    table = table[table["position"] > 0]
    if table.empty:
        return table
    reported = table.groupby("lap_number")["driver_number"].nunique()
    full = reported.max()
    keep = reported[reported >= max(2, full * 0.6)].index
    return table[table["lap_number"].isin(keep)].reset_index(drop=True)


def places_from_grid(folder_name, results_for_race):
    """Where each driver started on the grid against where they finished.

    The lap data only knows where a car was at the end of the first recorded lap, which
    is after the start itself. The official grid is the real starting position, so a
    first-corner move counts the way everyone watching counted it.
    """
    if results_for_race is None or results_for_race.empty:
        return pd.DataFrame()
    info = race_info(folder_name)
    people = entries(info)
    by_name = {}
    for name, team_id, _ in people.values():
        if name:
            by_name[name.lower()] = team_id

    table = results_for_race.copy()
    table = table[(table["grid"] > 0) & (table["finish_position"] > 0)]
    if table.empty:
        return table
    table["places_gained"] = table["grid"] - table["finish_position"]
    return table.sort_values("places_gained", ascending=False).reset_index(drop=True)


def movers(folder_name):
    """Where each driver was on lap 1 against where they finished."""
    flow = position_flow(folder_name)
    if flow.empty:
        return flow
    first = flow.sort_values("lap_number").groupby("driver_number").first()
    last = flow.sort_values("lap_number").groupby("driver_number").last()
    table = pd.DataFrame({
        "driver_name": last["driver_name"],
        "constructor": last["constructor"],
        "early_position": first["position"],
        "final_position": last["position"],
    }).reset_index()
    table["places_gained"] = table["early_position"] - table["final_position"]
    return table.sort_values("places_gained", ascending=False).reset_index(drop=True)


def lead_changes(folder_name):
    """Every time the car in front changed, lap by lap."""
    flow = position_flow(folder_name)
    if flow.empty:
        return pd.DataFrame()
    leaders = (flow[flow["position"] == 1].sort_values("lap_number")
               [["lap_number", "driver_name", "constructor"]])
    if leaders.empty:
        return pd.DataFrame()
    changed = leaders["driver_name"] != leaders["driver_name"].shift(1)
    return leaders[changed].reset_index(drop=True)


def overtaking_summary(folder_name):
    """How much position-swapping there was: places changed, and how often the lead went."""
    flow = position_flow(folder_name)
    if flow.empty:
        return {}
    flow = flow.sort_values(["driver_number", "lap_number"])
    moved = flow.groupby("driver_number")["position"].diff().abs().fillna(0)
    leaders = lead_changes(folder_name)
    return {
        "places_changed": int(moved.sum()),
        "laps": int(flow["lap_number"].max()),
        "lead_changes": max(0, len(leaders) - 1),
        "leaders": leaders["driver_name"].tolist() if not leaders.empty else [],
    }
