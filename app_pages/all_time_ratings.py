"""All-Time Ratings: every driver since 1950, with the car taken out."""
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import eras
from charts import dress
from style import stat_strip
from ui_kit import board, section


@st.cache_data(ttl=86400)
def ratings():
    data = eras.load()
    if not data:
        return None, None
    d = pd.DataFrame(data["drivers"])
    d["mid"] = (d["first"] + d["last"]) / 2
    d["era"] = (d["mid"] // 10 * 10).astype(int)
    rated = d[d["races"] >= data["min_races"]].copy()
    stats = rated.groupby("era")["skill"].agg(["mean", "std"])
    rated["era_z"] = (rated["skill"] - rated["era"].map(stats["mean"])) / rated["era"].map(stats["std"])
    return rated, pd.DataFrame(data["cars"])


drivers, cars = ratings()
if drivers is None:
    st.info("The ratings are built by the robot after new results.")
    st.stop()

c1, c2 = st.columns([2, 3])
view = c1.radio("Rating", ["Against their own era", "One scale for all eras"], key="atr_view",
                help="Era: how far above the average driver of the same decade. One scale: the model's raw rating, "
                     "which flatters the 1950s, when fields mixed stars with weekend amateurs.")
decades = ["All"] + [f"{d}s" for d in sorted(drivers["era"].unique())]
decade = c2.segmented_control("Decade", decades, default="All", key="atr_decade") or "All"
col = "era_z" if view.startswith("Against") else "skill"
pool = drivers if decade == "All" else drivers[drivers["era"] == int(decade[:-1])]
ranked = pool.sort_values(col, ascending=False).reset_index(drop=True)
top = ranked.iloc[0]
stat_strip([
    ("Highest rated", top["name"], f"{top['first']}–{top['last']}", True),
    ("Drivers rated", f"{len(pool)}", f"with at least {drivers['races'].min()} classified finishes", False),
    ("Best single season", (b := pool.loc[pool["peak"].idxmax()])["name"], f"{b['peak_season']}, car taken out", False),
])

section("The ranking", "Car taken out. Team-mates' results separate driver from car; drivers who changed teams "
        "link everyone onto one scale.")
rows = []
for _, r in ranked.head(30).iterrows():
    unit = "σ" if col == "era_z" else ""
    rows.append({"colour": "#e10600" if r["last"] >= 2025 else "#8a8a96",
                 "cells": [(r["name"], f"{r['first']}–{r['last']} · mostly {r['team']}"),
                           (max(r[col], 0.05), f"{r[col]:+.2f}{unit}"),
                           f"±{r['se'] / (drivers[drivers['era'] == r['era']]['skill'].std() if col == 'era_z' else 1):.2f}",
                           f"{r['peak_season']}", int(r["races"]), int(r["wins"])]})
board([("Driver", "label"), ("Rating", "bar"), ("Uncertainty", "num"), ("Best season", "num"), ("Finishes", "num"),
       ("Wins", "num")], rows, ranked=True)
st.caption("Red edge: still racing. 'Against their own era' is in standard deviations above the average driver of the "
           "same decade (by the middle of their career).")

section("Driver against car, season by season", "The driver's rating each season next to their car's strength. "
        "Where the lines split, the driver was beating (or flattered by) the car.")
names = dict(zip(drivers["driver"], drivers["name"]))
default = drivers.sort_values("skill", ascending=False)["driver"].iloc[0]
pick = st.selectbox("Driver", sorted(names, key=names.get), index=sorted(names, key=names.get).index("hamilton")
                    if "hamilton" in names else 0, format_func=names.get, key="atr_pick")
info = drivers[drivers["driver"] == pick].iloc[0]
seasons = {int(k): v for k, v in info["seasons"].items()}
raw = pd.read_csv(eras.RESULTS_FILE)
mine = raw[(raw["driver"] == pick)].groupby("season")["constructor"].agg(lambda s: s.value_counts().index[0])
car_map = cars.set_index("car")["strength"]
rows = []
for s, v in sorted(seasons.items()):
    rows.append({"Season": s, "Rating": v, "What": "Driver"})
    if s in mine.index and f"{mine[s]}_{s}" in car_map.index:
        rows.append({"Season": s, "Rating": car_map[f"{mine[s]}_{s}"] + info["skill"] * 0, "What": "Car"})
df = pd.DataFrame(rows)
chart = alt.Chart(df).mark_line(point=True, strokeWidth=3).encode(
    x=alt.X("Season:O"), y=alt.Y("Rating:Q", title="Strength (model scale)"),
    color=alt.Color("What:N", scale=alt.Scale(domain=["Driver", "Car"], range=["#e10600", "#8a8a96"]),
                    legend=alt.Legend(orient="top", title=None)),
    tooltip=["Season", "What", alt.Tooltip("Rating:Q", format=".2f")])
st.altair_chart(dress(chart).properties(height=280), use_container_width=True)
left, right = st.columns([3, 2], vertical_alignment="center")
left.caption("Classified finishes only (retirements left out), Indianapolis 500 excluded. Early decades have fewer races, "
             "so their ratings are less certain.")
right.page_link("app_pages/driver_swap.py", label="Put any driver in any car: Driver Swap", icon=":material/swap_horiz:")
