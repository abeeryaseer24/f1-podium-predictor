"""Live demos for Academy Modules 8, 9, 10, 14 and 16 (chassis and safety, cooling, data, rules, the capstone)."""
from dataclasses import replace

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import app_sim as A
from academy_widgets import circuit_picker
from charts import dress
from style import stat_strip
from ui_kit import board

G = 9.81


# ---------- 8.2 what a kilo costs ----------

def mass_cost():
    folder = circuit_picker("w8_mass_circuit", default="Silverstone")
    base = A.calibrated(folder)
    t0 = A.run_car(folder, A.car_key(base))["lap_time"]
    rows = []
    for dm in range(-20, 21, 5):
        rows.append({"Mass change (kg)": dm, "Lap time change (s)": A.run_car(folder, A.car_key(replace(base, mass=base.mass + dm)))["lap_time"] - t0})
    df = pd.DataFrame(rows)
    per10 = float(np.interp(10, df["Mass change (kg)"], df["Lap time change (s)"]))
    stat_strip([("10 kg costs", f"{per10:.3f} s", "a lap on this circuit", True),
                ("Over a race", f"{per10 * 55:.1f} s", "about 55 laps", False),
                ("Why ballast still helps", "Placement", "it moves weight where the engineers want it", False)])
    chart = alt.Chart(df).mark_line(point=True, color="#e10600", strokeWidth=2.5).encode(
        x="Mass change (kg):Q", y=alt.Y("Lap time change (s):Q"))
    st.altair_chart(dress(chart).properties(height=230), use_container_width=True)


# ---------- 8.3 the crash pulse ----------

def crash_pulse():
    c1, c2, c3 = st.columns(3)
    v = c1.slider("Impact speed (km/h)", 30, 250, 54, key="w8_v", help="The FIA frontal test is about 54 km/h (15 m/s).")
    d = c2.slider("Crush distance (cm)", 20, 150, 60, key="w8_d", help="How far the structure (and barrier) deforms.")
    m = c3.slider("Mass (kg)", 700, 900, 800, key="w8_m")
    vs = v / 3.6
    avg_g = vs ** 2 / (2 * d / 100) / G
    t = 2 * (d / 100) / vs
    energy = 0.5 * m * vs ** 2 / 1000
    stat_strip([("Average deceleration", f"{avg_g:.0f} g", "if the crush is perfectly even", True),
                ("Peak (triangle pulse)", f"{2 * avg_g:.0f} g", "real pulses peak higher", False),
                ("Energy to absorb", f"{energy:,.0f} kJ", "½ m v²", False),
                ("Over", f"{t * 1000:.0f} ms", "the length of the crash", False)])
    st.caption("Halve the crush distance and the deceleration doubles. That's why crash structures, barriers and run-off "
               "all buy distance.")


# ---------- 9.1 the heat budget ----------

def heat_budget():
    c1, c2, c3 = st.columns(3)
    era = c1.radio("Rules", ["2014–2025", "2026"], horizontal=True, key="w9_era")
    eff = c2.slider("Thermal efficiency (%)", 30, 55, 50, key="w9_eff")
    air = c3.slider("Air temperature (°C)", 10, 45, 25, key="w9_air")
    fuel_mw = 100 * 43.0e6 / 3600 / 1e6 if era == "2014–2025" else 3000 / 3600
    shaft = fuel_mw * eff / 100
    heat = fuel_mw - shaft
    exhaust, coolant = heat * 0.55, heat * 0.45
    delta = 120 - air
    area = coolant * 1e6 / (400 * delta)            # U ~ 400 W/m²K overall, coolant ~120 °C (illustrative)
    stat_strip([("Fuel energy in", f"{fuel_mw:.2f} MW", "at full throttle", True),
                ("To the crankshaft", f"{shaft * 1000:.0f} kW", f"{eff}% efficient", False),
                ("Into the radiators", f"{coolant * 1000:.0f} kW", "water and oil (the rest leaves in the exhaust)", False),
                ("Radiator area needed", f"{area:.1f} m²", f"coolant 120 °C, air {air} °C", False)])
    temps = pd.DataFrame({"Air (°C)": np.arange(10, 46), "Area (m²)": [coolant * 1e6 / (400 * (120 - a)) for a in range(10, 46)]})
    chart = alt.Chart(temps).mark_line(color="#e10600", strokeWidth=2.5).encode(x="Air (°C):Q", y="Area (m²):Q")
    st.altair_chart(dress(chart).properties(height=200), use_container_width=True)
    st.caption("Illustrative: a single overall heat-transfer coefficient. The point is the shape: the radiator has to "
               "grow fast as the air warms, because it's the temperature difference that carries the heat away.")


def cooling_drag():
    folder = circuit_picker("w9_drag_circuit", default="Marina Bay")
    base = A.calibrated(folder)
    open_ = st.slider("Extra cooling opening (drag, %)", 0, 8, 3, key="w9_open",
                      help="Bigger louvres and inlets cost drag.")
    t0 = A.run_car(folder, A.car_key(base))["lap_time"]
    t1 = A.run_car(folder, A.car_key(replace(base, drag_scale=1 + open_ / 100)))["lap_time"]
    stat_strip([("Lap time cost", f"{t1 - t0:+.3f} s", f"{open_}% more drag", True),
                ("Over a race", f"{(t1 - t0) * 60:+.1f} s", "about 60 laps", False)])


# ---------- 10.4 sampling rate ----------

def sampling():
    c1, c2 = st.columns(2)
    hz = c1.select_slider("Sample rate (Hz)", [2, 4, 10, 25, 100, 500], 4, key="w10_hz")
    peak = c2.slider("True peak braking (g)", 3.0, 6.0, 5.5, 0.1, key="w10_peak")
    t = np.linspace(0, 3, 3000)
    true = np.where((t > 0.5) & (t < 2.5), peak * np.exp(-((t - 0.9) / 0.35) ** 2) + 2.5 * np.clip((2.5 - t) / 2, 0, 1) * (t > 0.9), 0)
    true = np.maximum(true, 0)
    ts = np.arange(0, 3, 1 / hz)
    sampled = np.interp(ts, t, true)
    df = pd.concat([pd.DataFrame({"Time (s)": t, "g": true, "Signal": "The real braking"}),
                    pd.DataFrame({"Time (s)": ts, "g": sampled, "Signal": f"Sampled at {hz} Hz"})])
    stat_strip([("Measured peak", f"{sampled.max():.2f} g", f"at {hz} Hz", True),
                ("Missed", f"{peak - sampled.max():.2f} g", f"{(peak - sampled.max()) / peak:.0%} of the peak", False)])
    chart = alt.Chart(df).mark_line(strokeWidth=2.2, point=alt.OverlayMarkDef(size=25)).encode(
        x="Time (s):Q", y="g:Q", color=alt.Color("Signal:N", scale=alt.Scale(range=["#8a8a96", "#e10600"]),
                                                  legend=alt.Legend(orient="top", title=None)))
    st.altair_chart(dress(chart).properties(height=230), use_container_width=True)
    st.caption("Public timing data comes at a few samples a second, so short peaks are missed. Teams log key channels "
               "at hundreds of hertz or more.")


# ---------- 14.2 wind-tunnel time by championship place ----------

def atr_scale():
    rows = []
    for p in range(1, 11):
        share = 0.70 + 0.05 * (p - 1)
        rows.append({"colour": "#e10600" if p == 1 else None,
                     "cells": [(f"P{p}", "constructors'"), (share, f"{share:.0%}")]})
    board([("Finishing place", "label"), ("Share of the baseline wind-tunnel and CFD allowance", "bar")], rows)
    st.caption("The aerodynamic testing restriction since 2022: the champions get the least, the last-placed team the "
               "most, reset twice a year from the standings. Try it in Team Principal.")


# ---------- 16 capstone: design your car ----------

POINTS = 100


def capstone():
    folder = circuit_picker("w16_circuit", default="Silverstone")
    base = A.calibrated(folder)
    st.caption(f"You have {POINTS} design points. Each one buys a little of something; the lap simulator then drives your "
               "car on this circuit and it races the real field's pace.")
    c1, c2, c3, c4 = st.columns(4)
    down = c1.slider("Downforce", 0, 50, 25, key="w16_down")
    drag = c2.slider("Low drag", 0, 50, 25, key="w16_drag")
    mass = c3.slider("Weight saving", 0, 50, 25, key="w16_mass")
    power = c4.slider("Power", 0, 50, 25, key="w16_power")
    used = down + drag + mass + power
    if used > POINTS:
        st.warning(f"That's {used} points: {used - POINTS} over. Take some away.")
        return
    car = replace(base, downforce_scale=1 + (down - 25) * 0.004, drag_scale=1 - (drag - 25) * 0.004,
                  mass=base.mass - (mass - 25) * 0.6, power_kw=base.power_kw + (power - 25) * 1.6)
    ref = A.run_car(folder, A.car_key(base))
    mine = A.run_car(folder, A.car_key(car))
    delta = mine["lap_time"] - ref["lap_time"]
    pct = 100 * delta / ref["lap_time"]
    rng = np.random.default_rng(int(abs(delta) * 1e4) % 2 ** 31)
    field = np.r_[np.linspace(0.0, 2.2, 19), pct]         # the field spread round the reference car (illustrative)
    wins, avg = 0, 0.0
    for _ in range(2000):
        s = -field / 0.28 + rng.gumbel(size=len(field))
        place = int((s > s[-1]).sum()) + 1
        wins += place == 1
        avg += place
    stat_strip([("Your lap", A.lap_str(mine["lap_time"]), f"{delta:+.3f} s on the calibrated car", True),
                ("Top speed", A.kmh(mine["speed_kmh"].max()), f"{mine['speed_kmh'].max() - ref['speed_kmh'].max():+.0f} km/h", False),
                ("Win chance", f"{wins / 2000:.0%}", "against a typical field spread", False),
                ("Average finish", f"P{avg / 2000:.1f}", "over 2,000 races", False)])
    st.altair_chart(A.speed_chart([("Your car", "#e10600", mine["s"], mine["speed_kmh"]),
                                   ("Calibrated car", "#8a8a96", ref["s"], ref["speed_kmh"])], height=240),
                    use_container_width=True)
    st.caption(f"{used} of {POINTS} points used. Try a high-downforce car at Monaco and a low-drag car at Monza: the best "
               "design depends on the circuit, which is the whole of Module 1.4.")
