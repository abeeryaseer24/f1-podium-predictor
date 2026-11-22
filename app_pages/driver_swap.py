"""Driver Swap: put any driver from any era in any car, and replay that season."""
import pandas as pd
import streamlit as st

import eras
from style import stat_strip
from ui_kit import board, section


@st.cache_data(ttl=86400)
def data():
    return eras.load()


@st.cache_data(ttl=86400, max_entries=200)
def run(season, seat, new, peak):
    return eras.swap(data(), season, seat, new, use_peak=peak)


@st.cache_data(ttl=86400)
def seats(season):
    df = eras.finishers()
    df = df[df["season"] == season]
    top = df.groupby("driver").agg(name=("driver_name", "last"), team=("constructor_name", lambda s: s.value_counts().index[0]),
                                   races=("pos", "size"), best=("pos", "min"))
    return top[top["races"] >= 4].sort_values("best")


ratings = data()
if not ratings:
    st.info("The ratings are built by the robot after new results.")
    st.stop()
drivers = pd.DataFrame(ratings["drivers"])
pool = drivers[drivers["races"] >= ratings["min_races"]].sort_values("skill", ascending=False)
names = dict(zip(pool["driver"], pool["name"]))

seasons = sorted(eras.finishers()["season"].unique().tolist(), reverse=True)
c1, c2, c3 = st.columns(3)
season = c1.selectbox("Season", seasons, key="ds_season")
seat_table = seats(season)
seat = c2.selectbox("Whose car", seat_table.index.tolist(),
                    format_func=lambda d: f"{seat_table.at[d, 'name']} ({seat_table.at[d, 'team']})", key=f"ds_seat_{season}")
new = c3.selectbox("Put in", pool["driver"].tolist(), format_func=names.get, key="ds_new",
                   index=pool["driver"].tolist().index("senna") if "senna" in names else 0)
peak = st.toggle("Use each driver's best season (otherwise their career average)", value=True, key="ds_peak")

res = run(season, seat, new, peak)
real, swap = res["real"], res["swap"]
team = seat_table.at[seat, "team"]
stat_strip([
    (f"{names.get(new, new)} in the {season} {team}", f"{swap['points']:.0f} pts", f"title in {swap['title']:.0%} of seasons", True),
    (f"{seat_table.at[seat, 'name']} (real driver)", f"{real['points']:.0f} pts", f"title in {real['title']:.0%} of seasons", False),
    ("Difference", f"{swap['points'] - real['points']:+.0f} pts", f"average championship place P{swap['rank']:.1f} vs P{real['rank']:.1f}", False),
])
st.caption(f"Over {real['races']} races, each season replayed 2,000 times with today's points system. Rivals keep "
           "their real cars and drivers.")

section("Famous what-ifs", "A few swaps across the decades, with each driver at their best.")
famous = [(1988, "senna", "max_verstappen"), (2023, "max_verstappen", "senna"), (1992, "mansell", "michael_schumacher"),
          (2004, "michael_schumacher", "hamilton"), (2020, "hamilton", "alonso"), (1963, "clark", "fangio")]
rows = []
for s, a, b in famous:
    if b not in names or s not in seasons:
        continue
    try:
        r = run(s, a, b, True)
    except Exception:
        continue
    st_tab = seats(s)
    if a not in st_tab.index:
        continue
    gain = r["swap"]["points"] - r["real"]["points"]
    rows.append({"colour": "#1fd6a0" if gain > 0 else "#e4544a",
                 "cells": [(f"{names[b]} in the {s} {st_tab.at[a, 'team']}", f"instead of {st_tab.at[a, 'name']}"),
                           (r["swap"]["title"], f"{r['swap']['title']:.0%}"), (r["real"]["title"], f"{r['real']['title']:.0%}"),
                           (gain, f"{gain:+.0f} pts")]})
if rows:
    board([("Swap", "label"), ("Title odds, swapped", "bar"), ("Title odds, real", "bar"), ("Points", "delta")], rows)
left, right = st.columns([3, 2], vertical_alignment="center")
left.caption("Built on the All-Time Ratings model: a driver's skill plus the car's strength that season, with "
             "race-to-race randomness. A thought experiment, not a fact: era, rules and safety differ hugely.")
right.page_link("app_pages/all_time_ratings.py", label="See the All-Time Ratings", icon=":material/leaderboard:")
