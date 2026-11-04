"""Cached data helpers shared by every page, so slow work isn't repeated on every click.
ttl = how many seconds a result is kept before it's loaded fresh."""
import streamlit as st

from predictor import (model_info, past_races, predict_past, predict_upcoming,
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