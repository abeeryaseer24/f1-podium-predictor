"""Great Seasons: the closest title fights, the most one-sided years, and the
championships that went down to the final race."""
import altair as alt
import streamlit as st

from app_archive import (get_last_race_deciders, get_season_progress, get_seasons,
                         get_title_fights, require_history)
from cards import cards_css, note
from charts import dress
from style import empty_note, stat_strip
from ui_kit import GOLD, SILVER, kit_css, league, section

cards_css()
kit_css()
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
    ("Decided at the last race", str(len(deciders)),
     "the leader could still have been caught", False),
])

section("The twenty closest championships",
        "Points between the champion and the runner-up when the season ended. The shorter the bar, the tighter the year.")
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

section("The same twenty, with who they beat",
        "The bar is how close it was: a full bar is the tightest championship there "
        "has ever been.")
widest_gap = max(float(close["gap"].max()), 0.5)
league([{
    "pos": int(r.season), "name": r.champion, "colour": GOLD,
    "sub": f"beat {r.runner_up} · {r.champion_team}",
    "bar": 1 - (float(r.gap) / widest_gap),
    "figures": [(f"{r.gap:g}", "apart"),
                (f"{r.points_first:g}", "champion"),
                (f"{r.points_second:g}", "runner-up"),
                (f"{int(r.wins_first)}-{int(r.wins_second)}", "wins")],
} for r in close.itertuples()], wide_position=True)

# ---------- one season in detail ----------

section("Follow one season",
        "Pick a year and watch the title race build up round by round.")
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

section("Decided at the last race",
        "Seasons where the leader's advantage going into the final round was smaller "
        "than the points still on offer, so the title could genuinely still have "
        "changed hands that afternoon.")
if deciders.empty:
    empty_note("None found.")
else:
    rows = []
    for r in deciders.itertuples():
        held_on = r.champion == r.leader_before
        rows.append({
            "pos": int(r.season),
            "name": f"{r.leader_before} led, {r.chaser} chased",
            "sub": (f"{r.champion} won it · " +
                    ("the leader held on" if held_on else "the lead changed hands")),
            "colour": GOLD if held_on else SILVER,
            "bar": 1 - min(1.0, float(r.gap_before_final) / max(float(r.most_on_offer), 1)),
            "figures": [(f"{r.gap_before_final:g}", "ahead"),
                        (f"{r.most_on_offer:g}", "on offer")],
        })
    league(rows, wide_position=True)
    note("The bar is how exposed the leader was: a full bar means the gap was almost "
         "nothing next to what was still to be won.")
