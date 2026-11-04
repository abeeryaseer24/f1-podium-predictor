"""Cached data helpers shared by every page, so slow work isn't repeated on every click.
ttl = how many seconds a result is kept before it's loaded fresh."""
import json

import pandas as pd
import streamlit as st

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