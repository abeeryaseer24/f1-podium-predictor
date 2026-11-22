"""Engine Room: Formula 1 engines from the 1980s turbos to 2026, with their sound synthesised live."""
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import app_sim as A
import engines as EN
from app_data import get_race_file, get_race_info
from charts import dress
from style import stat_strip
from ui_kit import board, section

names = [e["name"] for e in EN.ERAS]
pick = st.segmented_control("Engine", names, default="3.0 V10", key="er_era") or "3.0 V10"
era = next(e for e in EN.ERAS if e["name"] == pick)

stat_strip([
    ("Era", era["years"], era["name"], True),
    ("Rev limit", f"{era['rpm_max']:,} rpm", f"firing {EN.firing_hz(era['rpm_max'], era['cylinders']):,.0f} times a second", False),
    ("Power", era["power_hp"], "horsepower, rounded", False),
    ("Layout", f"{era['cylinders']} cylinders, {era['litres']} L", "turbocharged" if era["turbo"] else "no turbo", False),
])
st.caption(era["note"])

section("Hear it", "Synthesised in your browser from the engine's firing frequency, not a recording. "
        "Start the engine, drag the rev counter, or drive a real lap.")
folder = A.pick_race("er_lap")
t, rpm = EN.lap_rpm(get_race_file(folder, "track"), era)
engine_lap = {"t": np.round(t, 2).tolist(), "rpm": np.round(rpm).tolist()}
EN.engine_sound(era, lap=engine_lap, dark=st.session_state.dark)
st.caption(f"'Drive the lap' plays the {get_race_info(folder)['race_name']} {get_race_info(folder)['season']} fastest "
           "lap's gear changes and speed in this engine's rev range.")

section("Every era side by side")
rows = [{"colour": e["colour"],
         "cells": [(e["name"], e["years"]), (e["rpm_max"], f"{e['rpm_max']:,} rpm"),
                   (EN.firing_hz(e["rpm_max"], e["cylinders"]), f"{EN.firing_hz(e['rpm_max'], e['cylinders']):,.0f} Hz"),
                   e["power_hp"].split(" (")[0],
                   (e["colour"], ("Turbo hybrid" if e["hybrid"] else "Turbo") if e["turbo"] else "Naturally aspirated")]}
        for e in EN.ERAS]
board([("Engine", "label"), ("Rev limit", "bar"), ("Firing frequency", "bar"), ("Power (hp)", "text"), ("Breathing", "tag")], rows)

section("The sound, as a number", "Firing frequency against engine speed: higher means a higher-pitched scream.")
rpms = np.linspace(4000, 19000, 60)
df = pd.concat([pd.DataFrame({"rpm": rpms[rpms <= e["rpm_max"]],
                              "Firing frequency (Hz)": EN.firing_hz(rpms[rpms <= e["rpm_max"]], e["cylinders"]),
                              "Engine": e["name"]}) for e in EN.ERAS])
chart = alt.Chart(df).mark_line(strokeWidth=3).encode(
    x=alt.X("rpm:Q", title="Engine speed (rpm)"), y="Firing frequency (Hz):Q",
    color=alt.Color("Engine:N", scale=alt.Scale(domain=names, range=[e["colour"] for e in EN.ERAS]),
                    legend=alt.Legend(orient="top", title=None, columns=3)))
st.altair_chart(dress(chart).properties(height=300), use_container_width=True)
left, right = st.columns([3, 2], vertical_alignment="center")
left.caption("Rounded public figures. The synthesiser is a teaching toy: real engines add exhaust, intake and gear noise.")
right.page_link("app_pages/academy_m1.py", label="Learn it: Academy 1.1 Anatomy of an F1 car",
                icon=":material/school:", query_params={"ch": "1.1"})
