"""Champions: every drivers' and constructors' title since 1950."""
import altair as alt
import streamlit as st

from app_archive import get_champions, get_title_counts, require_history
from cards import cards_css, note
from charts import dress, name_scale
from style import empty_note, stat_strip

cards_css()
require_history()

table = get_champions()
if table.empty:
    empty_note("No champions found in the history files.")
    st.stop()

drivers = get_title_counts("driver")
teams = get_title_counts("team")
latest = table.iloc[-1]

stat_strip([
    ("Seasons", str(len(table)),
     f'{int(table["season"].min())} to {int(table["season"].max())}', True),
    ("Most titles, driver", drivers.iloc[0]["driver_name"] if not drivers.empty else "—",
     f'{int(drivers.iloc[0]["titles"])} championships' if not drivers.empty else "", False),
    ("Most titles, team", teams.iloc[0]["team_name"] if not teams.empty else "—",
     f'{int(teams.iloc[0]["titles"])} championships' if not teams.empty else "", False),
    ("Latest champion", latest["driver_name"] or "—", str(int(latest["season"])), False),
])

st.subheader("Titles per driver")
top_drivers = drivers.head(20)
chart = (alt.Chart(top_drivers).mark_bar(cornerRadiusEnd=4, color="#e10600")
         .encode(x=alt.X("titles:Q", title="Championships",
                         axis=alt.Axis(tickMinStep=1, format="d")),
                 y=alt.Y("driver_name:N", sort=top_drivers["driver_name"].tolist(), title=None),
                 tooltip=[alt.Tooltip("driver_name:N", title="Driver"),
                          alt.Tooltip("titles:Q", title="Titles"),
                          alt.Tooltip("years:N", title="Years")]))
st.altair_chart(dress(chart).properties(height=max(220, 26 * len(top_drivers))),
                width="stretch", theme=None)

st.subheader("Titles per constructor")
top_teams = teams.head(20)
chart = (alt.Chart(top_teams).mark_bar(cornerRadiusEnd=4)
         .encode(x=alt.X("titles:Q", title="Championships",
                         axis=alt.Axis(tickMinStep=1, format="d")),
                 y=alt.Y("team_name:N", sort=top_teams["team_name"].tolist(), title=None),
                 color=alt.Color("team_name:N", scale=name_scale(top_teams["team_name"].tolist()),
                                 legend=None),
                 tooltip=[alt.Tooltip("team_name:N", title="Team"),
                          alt.Tooltip("titles:Q", title="Titles"),
                          alt.Tooltip("years:N", title="Years")]))
st.altair_chart(dress(chart).properties(height=max(220, 26 * len(top_teams))),
                width="stretch", theme=None)
note("There was no constructors' championship until 1958, so the early seasons have a "
     "drivers' champion only.")

st.subheader("Every season")
show = table.copy()
show["Season"] = show["season"].astype(int)
st.dataframe(
    show[["Season", "driver_name", "driver_team", "driver_wins", "driver_points", "team_name"]]
    .rename(columns={"driver_name": "Drivers' champion", "driver_team": "Driving for",
                     "driver_wins": "Wins", "driver_points": "Points",
                     "team_name": "Constructors' champion"})
    .sort_values("Season", ascending=False),
    hide_index=True, width="stretch")

st.subheader("The full list of champions")
st.dataframe(
    drivers.rename(columns={"driver_name": "Driver", "titles": "Titles", "years": "Years"})
    [["Driver", "Titles", "Years"]],
    hide_index=True, width="stretch")
