"""Cached helpers for the History pages.

Everything is read from the files src/history_loader.py writes. If they are not there yet,
`require_history()` prints a short instruction and stops the page.
"""
import streamlit as st

import archive
from cards import note
from style import empty_note


def require_history():
    """Stop the page politely if the history has not been downloaded yet."""
    if archive.available():
        return
    empty_note("The history files have not been downloaded yet.")
    note("Run this once, with the virtual environment active:<br>"
         "<code>python src/history_loader.py</code><br>"
         "It fetches every race since 1950 from the same free API the rest of the app uses. "
         "It takes a few minutes and can be stopped and restarted: run it again and it "
         "carries on from where it got to.")
    st.stop()


@st.cache_data(ttl=3600)
def get_results():
    return archive.results()


@st.cache_data(ttl=3600)
def get_seasons():
    return archive.seasons()


@st.cache_data(ttl=3600)
def get_champions():
    return archive.champions()


@st.cache_data(ttl=3600)
def get_title_counts(kind):
    return archive.title_counts(kind)


@st.cache_data(ttl=3600)
def get_wins_by_decade(top=12):
    return archive.wins_by_decade(top)


@st.cache_data(ttl=3600)
def get_wins_by_season(top=12):
    return archive.wins_by_season(top)


@st.cache_data(ttl=3600)
def get_season_shape():
    return archive.season_shape()


@st.cache_data(ttl=3600)
def get_driver_records(metric, active_only, top):
    return archive.driver_records(metric, active_only, top)


@st.cache_data(ttl=3600)
def get_team_records(metric, active_only, top):
    return archive.team_records(metric, active_only, top)


@st.cache_data(ttl=3600)
def get_title_fights():
    return archive.title_fights()


@st.cache_data(ttl=3600)
def get_last_race_deciders():
    return archive.decided_in_the_last_race()


@st.cache_data(ttl=3600)
def get_season_progress(season, top=6):
    return archive.season_points_progress(season, top)


@st.cache_data(ttl=3600)
def get_driver_index():
    return archive.driver_index()


@st.cache_data(ttl=3600)
def get_driver_career(driver_id):
    return archive.driver_career(driver_id)


@st.cache_data(ttl=3600)
def get_driver_seasons(driver_id):
    return archive.driver_seasons(driver_id)


@st.cache_data(ttl=3600)
def get_circuit_index():
    return archive.circuit_index()


@st.cache_data(ttl=3600)
def get_circuit_winners(circuit_id):
    return archive.circuit_winners(circuit_id)


@st.cache_data(ttl=3600)
def get_circuit_history(circuit_id):
    return archive.circuit_history(circuit_id)


@st.cache_data(ttl=3600)
def get_on_this_day(month, day):
    return archive.on_this_day(month, day)


@st.cache_data(ttl=3600)
def get_head_to_head(driver_a, driver_b):
    return archive.head_to_head(driver_a, driver_b)
