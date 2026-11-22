"""Energy Lab: the battery round a lap. Choose where to deploy and try to beat the default plan."""
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import app_sim as A
import energy as E
from charts import dress
from scene_env import env_for
from sim3d import lap_view
from style import stat_strip
from ui_kit import board, section

PHASE_COLOURS = {"deploy": "#1fd6a0", "harvest": "#2b6cff", "clip": "#e4544a", "engine": "#8a8a96"}
PHASE_LEGEND = [("Deploying", "#1fd6a0"), ("Harvesting", "#2b6cff"), ("Battery empty (clipping)", "#e4544a"),
                ("Engine only", "#8a8a96")]


@st.cache_data(ttl=3600, max_entries=300)
def run(folder, era, mode, aero, plan):
    car, pu = E.car_for(folder, era)
    pu = E.PowerUnit(**{**pu.__dict__, "active_aero": aero})
    return E.simulate(car, A.get_track(folder), pu, deploy_on=list(plan) if plan is not None else None, mode=mode)


folder = A.pick_race("energy")
c1, c2, c3 = st.columns(3)
era = c1.radio("Power unit", list(E.ERAS), horizontal=True, key="en_era")
mode = c2.radio("Lap", ["race", "qualifying"], horizontal=True, key="en_mode",
                format_func=lambda m: {"race": "Race (energy-neutral)", "qualifying": "Qualifying (full battery)"}[m])
aero = c3.toggle("Active aero on the straights", value=E.ERAS[era]["active_aero"], key=f"en_aero_{era}",
                 help="2026: wings flatten on the straights to cut drag.")

base = run(folder, era, mode, aero, None)
zones = base["straights"]
labels = [f"S{k + 1} · {int(e - s):,} m" for k, (_, _, s, e) in enumerate(zones)]
key = f"en_plan_{folder}_{era}_{mode}_{aero}"
st.session_state.setdefault(key, labels)
def search():
    """Switch straights on and off one at a time, keeping every change that makes the lap faster.
    Runs as a button callback, before the pills are drawn, so it may set their selection."""
    plan_ = [True] * len(labels)
    best = run(folder, era, mode, aero, tuple(plan_))["lap_time"]
    for _ in range(2):
        for k in range(len(plan_)):
            trial = plan_.copy()
            trial[k] = not trial[k]
            t = run(folder, era, mode, aero, tuple(trial))["lap_time"]
            if t < best - 1e-4:
                plan_, best = trial, t
    st.session_state[key] = [lab for lab, on in zip(labels, plan_) if on]
    st.session_state[f"{key}_found"] = (all(plan_), best)


left, right = st.columns([4, 1], vertical_alignment="bottom")
right.button("Find a better plan", use_container_width=True, key=f"{key}_search", on_click=search)
chosen = left.pills("Deploy the battery on", labels, selection_mode="multi", key=key)
found = st.session_state.pop(f"{key}_found", None)
if found:
    st.toast("Deploying everywhere is already the fastest plan here: the battery empties on every straight and "
             "refills in the next braking zone." if found[0] else f"Found a faster plan: {A.lap_str(found[1])}.")

plan = tuple(lab in (chosen or []) for lab in labels)
yours = run(folder, era, mode, aero, plan)
delta = yours["lap_time"] - base["lap_time"]
stat_strip([
    ("Your lap", A.lap_str(yours["lap_time"]),
     "same as deploying everywhere" if abs(delta) < 5e-4 else f"{abs(delta):.3f}s {'faster' if delta < 0 else 'slower'}"
     " than deploying everywhere", True),
    ("Energy harvested", f"{yours['harvested_mj']:.2f} MJ", "braking" + (" + turbo (MGU-H)" if yours["turbo_mj"] > 0 else ""), False),
    ("Energy deployed", f"{yours['deployed_mj']:.2f} MJ", "on the straights you picked", False),
    ("Battery empty", f"{yours['clip_share']:.0%}", "of the deploy zones (clipping)", False),
])

# ---------- 3D ----------
section("Your plan against deploying everywhere", "The track shows what your car is doing at each point.")
track = A.get_track(folder)
ghost = "#f5f5f7" if st.session_state.dark else "#15151e"
def car_of(r, name, colour):
    return {"name": name, "colour": colour, "t": np.r_[r["time"], r["lap_time"]],
            "s": np.r_[r["s"], r["s"][-1] + (r["s"][1] - r["s"][0])]}
lap_view(A.three_track(track, [PHASE_COLOURS[p] for p in yours["phase"]], PHASE_LEGEND),
         [car_of(yours, "YOU", "#e10600"), car_of(base, "ALL", ghost)],
         labels=A.corner_labels(folder, track), dark=st.session_state.dark, env=env_for(folder), height=500)

# ---------- battery ----------
section("The battery round the lap", "Charge in the battery (MJ) and the car's speed, against distance.")
k = max(1, len(yours["s"]) // 600)
soc = pd.DataFrame({"Distance (m)": yours["s"][::k], "Battery (MJ)": yours["soc_mj"][::k],
                    "Phase": pd.Series(yours["phase"][::k]).map({"deploy": "Deploying", "harvest": "Harvesting",
                                                                 "clip": "Battery empty (clipping)", "engine": "Engine only"})})
bands = alt.Chart(soc).mark_area(opacity=.35, interpolate="step-after").encode(
    x=alt.X("Distance (m):Q", scale=alt.Scale(nice=False)), y="Battery (MJ):Q",
    color=alt.Color("Phase:N", scale=alt.Scale(domain=[l for l, _ in PHASE_LEGEND], range=[c for _, c in PHASE_LEGEND]),
                    legend=alt.Legend(orient="top", title=None)))
line = alt.Chart(soc).mark_line(color="#e10600", strokeWidth=2).encode(x="Distance (m):Q", y="Battery (MJ):Q")
st.altair_chart(dress(bands + line).properties(height=220), use_container_width=True)
st.altair_chart(A.speed_chart([("Your plan", "#e10600", yours["s"], yours["speed_kmh"]),
                               ("Deploy everywhere", "#8a8a96", base["s"], base["speed_kmh"])],
                              marks=A.corner_marks(folder, track), height=260), use_container_width=True)

# ---------- straights ----------
section("Straight by straight", "Time gained or lost on each straight against deploying everywhere.")
t_y = np.interp([e for _, _, _, e in zones], yours["s"], yours["time"])
t_b = np.interp([e for _, _, _, e in zones], base["s"], base["time"])
t_y0 = np.interp([s for _, _, s, _ in zones], yours["s"], yours["time"])
t_b0 = np.interp([s for _, _, s, _ in zones], base["s"], base["time"])
rows = []
for kk, (lab, on) in enumerate(zip(labels, plan)):
    gain = (t_b[kk] - t_b0[kk]) - (t_y[kk] - t_y0[kk])
    i, j = zones[kk][0], zones[kk][1]
    clip = float((yours["phase"][i:j + 1] == "clip").mean())
    rows.append({"colour": "#1fd6a0" if on else "#8a8a96",
                 "cells": [(lab, "deploying" if on else "engine only"), (round(gain * 1000), f"{gain * 1000:+.0f} ms"),
                           (float(yours["speed_kmh"][i:j + 1].max()), f"{yours['speed_kmh'][i:j + 1].max():.0f} km/h"),
                           (clip, f"{clip:.0%}")]})
board([("Straight", "label"), ("Time on this straight", "delta"), ("Top speed", "bar"), ("Battery empty", "scale_low")], rows)
st.caption("Teaching model with rounded public power-unit figures; see the Academy's power unit module for how it works.")
