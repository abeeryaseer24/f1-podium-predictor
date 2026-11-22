"""Porpoising Lab: a ground-effect car accelerating down a straight. Find a setup that doesn't bounce."""
import altair as alt
import pandas as pd
import streamlit as st

import aero_toys as T
from charts import dress
from style import stat_strip
from ui_kit import board, section


@st.cache_data(ttl=3600, max_entries=200)
def run(h, k, c, sens):
    r = T.porpoise(static_mm=h, spring_kn_m=k, damper_kns_m=c, sensitivity=sens)
    return {key: r[key] for key in ("t", "speed_kmh", "height_mm", "vertical_g", "onset_kmh", "max_swing_mm",
                                    "mean_downforce_n")}


PRESETS = {"Bouncing (2022 launch)": (30, 900, 12, 1.2), "Stiffer springs": (30, 1600, 12, 1.2),
           "Raised floor": (42, 900, 12, 1.2), "Well damped": (30, 900, 45, 1.2), "Gentler floor": (30, 900, 12, 0.5)}
st.caption("Accelerating from 200 to 330 km/h on a straight. Tune the car until the floor stops bouncing, "
           "without giving away more downforce than you have to.")
pick = st.radio("Start from", list(PRESETS), horizontal=True, key="pp_preset")
h0, k0, c0, s0 = PRESETS[pick]
c1, c2 = st.columns(2)
h = c1.slider("Static ride height (mm)", 20, 50, h0, key=f"pp_h_{pick}")
k = c1.slider("Heave spring (kN/m)", 400, 2500, k0, step=50, key=f"pp_k_{pick}")
c = c2.slider("Damping (kN·s/m)", 4, 80, c0, key=f"pp_c_{pick}")
sens = c2.slider("How aggressive the floor is", 0.3, 1.6, s0, step=0.1, key=f"pp_s_{pick}",
                 help="How much extra downforce each millimetre closer to the track gives.")

r = run(h, k, c, sens)
ref = run(*PRESETS["Bouncing (2022 launch)"])
bouncing = r["onset_kmh"] is not None
stat_strip([
    ("Bouncing", f"from {r['onset_kmh']:.0f} km/h" if bouncing else "None", "the floor stalls and recovers" if bouncing
     else "the floor stays attached all the way", True),
    ("Worst bounce", f"{r['max_swing_mm']:.0f} mm", "peak-to-peak ride height", False),
    ("Peak vertical load", f"{abs(r['vertical_g']).max():.1f} g", "what the driver feels", False),
    ("Average downforce", f"{r['mean_downforce_n'] / ref['mean_downforce_n']:.0%}", "of the bouncing launch car", False),
])

section("Ride height down the straight", "The floor's distance from the track as the car speeds up. "
        "The red band is where this floor stalls.")
k_ = 20
df = pd.DataFrame({"Speed (km/h)": r["speed_kmh"][::k_], "Ride height (mm)": r["height_mm"][::k_]})
band = alt.Chart(pd.DataFrame({"lo": [0], "hi": [18]})).mark_rect(color="#e4544a", opacity=.12).encode(y="lo:Q", y2="hi:Q")
line = alt.Chart(df).mark_line(color="#e10600", strokeWidth=1.6).encode(
    x=alt.X("Speed (km/h):Q", scale=alt.Scale(domain=[200, 330])),
    y=alt.Y("Ride height (mm):Q", scale=alt.Scale(domain=[0, max(52, float(df["Ride height (mm)"].max()) + 2)])))
st.altair_chart(dress(band + line).properties(height=300), use_container_width=True)

section("Every preset at a glance", "The same straight for each starting setup.")
rows = []
for name, args in PRESETS.items():
    rr = run(*args)
    rows.append({"colour": "#e4544a" if rr["onset_kmh"] else "#1fd6a0",
                 "cells": [(name, f"{args[0]} mm · {args[1]} kN/m · {args[2]} kN·s/m"),
                           (rr["onset_kmh"] or 400, f"{rr['onset_kmh']:.0f} km/h" if rr["onset_kmh"] else "never"),
                           (rr["max_swing_mm"], f"{rr['max_swing_mm']:.0f} mm"),
                           (rr["mean_downforce_n"] / ref["mean_downforce_n"], f"{rr['mean_downforce_n'] / ref['mean_downforce_n']:.0%}")]})
board([("Setup", "label"), ("Bouncing from", "scale"), ("Worst bounce", "scale_low"), ("Downforce", "scale")], rows)
left, right = st.columns([3, 2], vertical_alignment="center")
left.caption("Teaching model with illustrative constants.")
right.page_link("app_pages/academy_m3.py", label="Learn it: Academy 3.6 Ride height and rake",
                icon=":material/school:", query_params={"ch": "3.6"})
