"""Live demos for Academy Module 2 (tyres). They run on tyre_physics.py, the Tyre Lab fits
(tyres.py) and the real fastest laps."""
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import app_sim as A
import tyre_physics as TP
from academy_widgets import circuit_picker
from app_data import get_race_file
from charts import dress
from style import stat_strip


def slip_curves():
    load = st.slider("Load on the tyre (N)", 500, 8000, 2000, step=100, key="w_slip_load",
                     help="About 2,000 N is a quarter of the car's weight; at 250 km/h downforce adds about as much again.")
    angles = np.linspace(0, 16, 161)
    ratios = np.linspace(0, 0.4, 161)
    lat = pd.DataFrame({"Slip": angles, "Force (kN)": TP.lateral_force(angles, load) / 1000})
    lon = pd.DataFrame({"Slip": ratios * 100, "Force (kN)": TP.longitudinal_force(ratios, load) / 1000})
    left, right = st.columns(2)
    left.altair_chart(dress(alt.Chart(lat).mark_line(color="#e10600", strokeWidth=3).encode(
        x=alt.X("Slip:Q", title="Slip angle (°)"), y="Force (kN):Q")).properties(height=240, title="Cornering"),
        use_container_width=True)
    right.altair_chart(dress(alt.Chart(lon).mark_line(color="#e8b33a", strokeWidth=3).encode(
        x=alt.X("Slip:Q", title="Slip ratio (%)"), y="Force (kN):Q")).properties(height=240, title="Braking or driving"),
        use_container_width=True)
    pa = angles[int(np.argmax(lat["Force (kN)"]))]
    pr = ratios[int(np.argmax(lon["Force (kN)"]))]
    st.caption(f"Peak cornering force at about {pa:.0f}° of slip angle; peak braking or driving force at about "
               f"{pr:.0%} slip ratio. Past the peak the tyre slides and loses grip.")


def magic_shape():
    c1, c2, c3 = st.columns(3)
    B = c1.slider("B, stiffness", 6.0, 30.0, TP.B_LAT, step=0.5, key="w_mf_b")
    C = c2.slider("C, shape", 1.1, 1.9, TP.C_LAT, step=0.05, key="w_mf_c")
    E = c3.slider("E, curvature", -1.0, 0.9, TP.E_LAT, step=0.05, key="w_mf_e")
    x = np.linspace(0, 0.35, 200)
    base = TP.magic(x, 1.0, TP.B_LAT, TP.C_LAT, TP.E_LAT)
    yours = TP.magic(x, 1.0, B, C, E)
    df = pd.DataFrame({"Slip angle (°)": np.degrees(np.r_[x, x]), "Force (share of peak)": np.r_[base, yours],
                       "Curve": ["Typical slick"] * len(x) + ["Yours"] * len(x)})
    st.altair_chart(dress(alt.Chart(df).mark_line(strokeWidth=2.5).encode(
        x="Slip angle (°):Q", y="Force (share of peak):Q",
        color=alt.Color("Curve:N", scale=alt.Scale(domain=["Typical slick", "Yours"], range=["#8a8a96", "#e10600"]),
                        legend=alt.Legend(orient="top", title=None)))).properties(height=260), use_container_width=True)
    st.caption(f"Your curve peaks at {np.degrees(x[int(np.argmax(yours))]):.1f}° and keeps "
               f"{yours[-1] / yours.max():.0%} of its peak at 20°. D (the peak) is fixed at 1 so only the shape changes.")


def real_gg_widget():
    folder = circuit_picker("w_gg_circuit", default="Silverstone")
    gg = TP.real_gg(get_race_file(folder, "track"), A.get_track(folder))
    pts = pd.DataFrame({"Sideways g": np.abs(gg["lat_g"][::2]), "Braking / accelerating g": gg["long_g"][::2],
                        "Speed (km/h)": gg["speed_kmh"][::2].round(0)})
    pts = pts[(pts["Sideways g"] < 7) & (pts["Braking / accelerating g"].abs() < 7)]
    st.altair_chart(dress(alt.Chart(pts).mark_circle(size=24, opacity=.75).encode(
        x=alt.X("Sideways g:Q", scale=alt.Scale(domain=[0, 6.5])),
        y=alt.Y("Braking / accelerating g:Q", scale=alt.Scale(domain=[-6, 3])),
        color=alt.Color("Speed (km/h):Q", scale=alt.Scale(scheme="turbo")),
        tooltip=["Speed (km/h)"])).properties(height=360), use_container_width=True)
    st.caption("Every dot is a point on the real fastest lap. The fastest corners (red) reach the highest sideways g "
               "because downforce grows with speed. The Tyre Physics page has more.")


def weight_transfer():
    k = st.slider("Load sensitivity", 0.0, 0.3, 0.12, step=0.01, key="w_wt_k")
    shift = st.slider("Load moved to the outside tyre (N)", 0, 1800, 900, step=50, key="w_wt_shift")
    even = 2 * TP.mu_at(2000, 1.7, k) * 2000
    split = TP.mu_at(2000 + shift, 1.7, k) * (2000 + shift) + TP.mu_at(2000 - shift, 1.7, k) * (2000 - shift)
    stat_strip([
        ("Even load (2 × 2,000 N)", f"{even / 1000:.2f} kN", "grip of the pair", False),
        (f"Uneven ({2000 + shift:,} / {2000 - shift:,} N)", f"{split / 1000:.2f} kN", "same total load", False),
        ("Lost to weight transfer", f"{1 - split / even:.1%}", "a lower, wider car transfers less", True),
    ])


def temperature_window():
    push = st.slider("How hard the driver pushes", 0.75, 1.05, 0.95, step=0.01, key="w_tw_push")
    r = TP.stint_temperature(push=push)
    df = pd.DataFrame({"Lap": r["lap"], "Temperature (°C)": r["temperature"], "Grip": r["grip"]})
    band = alt.Chart(pd.DataFrame({"lo": [70], "hi": [130]})).mark_rect(opacity=.10, color="#1fd6a0").encode(
        y="lo:Q", y2="hi:Q")
    line = alt.Chart(df).mark_line(color="#e10600", strokeWidth=2.5).encode(
        x="Lap:Q", y=alt.Y("Temperature (°C):Q", scale=alt.Scale(domain=[40, 170])),
        tooltip=["Lap", alt.Tooltip("Temperature (°C):Q", format=".0f"), alt.Tooltip("Grip:Q", format=".0%")])
    st.altair_chart(dress(band + line).properties(height=260), use_container_width=True)
    st.caption(f"Mid-stint: {r['temperature'][12]:.0f} °C and {r['grip'][12]:.0%} of the best grip. The green band "
               "is the window. A teaching model with sensible, made-up constants.")


def tyre_cliff():
    from strategy import CLIFF_RATE, CLIFF_START
    c1, c2 = st.columns(2)
    wear = c1.slider("Wear rate (seconds lost per lap of age)", 0.00, 0.20, 0.06, step=0.01, key="w_cl_wear")
    life = c2.slider("Tyre life (laps)", 10, 50, 30, step=1, key="w_cl_life")
    age = np.arange(0, life + 12)
    start = CLIFF_START * life
    over = np.maximum(0, age - start)
    loss = wear * age + CLIFF_RATE * over * (over + 1) / 2
    df = pd.DataFrame({"Tyre age (laps)": age, "Time lost per lap (s)": loss})
    st.altair_chart(dress(alt.Chart(df).mark_line(color="#e10600", strokeWidth=3, point=True).encode(
        x="Tyre age (laps):Q", y="Time lost per lap (s):Q")).properties(height=260), use_container_width=True)
    st.caption(f"A straight line of wear, then a cliff from about lap {start:.0f}: the same tyre model our Pit Wall "
               "strategist uses.")


def real_degradation():
    import tyres
    folder = circuit_picker("w_deg_circuit", default="Barcelona")
    res = tyres.analyse(folder)
    if not res["compounds"]:
        st.info("Not enough clean laps on any compound in this race (a wet race, perhaps). Pick another.")
        return
    colours = {"SOFT": "#e4544a", "MEDIUM": "#e8b33a", "HARD": "#d9d9d4", "INTERMEDIATE": "#1fd6a0", "WET": "#2b6cff"}
    lines = []
    for c in res["compounds"]:
        ages = np.arange(0, c["max_age"] + 1)
        lines.append(pd.DataFrame({"Tyre age (laps)": ages,
                                   "Slower than a new reference tyre (s)": c["offset"] + c["wear"] * ages,
                                   "Compound": c["name"].title()}))
    names = [c["name"].title() for c in res["compounds"]]
    st.altair_chart(dress(alt.Chart(pd.concat(lines)).mark_line(strokeWidth=3).encode(
        x="Tyre age (laps):Q", y="Slower than a new reference tyre (s):Q",
        color=alt.Color("Compound:N", scale=alt.Scale(domain=names, range=[colours.get(n.upper(), "#8a8a96") for n in names]),
                        legend=alt.Legend(orient="top", title=None)))).properties(height=280), use_container_width=True)
    stat_strip([(c["name"].title(), f"{c['wear']:+.3f} s/lap", f"{c['laps']} clean laps", False)
                for c in res["compounds"]][:4])
    st.caption(f"Fitted on every clean racing lap with each driver's pace and fuel taken out (fuel: {res['fuel']:+.3f} s "
               f"per lap). Typical error {res['error']:.2f} s on laps the fit didn't see. Negative wear means laps got "
               "faster with age: track grip improving, or drivers managing early in the stint. Tyre Lab has every race.")
