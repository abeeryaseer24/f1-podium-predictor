"""Live demos for Academy Modules 4-7 (aerodynamics, power unit, transmission, brakes)."""
from dataclasses import replace

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import aero_toys as T
import app_sim as A
import energy as EN
import engines as ENG
from academy_widgets import circuit_picker
from app_data import get_race_file
from charts import dress
from style import stat_strip

RHO, MU = 1.2, 1.8e-5


# ---------- Module 4: aerodynamics ----------

def bernoulli_floor():
    c1, c2 = st.columns(2)
    v = c1.slider("Car speed (km/h)", 50, 350, 250, step=10, key="w41_v") / 3.6
    speedup = c1.slider("Air speed under the floor (× car speed)", 1.0, 1.8, 1.35, step=0.05, key="w41_k")
    area = c2.slider("Floor area doing the work (m²)", 1.0, 4.0, 2.5, step=0.1, key="w41_a")
    dp = 0.5 * RHO * ((speedup * v) ** 2 - v ** 2)
    force = dp * area
    stat_strip([("Pressure drop under the floor", f"{dp / 1000:.2f} kPa", f"{dp / 101325:.1%} of atmospheric pressure", True),
                ("Downforce from the floor", f"{force / 1000:.1f} kN", f"like {force / 9.81:.0f} kg pressing down", False),
                ("Air under the floor", f"{speedup * v * 3.6:.0f} km/h", "faster air, lower pressure", False)])
    st.caption("Bernoulli: p + ½ρv² stays constant along a streamline, so where the air speeds up its pressure drops. "
               "An idealised calculation; real floors lose some of it to friction and leaks at the edges.")


def reynolds_calc():
    c1, c2 = st.columns(2)
    v = c1.slider("Speed (km/h)", 50, 350, 250, step=10, key="w42_v") / 3.6
    L = c2.slider("Length of the part (m)", 0.05, 5.0, 0.30, step=0.05, key="w42_l",
                  help="0.3 m is a front-wing element; 5 m is the whole car.")
    re = RHO * v * L / MU
    stat_strip([("Reynolds number", f"{re:,.0f}", "inertia ÷ viscosity", True),
                ("Flow regime", "turbulent" if re > 5e5 else "laminar for a while", "boundary layers trip at about 500,000", False),
                ("60 % wind-tunnel model", f"{re * 0.6 * (50 / max(v, 1)):,.0f}", "at the 50 m/s tunnel limit", False)])


def wing_polar():
    c1, c2 = st.columns(2)
    aspect = c1.slider("Aspect ratio (span ÷ chord)", 1.0, 8.0, 3.0, step=0.5, key="w43_ar")
    cd0 = c2.slider("Drag at zero lift, CD0", 0.01, 0.10, 0.03, step=0.005, key="w43_cd0")
    alpha = np.linspace(0, 22, 89)
    cl = np.where(alpha < 14, 2 * np.pi * np.radians(alpha) * aspect / (aspect + 2),
                  2 * np.pi * np.radians(14) * aspect / (aspect + 2) * (1 - 0.06 * (alpha - 14)))
    cd = cd0 + cl ** 2 / (np.pi * 0.85 * aspect) + np.where(alpha > 14, 0.02 * (alpha - 14), 0)
    df = pd.DataFrame({"Angle of attack (°)": np.r_[alpha, alpha], "Coefficient": np.r_[cl, cd],
                       "Curve": ["Lift (downforce)"] * len(alpha) + ["Drag"] * len(alpha)})
    best = int(np.argmax(cl / cd))
    st.altair_chart(dress(alt.Chart(df).mark_line(strokeWidth=3).encode(
        x="Angle of attack (°):Q", y="Coefficient:Q",
        color=alt.Color("Curve:N", scale=alt.Scale(domain=["Lift (downforce)", "Drag"], range=["#e10600", "#8a8a96"]),
                        legend=alt.Legend(orient="top", title=None)))).properties(height=260), use_container_width=True)
    st.caption(f"Best efficiency (lift ÷ drag = {cl[best] / cd[best]:.1f}) at {alpha[best]:.1f}°; the wing stalls "
               "near 14°. Thin-aerofoil theory with a finite-wing correction: a teaching approximation.")


def dirty_air_mini():
    gap = st.slider("Distance behind another car (m)", 5, 80, 20, key="w410_gap")
    stat_strip([(era, f"{float(T.kept(gap, era)):.0%}", "of its downforce kept", i == 0)
                for i, era in enumerate(T.FIA_POINTS)])
    st.caption("Through the FIA's published 2021 and 2022 figures. The Dirty Air Lab turns this into lap time.")


def porpoise_mini():
    h = st.slider("Static ride height (mm)", 22, 48, 30, key="w411_h")
    r = T.porpoise(static_mm=h, spring_kn_m=900, damper_kns_m=12, sensitivity=1.2)
    k = 25
    df = pd.DataFrame({"Speed (km/h)": r["speed_kmh"][::k], "Ride height (mm)": r["height_mm"][::k]})
    st.altair_chart(dress(alt.Chart(df).mark_line(color="#e10600", strokeWidth=1.5).encode(
        x="Speed (km/h):Q", y=alt.Y("Ride height (mm):Q", scale=alt.Scale(domain=[0, 52])))).properties(height=220),
        use_container_width=True)
    st.caption(f"Bouncing from {r['onset_kmh']:.0f} km/h." if r["onset_kmh"] else "No bouncing at this height.")


def active_aero_demo():
    folder = circuit_picker("w414_circuit", default="Monza")
    cut = st.slider("Drag cut on the straights (%)", 0, 50, 33, key="w414_cut")
    base = A.calibrated(folder)
    t0 = A.run_car(folder, A.car_key(base))["lap_time"]
    t1 = A.run_car(folder, A.car_key(replace(base, drag_scale=1 - cut / 100 * 0.8)))["lap_time"]
    stat_strip([("Lap time", f"{t1 - t0:+.3f}s", "against fixed wings", True),
                ("Top speed effect", "higher", "less drag, same power", False)])
    st.caption("Applied as an overall drag cut weighted towards the straights. The Energy Lab models the 2026 "
               "straight mode properly, with the battery.")


# ---------- Module 5: power unit ----------

def otto_efficiency():
    r = st.slider("Compression ratio", 6.0, 18.0, 12.0, step=0.5, key="w51_r")
    gamma = 1.35
    eta = 1 - 1 / r ** (gamma - 1)
    ratios = np.linspace(6, 18, 49)
    df = pd.DataFrame({"Compression ratio": ratios, "Ideal efficiency": 1 - 1 / ratios ** (gamma - 1)})
    st.altair_chart(dress(alt.Chart(df).mark_line(color="#e10600", strokeWidth=3).encode(
        x="Compression ratio:Q", y=alt.Y("Ideal efficiency:Q", axis=alt.Axis(format="%")))).properties(height=220),
        use_container_width=True)
    st.caption(f"Ideal Otto efficiency at {r:.1f}:1 is {eta:.0%}. Real engines lose heat, friction and pumping work; "
               "the best F1 power units passed 50 % in total by recovering exhaust energy.")


def fuel_flow_power():
    c1, c2 = st.columns(2)
    flow = c1.slider("Fuel flow (kg/h)", 40, 120, 100, key="w54_f", help="2014–2025 limit: 100 kg/h above 10,500 rpm.")
    eff = c2.slider("Thermal efficiency (%)", 25, 55, 50, key="w54_e")
    chem = flow / 3600 * 43e6
    stat_strip([("Chemical power in", f"{chem / 1000:,.0f} kW", "fuel at about 43 MJ/kg", False),
                ("Power out", f"{chem * eff / 100 / 1000:,.0f} kW", f"{chem * eff / 100 / 745.7:,.0f} hp", True),
                ("Heat to get rid of", f"{chem * (1 - eff / 100) / 1000:,.0f} kW", "exhaust and radiators", False)])
    st.caption("With fuel flow capped, the only way to more power is efficiency. That one rule drove the 2014–2025 engines.")


def energy_mini():
    folder = circuit_picker("w57_circuit", default="Monaco")
    era = st.radio("Power unit", list(EN.ERAS), horizontal=True, key="w57_era")
    car, pu = EN.car_for(folder, era)
    r = EN.simulate(car, A.get_track(folder), pu, mode="race")
    k = max(1, len(r["s"]) // 500)
    df = pd.DataFrame({"Distance (m)": r["s"][::k], "Battery (MJ)": r["soc_mj"][::k]})
    st.altair_chart(dress(alt.Chart(df).mark_area(color="#1fd6a0", opacity=.5, line={"color": "#1fd6a0"}).encode(
        x=alt.X("Distance (m):Q", scale=alt.Scale(nice=False)), y="Battery (MJ):Q")).properties(height=200),
        use_container_width=True)
    st.caption(f"Harvested {r['harvested_mj']:.1f} MJ, deployed {r['deployed_mj']:.1f} MJ, battery empty on "
               f"{r['clip_share']:.0%} of the deploy zones. The Energy Lab lets you plan it.")


def engine_sound_mini():
    names = [e["name"] for e in ENG.ERAS]
    pick = st.radio("Engine", names, horizontal=True, index=2, key="w511_e")
    ENG.engine_sound(next(e for e in ENG.ERAS if e["name"] == pick), dark=st.session_state.get("dark", True))


# ---------- Module 6: transmission ----------

def gear_ratios():
    folder = circuit_picker("w62_circuit", default="Monza")
    top = st.slider("Top speed in 8th gear at the rev limit (km/h)", 280, 380, 340, key="w62_top")
    rpm_max = 12500
    first = st.slider("1st gear top speed (km/h)", 60, 130, 95, key="w62_first")
    tops = np.geomspace(first, top, 8)
    sim = A.run_car(folder, A.car_key(A.calibrated(folder)))
    reach = float(sim["speed_kmh"].max())
    stat_strip([("Fastest point of the lap", f"{reach:.0f} km/h", "on the lap simulator", True),
                ("Revs there in 8th", f"{min(rpm_max, rpm_max * reach / top):,.0f} rpm",
                 "on the limiter: gear too short" if reach >= top else "room to spare", False),
                ("Step between gears", f"{(tops[1] / tops[0] - 1):.0%}", "evenly spaced ratios", False)])
    df = pd.DataFrame({"Gear": [str(g) for g in range(1, 9)], "Top speed (km/h)": tops.round(0)})
    st.altair_chart(dress(alt.Chart(df).mark_bar(color="#e10600", cornerRadius=4).encode(
        x=alt.X("Gear:N", axis=alt.Axis(labelAngle=0)), y="Top speed (km/h):Q")).properties(height=200),
        use_container_width=True)


# ---------- Module 7: brakes ----------

def braking_energy():
    c1, c2 = st.columns(2)
    v1 = c1.slider("Speed before braking (km/h)", 150, 350, 320, step=5, key="w71_v1") / 3.6
    v2 = c1.slider("Speed at the corner (km/h)", 50, 250, 90, step=5, key="w71_v2") / 3.6
    mass = c2.slider("Car mass (kg)", 760, 900, 820, key="w71_m")
    g = c2.slider("Average deceleration (g)", 2.0, 6.0, 4.5, step=0.1, key="w71_g")
    v2 = min(v2, v1 - 1)
    energy = 0.5 * mass * (v1 ** 2 - v2 ** 2)
    t = (v1 - v2) / (g * 9.81)
    dist = (v1 ** 2 - v2 ** 2) / (2 * g * 9.81)
    stat_strip([("Energy to get rid of", f"{energy / 1e6:.2f} MJ", "mostly as heat in the brakes", True),
                ("Time braking", f"{t:.2f} s", f"over {dist:.0f} m", False),
                ("Average braking power", f"{energy / t / 1e6:.1f} MW", "more than a thousand hairdryers", False)])
