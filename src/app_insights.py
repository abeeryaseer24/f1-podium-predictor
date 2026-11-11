"""Cached helpers for Race Insights and the Penalties Log.

Everything comes from the prepared race files in data/races/, so it covers 2023 onwards.
"""
import streamlit as st

import insights


@st.cache_data(ttl=600)
def get_prepared_races(season):
    """[(round, race name, folder name), ...] for one season, oldest first."""
    return [(info["round"], info["race_name"], name)
            for name, info in insights.race_folders(season)]


@st.cache_data(ttl=600)
def get_weather(folder_name):
    return insights.weather(folder_name)


@st.cache_data(ttl=600)
def get_weather_summary(folder_name):
    return insights.weather_summary(folder_name)


@st.cache_data(ttl=600)
def get_control(folder_name):
    return insights.control(folder_name)


@st.cache_data(ttl=600)
def get_penalties(folder_name):
    return insights.penalties(folder_name)


@st.cache_data(ttl=600)
def get_season_penalties(season):
    return insights.season_penalties(season)


@st.cache_data(ttl=600)
def get_position_flow(folder_name):
    return insights.position_flow(folder_name)


@st.cache_data(ttl=600)
def get_movers(folder_name):
    return insights.movers(folder_name)


@st.cache_data(ttl=600)
def get_overtaking(folder_name):
    return insights.overtaking_summary(folder_name)
