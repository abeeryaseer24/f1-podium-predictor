"""Dirty Air Lab: how much a car loses following another, and why the 2022 rules changed the cars."""
from dataclasses import replace

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import aero_toys as T
import app_sim as A
from charts import dress
from style import stat_strip
from ui_kit import board, section

ERA_COLOURS = {"2017–2021 cars": "#e8b33a", "2022+ cars": "#1fd6a0"}

folder = A.pick_race("dirty")
gap_s = st.slider("Gap to the car in front (seconds)", 0.2, 3.0, 0.8, step=0.1, key="da_gap")
base = A.calibrated(folder)
sim = A.run_car(folder, A.car_key(base))
corner_speed = float(np.median(sim["speed"][sim["mode"] == "corner"])) if (sim["mode"] == "corner").any() else 55.0
straight_speed = float(np.median(sim["speed"][sim["mode"] == "throttle"]))
gap_corner, gap_straight = gap_s * corner_speed, gap_s * straight_speed

results = {}
for era in T.FIA_POINTS:
    keep = float(T.kept(gap_corner, era))
    follower = replace(base, downforce_scale=keep, drag_scale=float(T.tow(gap_straight)))
    no_tow = replace(base, downforce_scale=keep)
    results[era] = {"keep": keep,
                    "lap": A.run_car(folder, A.car_key(follower))["lap_time"] - sim["lap_time"],
                    "corners": A.run_car(folder, A.car_key(no_tow))["lap_time"] - sim["lap_time"]}
old, new = results["2017–2021 cars"], results["2022+ cars"]
stat_strip([
    ("Distance behind", f"{gap_corner:.0f} m", f"in a typical corner here ({corner_speed * 3.6:.0f} km/h)", True),
    ("Downforce kept, 2017–21 car", f"{old['keep']:.0%}", f"costs {old['corners']:+.2f}s a lap in the corners", False),
    ("Downforce kept, 2022+ car", f"{new['keep']:.0%}", f"costs {new['corners']:+.2f}s a lap in the corners", False),
    ("Tow on the straights", f"{1 - float(T.tow(gap_straight)):.0%}", "less drag right behind", False),
])

section("Downforce kept behind another car", "Through the FIA's published points (dots). The dashed line is your gap.")
gaps = np.linspace(3, 100, 200)
df = pd.concat([pd.DataFrame({"Metres behind": gaps, "Downforce kept": T.kept(gaps, era), "Cars": era})
                for era in T.FIA_POINTS])
pts = pd.DataFrame([{"Metres behind": g, "Downforce kept": v, "Cars": era}
                    for era, p in T.FIA_POINTS.items() for g, v in p.items()])
scale = alt.Scale(domain=list(ERA_COLOURS), range=list(ERA_COLOURS.values()))
lines = alt.Chart(df).mark_line(strokeWidth=3).encode(
    x="Metres behind:Q", y=alt.Y("Downforce kept:Q", axis=alt.Axis(format="%"), scale=alt.Scale(domain=[0.3, 1.02])),
    color=alt.Color("Cars:N", scale=scale, legend=alt.Legend(orient="top", title=None)))
dots = alt.Chart(pts).mark_point(filled=True, size=110).encode(x="Metres behind:Q", y="Downforce kept:Q",
                                                               color=alt.Color("Cars:N", scale=scale, legend=None))
rule = alt.Chart(pd.DataFrame({"x": [gap_corner]})).mark_rule(strokeDash=[5, 4], color="#e10600").encode(x="x:Q")
st.altair_chart(dress(lines + dots + rule).properties(height=300), use_container_width=True)

section("Can it follow?", "Lap time lost to the wake at every gap, with the tow on the straights included.")
rows = []
for g in (0.3, 0.5, 0.8, 1.0, 1.5, 2.0):
    cells = [(f"{g:.1f} s behind", f"about {g * corner_speed:.0f} m in the corners")]
    for era in T.FIA_POINTS:
        keep = float(T.kept(g * corner_speed, era))
        t = A.run_car(folder, A.car_key(replace(base, downforce_scale=keep,
                                                 drag_scale=float(T.tow(g * straight_speed)))))["lap_time"] - sim["lap_time"]
        cells.append((-t, f"{t:+.2f}s"))
    rows.append({"colour": "#e10600" if abs(g - gap_s) < 0.05 else "#8a8a96", "cells": cells})
board([("Gap", "label"), *[(f"{era}: lap time", "delta") for era in T.FIA_POINTS]], rows)
left, right = st.columns([3, 2], vertical_alignment="center")
left.caption("Downforce loss from the FIA's 2021 figures; the tow and the lap times come from our lap simulator.")
right.page_link("app_pages/academy_m1.py", label="Learn it: Academy 1.2 The regulations",
                icon=":material/school:", query_params={"ch": "1.2"})
