"""Penalties Log: every stewards' decision of a season, pulled out of the race control
messages."""
import altair as alt
import streamlit as st

from app_garage import default_season, get_seasons
from app_insights import get_prepared_races, get_season_penalties
from cards import cards_css, note
from charts import dress, team_scale
from insights import STEWARD_KINDS
from style import empty_note, stat_strip, team_info

cards_css()

seasons = get_seasons()
season = st.selectbox("Season", seasons, index=seasons.index(default_season()))
races = get_prepared_races(season)
log = get_season_penalties(season)

if log.empty:
    empty_note(f"No stewards' decisions found for {season}.")
    note("This page reads the race control messages in the prepared race files under "
         "<code>data/races/</code>, which start in 2023. If the season is recent, the "
         "robot may not have prepared its races yet.")
    st.stop()

given = log[log["kind"].isin(("Penalty given", "Disqualified"))]
investigated = log[log["kind"] == "Under investigation"]
deleted = log[log["kind"] == "Lap time deleted"]

stat_strip([
    ("Penalties given", str(len(given)), f'across {log["round"].nunique()} races', True),
    ("Incidents investigated", str(len(investigated)),
     "not all of them led to a penalty", False),
    ("Lap times deleted", str(len(deleted)), "mostly track limits", False),
    ("Races covered", f'{log["round"].nunique()} of {len(races)}',
     "races with files prepared", False),
])

note("These come from what race control actually broadcast during each race, so they "
     "cover in-race decisions. Penalties handed out after the chequered flag, and grid "
     "penalties announced on a Saturday, often do not appear in the race messages.")

# ---------- by driver ----------

named = log[log["driver_name"].astype(str) != ""]
if not named.empty:
    st.subheader("Who the stewards spoke to most")
    counts = (named[named["kind"].isin(STEWARD_KINDS)]
              .groupby(["driver_name", "constructor"], as_index=False).size()
              .rename(columns={"size": "decisions"})
              .sort_values("decisions", ascending=False))
    data = counts.dropna(subset=["constructor"]).copy()
    if not data.empty:
        data["Team"] = data["constructor"].map(lambda t: team_info(t)[0])
        chart = (alt.Chart(data).mark_bar(cornerRadiusEnd=4)
                 .encode(x=alt.X("decisions:Q", title="Stewards' decisions",
                                 axis=alt.Axis(tickMinStep=1, format="d")),
                         y=alt.Y("driver_name:N", sort=data["driver_name"].tolist(),
                                 title=None),
                         color=alt.Color("Team:N",
                                         scale=team_scale(sorted(data["constructor"].unique())),
                                         legend=None),
                         tooltip=[alt.Tooltip("driver_name:N", title="Driver"), "Team",
                                  alt.Tooltip("decisions:Q", title="Decisions")]))
        st.altair_chart(dress(chart).properties(height=max(240, 26 * len(data))),
                        width="stretch", theme=None)
        note("A driver high on this list is not necessarily a dirty racer: an incident "
             "they were the victim of is logged against both cars.")

# ---------- by kind ----------

st.subheader("What kind of decision")
kinds = (log.groupby("kind", as_index=False).size()
         .rename(columns={"size": "count"}).sort_values("count", ascending=False))
chart = (alt.Chart(kinds).mark_bar(cornerRadiusEnd=4, color="#e10600")
         .encode(x=alt.X("count:Q", title="Messages",
                         axis=alt.Axis(tickMinStep=1, format="d")),
                 y=alt.Y("kind:N", sort=kinds["kind"].tolist(), title=None),
                 tooltip=["kind", "count"]))
st.altair_chart(dress(chart).properties(height=max(180, 30 * len(kinds))),
                width="stretch", theme=None)

# ---------- by race ----------

st.subheader("Which races the stewards were busiest at")
per_race = (log.groupby(["round", "race_name"], as_index=False).size()
            .rename(columns={"size": "decisions"}).sort_values("round"))
chart = (alt.Chart(per_race).mark_bar(cornerRadiusEnd=4, color="#e10600")
         .encode(x=alt.X("round:O", title="Round"),
                 y=alt.Y("decisions:Q", title="Decisions",
                         axis=alt.Axis(tickMinStep=1, format="d")),
                 tooltip=[alt.Tooltip("race_name:N", title="Race"),
                          alt.Tooltip("decisions:Q", title="Decisions")]))
st.altair_chart(dress(chart).properties(height=300), width="stretch", theme=None)

# ---------- the log itself ----------

st.subheader("The log")
kind_filter = st.multiselect("Show", list(STEWARD_KINDS), default=list(STEWARD_KINDS))
shown = log[log["kind"].isin(kind_filter)] if kind_filter else log
st.dataframe(
    shown[["round", "race_name", "lap_number", "kind", "driver_name", "message"]]
    .rename(columns={"round": "Round", "race_name": "Race", "lap_number": "Lap",
                     "kind": "Kind", "driver_name": "Driver", "message": "What was said"})
    .sort_values(["Round", "Lap"]),
    hide_index=True, width="stretch")
