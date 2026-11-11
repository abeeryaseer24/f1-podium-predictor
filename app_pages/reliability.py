"""Reliability: how often each team's cars reached the finish, and what stopped the
ones that did not."""
import streamlit as st

from app_garage import default_season, get_reliability, get_seasons
from cards import cards_css, note
from charts import cause_bars, simple_bars
from style import empty_note, stat_strip, team_info

cards_css()

seasons = get_seasons()
season = st.selectbox("Season", seasons, index=seasons.index(default_season()))
summary, causes = get_reliability(season)

if summary.empty:
    empty_note(f"No results for {season} yet.")
    st.stop()

best = summary.iloc[0]
worst = summary.iloc[-1]
total_dnfs = int(summary["dnfs"].sum())
total_entries = int(summary["entries"].sum())

stat_strip([
    ("Most reliable", team_info(best["constructor"])[0],
     f'{best["finish_rate"]:.0f}% of cars finished', True),
    ("Least reliable", team_info(worst["constructor"])[0],
     f'{worst["finish_rate"]:.0f}% of cars finished', False),
    ("Cars that stopped", str(total_dnfs),
     f"out of {total_entries} starts", False),
])

note("A car counts as finishing if it was classified at the end, including cars a lap or "
     "more down. Everything else, from an engine letting go to a first-lap crash, counts "
     "as not finishing. A crash is not the team's fault in the way a failure is, which is "
     "why the reasons are split out below.")

st.subheader("How many cars reached the finish")
st.altair_chart(simple_bars(summary, "finish_rate", "Per cent of cars classified"),
                width="stretch", theme=None)

if not causes.empty:
    st.subheader("Why the others stopped")
    note("The API writes the reason in many different words. They are grouped here into "
         "a handful of plain ones, so 'Power Unit', 'Engine' and 'Turbo' all land together.")
    st.altair_chart(cause_bars(causes), width="stretch", theme=None)

    st.subheader("The reasons in full")
    show = causes.copy()
    show["Team"] = show["constructor"].map(lambda t: team_info(t)[0])
    st.dataframe(
        show.pivot_table(index="Team", columns="cause", values="count",
                         fill_value=0, aggfunc="sum"),
        width="stretch")

st.subheader("The whole table")
table = summary.copy()
table["Team"] = table["constructor"].map(lambda t: team_info(t)[0])
st.dataframe(
    table[["Team", "entries", "finishes", "dnfs", "finish_rate"]]
    .rename(columns={"entries": "Starts", "finishes": "Classified",
                     "dnfs": "Did not finish", "finish_rate": "Finish rate %"}),
    hide_index=True, width="stretch")
