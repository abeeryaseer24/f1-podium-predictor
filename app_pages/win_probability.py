"""Win Probability: how each driver's chances moved through a real race, lap by lap."""
import altair as alt
import pandas as pd
import streamlit as st

import race_engine as RE
import race_story as RS
from app_data import get_prepared_races
from charts import dress
from style import stat_strip
from ui_kit import board, section


@st.cache_data(ttl=86400, max_entries=40)
def odds(folder):
    race = RE.build(folder)
    return RE.win_odds(race), race


@st.cache_data(ttl=86400, max_entries=40)
def neutral(folder):
    laps, _, control, _ = RS.load(folder)
    return sorted(RS.neutral_laps(laps, control))


races = get_prepared_races()
seasons = sorted(races["season"].unique().tolist(), reverse=True)
c1, c2 = st.columns(2)
season = c1.selectbox("Season", seasons, key="wp_season")
in_season = races[races["season"] == season].sort_values("round")
names = {r.folder: f"Round {r.round} · {r.race_name}" for r in in_season.itertuples()}
folder = c2.selectbox("Race", list(names), index=len(names) - 1, format_func=names.get, key="wp_race")
what = st.radio("Show", ["win", "podium"], horizontal=True, key="wp_what",
                format_func=lambda k: {"win": "Chance of winning", "podium": "Chance of a podium"}[k])

data, race = odds(folder)
who = race["who"]
data["code"] = data["driver_number"].map(lambda d: who[d].get("code", str(d)))
peak = data.groupby("driver_number")[what].max()
shown = peak[peak >= (0.05 if what == "win" else 0.15)].index.tolist()
real_winner = next((d for d, p in race["real_pos"].items() if p == 1), None)
start = data[data["lap"] == data["lap"].min()].set_index("driver_number")[what]
first_fav = start.idxmax()
swing = data.groupby("driver_number")[what].agg(lambda s: s.max() - s.min())
biggest = swing.idxmax()
stat_strip([
    ("Favourite at the start", who[first_fav].get("code", "–"), f"{start.max():.0%} {'to win' if what == 'win' else 'podium'}", True),
    ("Winner", who.get(real_winner, {}).get("code", "–") if real_winner else "–",
     f"was {start.get(real_winner, 0):.0%} at the start" if real_winner else "", False),
    ("Biggest swing", who[biggest].get("code", "–"), f"{swing.max():.0%} between their best and worst moment", False),
])

section("The race, as odds", "Restarted from the real positions and gaps every two laps and replayed 200 times. "
        "Grey bands are safety car, VSC or red-flag laps.")
plot = data[data["driver_number"].isin(shown)]
colours = {who[d].get("code", str(d)): who[d].get("colour") or "#8a8a96" for d in shown}
sc = neutral(folder)
bands = alt.Chart(pd.DataFrame({"lap": sc, "lap2": [l + 1 for l in sc]})).mark_rect(color="#8a8a96", opacity=.18).encode(
    x="lap:Q", x2="lap2:Q") if sc else None
lines = alt.Chart(plot).mark_line(strokeWidth=3, interpolate="monotone").encode(
    x=alt.X("lap:Q", title="Lap", scale=alt.Scale(nice=False)),
    y=alt.Y(f"{what}:Q", title="Chance", axis=alt.Axis(format="%"), scale=alt.Scale(domain=[0, 1])),
    color=alt.Color("code:N", scale=alt.Scale(domain=list(colours), range=list(colours.values())),
                    legend=alt.Legend(orient="top", title=None)),
    tooltip=["code", "lap", alt.Tooltip(f"{what}:Q", format=".0%")])
st.altair_chart(dress((bands + lines) if bands is not None else lines).properties(height=340), use_container_width=True)

section("Whose race changed most", "Each driver's chances at the start, at their best, and at the flag.")
end = data[data["lap"] == data["lap"].max()].set_index("driver_number")[what]
rows = []
for d in swing.sort_values(ascending=False).index[:12]:
    rows.append({"colour": who[d].get("colour") or "#8a8a96",
                 "cells": [(f"{who[d].get('code', d)} · {str(who[d].get('name', '')).title()}", who[d].get("team", "")),
                           (start.get(d, 0), f"{start.get(d, 0):.0%}"), (peak.get(d, 0), f"{peak.get(d, 0):.0%}"),
                           (end.get(d, 0), f"{end.get(d, 0):.0%}"),
                           (end.get(d, 0) - start.get(d, 0), f"{end.get(d, 0) - start.get(d, 0):+.0%}"),
                           f"P{race['real_pos'][d]}" if d in race["real_pos"] else "–"]})
board([("Driver", "label"), ("At the start", "bar"), ("Best moment", "bar"), ("Near the flag", "bar"),
       ("Change", "delta"), ("Result", "num")], rows)
left, right = st.columns([3, 2], vertical_alignment="center")
left.caption("Uses each car's pace measured over the whole race and the real pit plans, so it knows how fast everyone "
             "was, but not the incidents, penalties or safety cars still to come.")
right.page_link("app_pages/race_simulator.py", label="Change the race in the Race Simulator", icon=":material/tune:")
