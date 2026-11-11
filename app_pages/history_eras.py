"""Eras: which teams owned which decade, and how the sport itself has changed."""
import altair as alt
import streamlit as st

from app_archive import get_season_shape, get_wins_by_decade, get_wins_by_season, require_history
from cards import cards_css, note
from charts import dress, name_scale
from style import empty_note, stat_strip

cards_css()
require_history()

decades = get_wins_by_decade()
by_season = get_wins_by_season()
shape = get_season_shape()

if decades.empty:
    empty_note("No wins found in the history files.")
    st.stop()

best_decade = decades.sort_values("wins", ascending=False).iloc[0]
stat_strip([
    ("Most dominant decade", best_decade["team"],
     f'{int(best_decade["wins"])} wins in the {int(best_decade["decade"])}s', True),
    ("Seasons covered", str(len(shape)),
     f'{int(shape["season"].min())} to {int(shape["season"].max())}', False),
    ("Races in the archive", str(int(shape["races"].sum())), "Grands Prix", False),
])

order = (decades.groupby("team")["wins"].sum().sort_values(ascending=False).index.tolist())

st.subheader("Share of wins, decade by decade")
note("Each bar is one decade, split by the teams that won in it. Watch Ferrari hold on "
     "through every era while the others rise and fall around them.")
note("Until the 1980s the records name a car by its chassis and its engine, so Colin "
     "Chapman's Lotus appears as Lotus-Climax, Lotus-BRM and Lotus-Ford. These charts "
     "group those together by chassis, which is the team. Smaller winners are gathered "
     "into <b>Everyone else</b> so the colours stay readable.")
chart = (alt.Chart(decades).mark_bar()
         .encode(x=alt.X("decade:O", title=None),
                 y=alt.Y("wins:Q", title="Share of wins", stack="normalize"),
                 color=alt.Color("team:N", scale=name_scale(order), title=None,
                                 sort=order),
                 order=alt.Order("team:N"),
                 tooltip=[alt.Tooltip("team:N", title="Team"),
                          alt.Tooltip("decade:O", title="Decade"),
                          alt.Tooltip("wins:Q", title="Wins")]))
st.altair_chart(dress(chart).properties(height=380), width="stretch", theme=None)

st.subheader("Wins per decade, as plain numbers")
chart = (alt.Chart(decades).mark_bar()
         .encode(x=alt.X("decade:O", title=None),
                 y=alt.Y("wins:Q", title="Race wins"),
                 color=alt.Color("team:N", scale=name_scale(order), title=None, sort=order),
                 tooltip=[alt.Tooltip("team:N", title="Team"),
                          alt.Tooltip("decade:O", title="Decade"),
                          alt.Tooltip("wins:Q", title="Wins")]))
st.altair_chart(dress(chart).properties(height=340), width="stretch", theme=None)

st.subheader("Season by season")
note("The same thing year by year, which shows how long each winning streak really lasted.")
chart = (alt.Chart(by_season).mark_area(interpolate="monotone")
         .encode(x=alt.X("season:Q", title=None, axis=alt.Axis(format="d")),
                 y=alt.Y("wins:Q", title="Wins that season", stack="normalize"),
                 color=alt.Color("team:N", scale=name_scale(order), title=None, sort=order),
                 tooltip=[alt.Tooltip("team:N", title="Team"),
                          alt.Tooltip("season:Q", title="Season", format="d"),
                          alt.Tooltip("wins:Q", title="Wins")]))
st.altair_chart(dress(chart).properties(height=340), width="stretch", theme=None)

st.subheader("How the sport itself has changed")
note("Races per season, and how many different drivers won at least one of them. "
     "A season with one or two winners was a season somebody dominated.")
base = alt.Chart(shape).encode(x=alt.X("season:Q", title=None, axis=alt.Axis(format="d")))
races = base.mark_area(opacity=.35, color="#e10600").encode(
    y=alt.Y("races:Q", title="Races in the season"),
    tooltip=[alt.Tooltip("season:Q", title="Season", format="d"),
             alt.Tooltip("races:Q", title="Races"),
             alt.Tooltip("winners:Q", title="Different winners"),
             alt.Tooltip("teams:Q", title="Teams")])
winners = base.mark_line(strokeWidth=2.5, color="#27f4d2").encode(
    y=alt.Y("winners:Q", title="Different winners"))
st.altair_chart(dress(alt.layer(races, winners).resolve_scale(y="independent")),
                width="stretch", theme=None)

st.subheader("The numbers")
st.dataframe(
    shape.rename(columns={"season": "Season", "races": "Races",
                          "winners": "Different winners", "teams": "Teams",
                          "entries": "Cars entered"}).sort_values("Season", ascending=False),
    hide_index=True, width="stretch")
