"""Great Seasons: the closest title fights, the most one-sided years, and the
championships that went down to the final race."""
import altair as alt
import streamlit as st

from app_archive import (get_last_race_deciders, get_season_progress, get_seasons,
                         get_title_fights, require_history)
from cards import cards_css, note
from charts import dress
from style import empty_note, stat_strip

cards_css()
require_history()

fights = get_title_fights()
deciders = get_last_race_deciders()
seasons = get_seasons()

if fights.empty:
    empty_note("No seasons found in the history files.")
    st.stop()

closest = fights.iloc[0]
widest = fights.iloc[-1]

stat_strip([
    ("Closest title", str(int(closest["season"])),
     f'{closest["champion"]} by {closest["gap"]:g} point'
     f'{"s" if closest["gap"] != 1 else ""}', True),
    ("Most one-sided", str(int(widest["season"])),
     f'{widest["champion"]} by {widest["gap"]:g} points', False),
    ("Went to the last race", str(len(deciders)), "seasons still open", False),
])

st.subheader("The twenty closest championships")
close = fights.head(20).copy()
close["Season"] = close["season"].astype(int).astype(str)
chart = (alt.Chart(close).mark_bar(cornerRadiusEnd=4, color="#e10600")
         .encode(x=alt.X("gap:Q", title="Points between first and second"),
                 y=alt.Y("Season:N", sort=close["Season"].tolist(), title=None),
                 tooltip=["Season", alt.Tooltip("champion:N", title="Champion"),
                          alt.Tooltip("runner_up:N", title="Runner-up"),
                          alt.Tooltip("gap:Q", title="Points apart")]))
st.altair_chart(dress(chart).properties(height=max(260, 26 * len(close))),
                width="stretch", theme=None)
note("Points are not comparable across the years, so a two-point gap in 1958 was a much "
     "bigger deal than a two-point gap today. Treat this as a list of tight finishes, not "
     "a ranking.")

st.dataframe(
    close[["Season", "champion", "champion_team", "runner_up", "points_first",
           "points_second", "gap", "wins_first", "wins_second"]]
    .rename(columns={"champion": "Champion", "champion_team": "Team",
                     "runner_up": "Runner-up", "points_first": "Champion points",
                     "points_second": "Runner-up points", "gap": "Apart",
                     "wins_first": "Champion wins", "wins_second": "Runner-up wins"}),
    hide_index=True, width="stretch")

# ---------- one season in detail ----------

st.subheader("Follow one season")
pick = st.selectbox("Season", list(reversed(seasons)))
progress, names = get_season_progress(int(pick))

if progress.empty:
    empty_note(f"No race data for {pick}.")
else:
    note("Points added up race by race for the six drivers who scored the most. "
         "Before 1991 only a driver's best few results counted towards the title, so for "
         "those years this line is the raw total and will not always match the official "
         "table of the time.")
    chart = (alt.Chart(progress).mark_line(strokeWidth=3, interpolate="monotone", point=True)
             .encode(x=alt.X("round:Q", title="Round",
                             axis=alt.Axis(tickMinStep=1, format="d")),
                     y=alt.Y("cum_points:Q", title="Points"),
                     color=alt.Color("driver_name:N", title=None),
                     tooltip=[alt.Tooltip("driver_name:N", title="Driver"),
                              alt.Tooltip("race_name:N", title="Race"),
                              alt.Tooltip("cum_points:Q", title="Running total"),
                              alt.Tooltip("points:Q", title="That race")]))
    st.altair_chart(dress(chart), width="stretch", theme=None)

# ---------- final race deciders ----------

st.subheader("Still open going into the final race")
if deciders.empty:
    empty_note("None found.")
else:
    note("Seasons where the leader's advantage before the last round was smaller than the "
         "points still on offer, so the championship could still have changed hands.")
    st.dataframe(
        deciders.rename(columns={"season": "Season", "leader_before": "Led going in",
                                 "chaser": "Chasing", "gap_before_final": "Points ahead",
                                 "most_on_offer": "Most still available",
                                 "champion": "Won it"}),
        hide_index=True, width="stretch")
