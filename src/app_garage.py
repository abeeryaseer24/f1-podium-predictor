"""Cached helpers for the Teams and Drivers pages.

These sit next to app_data.py and work the same way: every slow job is wrapped in a
cache so a page can be redrawn without doing the work again. ttl is how many seconds a
result is kept.
"""
from pathlib import Path

import pandas as pd
import streamlit as st

import standings
from pace import driver_pace_table, smooth, team_pace
from pitstops import race_folders, race_stints, race_stops, team_compound_use, team_stop_summary
from predictor import current_season

ROOT = Path(__file__).resolve().parent.parent
POWER_UNITS_CSV = ROOT / "data" / "power_units.csv"
UPGRADES_CSV = ROOT / "data" / "upgrades.csv"

# How many of each power unit part a driver may use in a season before a grid penalty.
# 2026 rules; the first part over the limit costs 10 places, each one after that 5.
PU_ALLOWANCE = {
    "ICE": 4,
    "Turbocharger": 4,
    "Exhaust": 4,
    "MGU-K": 3,
    "Energy Store": 3,
    "Control Electronics": 3,
    "Ancillaries": 6,
}


@st.cache_data(ttl=600)
def get_seasons():
    """Every season we have results for, newest first."""
    results = pd.read_csv(standings.RESULTS_CSV, usecols=["season"])
    return sorted(results["season"].unique().tolist(), reverse=True)


def default_season():
    """The season to show first: this year if it has raced, otherwise the last one."""
    seasons = get_seasons()
    now = current_season()
    return now if now in seasons else (seasons[0] if seasons else now)


# ---------- championship tables ----------

@st.cache_data(ttl=600)
def get_constructor_table(season):
    return standings.constructor_table(season)


@st.cache_data(ttl=600)
def get_constructor_progress(season):
    return standings.constructor_progress(season)


@st.cache_data(ttl=600)
def get_driver_table(season):
    return standings.driver_table(season)


@st.cache_data(ttl=600)
def get_driver_progress(season):
    return standings.driver_progress(season)


@st.cache_data(ttl=600)
def get_entries(season):
    return standings.current_entries(season)


def sprint_points_included():
    return standings.has_sprint_data()


# ---------- reliability and head to head ----------

@st.cache_data(ttl=600)
def get_reliability(season):
    return standings.reliability(season)


@st.cache_data(ttl=600)
def get_teammate_battles(season):
    return standings.teammate_battles(season)


@st.cache_data(ttl=600)
def get_driver_teammates(driver_id):
    return standings.driver_teammate_record(driver_id)


# ---------- one team or one driver ----------

@st.cache_data(ttl=600)
def get_team_history(team_id, family_ids):
    return standings.team_history(team_id, list(family_ids))


@st.cache_data(ttl=600)
def get_team_drivers(family_ids):
    return standings.team_drivers(list(family_ids))


@st.cache_data(ttl=600)
def get_driver_history(driver_id):
    return standings.driver_history(driver_id)


@st.cache_data(ttl=600)
def get_driver_totals(driver_id):
    return standings.driver_totals(driver_id)


@st.cache_data(ttl=600)
def get_driver_races(driver_id):
    """Every race this driver has started, in our data: grid, finish, points and status."""
    table = standings.points_table()
    return table[table["driver"] == driver_id].sort_values(["season", "round"])


# ---------- pace ----------

@st.cache_data(ttl=600)
def get_team_pace(season, dry_only):
    table = team_pace(dry_only)
    if table.empty:
        return table
    return smooth(table[table["season"] == season], "constructor")


@st.cache_data(ttl=600)
def get_driver_pace(season, dry_only):
    table = driver_pace_table(dry_only)
    if table.empty:
        return table
    table = table[table["season"] == season].dropna(subset=["driver"])
    return smooth(table, "driver")


def pace_available():
    return not team_pace().empty


# ---------- pit stops ----------

@st.cache_data(ttl=600)
def get_team_stops(season):
    return team_stop_summary(season)


@st.cache_data(ttl=600)
def get_compound_use(season):
    return team_compound_use(season)


@st.cache_data(ttl=600)
def get_prepared_rounds(season):
    """The rounds of a season that have race files, as [(round, race name, folder), ...]."""
    return [(info["round"], info["race_name"], folder.name)
            for folder, info in race_folders(season)]


@st.cache_data(ttl=600)
def get_race_stops(folder_name):
    from pitstops import RACES_DIR
    import json
    folder = RACES_DIR / folder_name
    info = json.loads((folder / "info.json").read_text(encoding="utf-8"))
    return race_stops(folder, info)


@st.cache_data(ttl=600)
def get_race_stints(folder_name):
    from pitstops import RACES_DIR
    import json
    folder = RACES_DIR / folder_name
    info = json.loads((folder / "info.json").read_text(encoding="utf-8"))
    return race_stints(folder, info)


# ---------- the two files kept by hand ----------

@st.cache_data(ttl=60)
def get_power_units():
    """Every power unit part change logged by hand in data/power_units.csv.
    One row per new part fitted; the part the car started the season with is not logged."""
    columns = ["season", "round", "driver", "constructor", "component", "note"]
    if not POWER_UNITS_CSV.exists():
        return pd.DataFrame(columns=columns)
    table = pd.read_csv(POWER_UNITS_CSV)
    for col in columns:
        if col not in table.columns:
            table[col] = ""
    return table[columns]


@st.cache_data(ttl=60)
def get_upgrades():
    """Upgrade notes kept by hand in data/upgrades.csv."""
    columns = ["season", "round", "constructor", "area", "description", "source"]
    if not UPGRADES_CSV.exists():
        return pd.DataFrame(columns=columns)
    table = pd.read_csv(UPGRADES_CSV)
    for col in columns:
        if col not in table.columns:
            table[col] = ""
    return table[columns]


def power_unit_counts(season):
    """Per driver and part: how many used, how many are left, and the grid penalty
    they would take for the next one."""
    log = get_power_units()
    log = log[log["season"] == season] if not log.empty else log
    entries = get_entries(season)
    rows = []
    for entry in entries.itertuples():
        for component, allowance in PU_ALLOWANCE.items():
            changes = 0 if log.empty else int(
                ((log["driver"] == entry.driver) & (log["component"] == component)).sum())
            used = 1 + changes
            over = max(0, used - allowance)
            rows.append({
                "driver": entry.driver,
                "constructor": entry.constructor,
                "component": component,
                "used": used,
                "allowance": allowance,
                "left": max(0, allowance - used),
                "over": over,
                "next_penalty": 0 if used < allowance else (10 if over == 0 else 5),
            })
    return pd.DataFrame(rows)
