"""Cached data helpers shared by every page, so slow work isn't repeated on every click.
ttl = how many seconds a result is kept before it's loaded fresh."""
import json

import pandas as pd
import streamlit as st

from duel import fastest_laps, run_duel, session_key
from tyres import analyse as analyse_tyres
from replay import build_replay

from predictor import (RACES_DIR, model_info, past_races, predict_past, predict_upcoming,
                       scoreboard, upcoming_races)


@st.cache_data(ttl=600)
def get_past_races():
    return past_races()


@st.cache_data(ttl=3600)
def get_upcoming(season):
    return upcoming_races(season)


@st.cache_data(ttl=600)
def run_past(season, rnd):
    return predict_past(season, rnd)


@st.cache_data(ttl=3600)
def run_upcoming(season, rnd):
    return predict_upcoming(season, rnd)


@st.cache_data(ttl=600)
def get_scoreboard(kind):
    return scoreboard(kind)


@st.cache_data(ttl=600)
def get_model_info():
    return model_info()


# ---------- prepared race files (for the 3D pages) ----------

@st.cache_data(ttl=600)
def get_prepared_races():
    """Every race that has a complete folder: season, round, race_name, folder."""
    rows = []
    for folder in sorted(RACES_DIR.glob("*_*")):
        info_file = folder / "info.json"
        if info_file.exists():
            info = json.loads(info_file.read_text())
            rows.append({"season": info["season"], "round": info["round"],
                         "race_name": info["race_name"], "folder": folder.name})
    return pd.DataFrame(rows)


@st.cache_data(ttl=600)
def get_race_file(folder, name):
    """One prepared table, e.g. get_race_file("2026_19", "track")."""
    return pd.read_parquet(RACES_DIR / folder / f"{name}.parquet")


@st.cache_data(ttl=600)
def get_race_info(folder):
    return json.loads((RACES_DIR / folder / "info.json").read_text())

@st.cache_data(ttl=600)
def get_corners(folder):
    """Corner labels for a race, or [] if they haven't been made yet."""
    path = RACES_DIR / folder / "corners.json"
    return json.loads(path.read_text()) if path.exists() else []

# ---------- Ghost Lap Duel (live from OpenF1, kept for a day) ----------

@st.cache_data(ttl=86400)
def get_fastest_laps(folder, session_name):
    return fastest_laps(session_key(folder, session_name))


@st.cache_data(ttl=86400)
def get_duel(folder, session_name, num_a, num_b):
    return run_duel(folder, session_name, num_a, num_b)

# ---------- Tyre Lab ----------

@st.cache_data(ttl=600)
def get_tyres(folder):
    return analyse_tyres(folder)

# ---------- Pit Wall ----------

@st.cache_data(ttl=600)
def get_replay(folder):
    return build_replay(folder)