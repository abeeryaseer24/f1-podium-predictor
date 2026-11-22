"""Tyre Physics: how a racing tyre grips, slides, overheats, and shares its grip."""
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import app_sim as A
import tyre_physics as T
from app_data import get_race_file, get_race_info
from charts import dress, theme
from style import stat_strip
from ui_kit import section

text, grid, muted = theme()
def learn(what, chapter, title):
    """One line saying what the tool shows, and where the Academy explains it."""
    left, right = st.columns([3, 2], vertical_alignment="center")
    left.caption(what)
    right.page_link("app_pages/academy_m2.py", label=f"Learn it: Academy {chapter} {title}",
                    icon=":material/school:", query_params={"ch": chapter})


tabs = st.tabs(["The magic formula", "Load sensitivity", "The friction circle", "The temperature window"])

# ---------- 1. magic formula ----------
with tabs[0]:
    learn("Force against slip: shape the curve.", "2.3", "The magic formula")
    c1, c2, c3 = st.columns(3)
    load = c1.slider("Load on the tyre (N)", 500, 8000, 2000, step=100, key="tp_load",
                     help="About 2,000 N is a quarter of the car's weight. Downforce adds thousands more at speed.")
    mu0 = c1.slider("Grip (friction coefficient)", 1.0, 2.5, 1.7, step=0.05, key="tp_mu")
    B = c2.slider("Stiffness, B", 6.0, 30.0, T.B_LAT, step=0.5, key="tp_b",
                  help="How quickly force builds with slip: a stiffer tyre responds sooner and peaks earlier.")
    C = c2.slider("Shape, C", 1.1, 1.9, T.C_LAT, step=0.05, key="tp_c",
                  help="How sharply the force falls after the peak.")
    E = c3.slider("Curvature, E", -1.0, 0.9, T.E_LAT, step=0.05, key="tp_e",
                  help="How rounded the curve is near its peak.")
    k = c3.slider("Load sensitivity", 0.0, 0.3, 0.12, step=0.01, key="tp_k")
    slip = np.linspace(0, 20, 401)
    force = T.lateral_force(slip, load, mu0, k, B, C, E)
    peak_i = int(np.argmax(force))
    stiffness = (force[4] - force[0]) / (slip[4] - slip[0])
    stat_strip([
        ("Peak cornering force", f"{force[peak_i] / 1000:.2f} kN", f"{force[peak_i] / load:.2f}× the load on the tyre", True),
        ("Peak at", f"{slip[peak_i]:.1f}°", "of slip angle", False),
        ("Cornering stiffness", f"{stiffness:.0f} N/°", "how much force each degree buys", False),
        ("At 15° of slip", f"{T.lateral_force(15, load, mu0, k, B, C, E) / force[peak_i]:.0%}", "of the peak: past it, the tyre slides", False),
    ])
    data = pd.DataFrame({"Slip angle (°)": slip, "Force (kN)": force / 1000})
    curve = alt.Chart(data).mark_line(color="#e10600", strokeWidth=3).encode(
        x="Slip angle (°):Q", y=alt.Y("Force (kN):Q", title="Cornering force (kN)"))
    dot = alt.Chart(data.iloc[[peak_i]]).mark_point(filled=True, size=120, color="#e10600").encode(
        x="Slip angle (°):Q", y="Force (kN):Q")
    st.altair_chart(dress(curve + dot).properties(height=320), use_container_width=True)
    st.caption("Typical racing-slick shape, not Pirelli data.")

# ---------- 2. load sensitivity ----------
with tabs[1]:
    learn("Grip against load, and what weight transfer costs.", "2.5", "Load sensitivity")
    k2 = st.slider("Load sensitivity", 0.0, 0.3, 0.12, step=0.01, key="tp_k2",
                   help="0 means grip grows exactly in step with load.")
    loads = np.linspace(500, 9000, 200)
    sens = pd.DataFrame({"Load (N)": np.r_[loads, loads],
                         "Peak force (kN)": np.r_[T.mu_at(loads, 1.7, k2) * loads, 1.7 * loads] / 1000,
                         "Tyre": ["Real tyre"] * len(loads) + ["If grip grew in step with load"] * len(loads)})
    chart = alt.Chart(sens).mark_line(strokeWidth=2.5).encode(
        x="Load (N):Q", y="Peak force (kN):Q",
        color=alt.Color("Tyre:N", scale=alt.Scale(domain=["Real tyre", "If grip grew in step with load"],
                                                  range=["#e10600", "#8a8a96"]),
                        legend=alt.Legend(orient="top", title=None)),
        strokeDash=alt.condition(alt.datum.Tyre == "Real tyre", alt.value([1, 0]), alt.value([5, 4])))
    st.altair_chart(dress(chart).properties(height=300), use_container_width=True)
    shift = st.slider("Load moved from the inside tyre to the outside tyre in a corner (N)", 0, 1800, 900, step=50,
                      key="tp_shift")
    even = 2 * T.mu_at(2000, 1.7, k2) * 2000
    split = T.mu_at(2000 + shift, 1.7, k2) * (2000 + shift) + T.mu_at(2000 - shift, 1.7, k2) * (2000 - shift)
    stat_strip([
        ("Two tyres, 2,000 N each", f"{even / 1000:.2f} kN", "of grip between them", False),
        (f"{2000 + shift:,} N and {2000 - shift:,} N", f"{split / 1000:.2f} kN", "same total load", False),
        ("Grip lost to weight transfer", f"{(1 - split / even):.1%}", "this is why low, stiff, wide cars corner better", True),
    ])

# ---------- 3. friction circle ----------
with tabs[2]:
    learn("The real fastest lap as a g-g diagram.", "2.4", "The friction circle and g-g diagrams")
    folder = A.pick_race("tyre_gg")
    track = A.get_track(folder)
    gg = T.real_gg(get_race_file(folder, "track"), track)
    sim = A.run_car(folder, A.car_key(A.calibrated(folder)))
    step = 2
    real_pts = pd.DataFrame({"Lateral g": np.abs(gg["lat_g"][::step]), "Longitudinal g": gg["long_g"][::step],
                             "Speed (km/h)": gg["speed_kmh"][::step].round(0), "Lap": "Real fastest lap"})
    sim_pts = pd.DataFrame({"Lateral g": sim["lat_g"][::step], "Longitudinal g": sim["long_g"][::step],
                            "Speed (km/h)": sim["speed_kmh"][::step].round(0), "Lap": "Our lap simulator"})
    show_sim = st.toggle("Show the lap simulator's car too", value=False, key="tp_gg_sim")
    pts = pd.concat([real_pts, sim_pts]) if show_sim else real_pts
    pts = pts[(pts["Lateral g"] < 7) & (pts["Longitudinal g"].abs() < 7)]
    scatter = alt.Chart(pts).mark_circle(size=26, opacity=.75).encode(
        x=alt.X("Lateral g:Q", title="Sideways g (cornering)", scale=alt.Scale(domain=[0, 6.5])),
        y=alt.Y("Longitudinal g:Q", title="Braking (down) and accelerating (up), g", scale=alt.Scale(domain=[-6, 3])),
        color=(alt.Color("Lap:N", scale=alt.Scale(domain=["Real fastest lap", "Our lap simulator"],
                                                  range=["#e10600", "#8a8a96"]), legend=alt.Legend(orient="top", title=None))
               if show_sim else alt.Color("Speed (km/h):Q", scale=alt.Scale(scheme="turbo"),
                                          legend=alt.Legend(orient="right"))),
        tooltip=["Lap", "Speed (km/h)", alt.Tooltip("Lateral g:Q", format=".2f"), alt.Tooltip("Longitudinal g:Q", format=".2f")])
    st.altair_chart(dress(scatter).properties(height=420), use_container_width=True)
    lat95 = np.percentile(np.abs(gg["lat_g"]), 95)
    brake95 = -np.percentile(gg["long_g"], 1)
    stat_strip([
        ("Cornering, near the limit", f"{lat95:.1f} g", "95th percentile of the lap", True),
        ("Braking, near the limit", f"{brake95:.1f} g", "hardest 1 % of the lap", False),
        ("Accelerating, best", f"{np.percentile(gg['long_g'], 99):.1f} g", "power-limited above low speed", False),
    ])
    st.caption(f"{get_race_info(folder)['race_name']} {get_race_info(folder)['season']} · about 4 samples a second, "
               "so single dots are noisy.")

# ---------- 4. temperature ----------
with tabs[3]:
    learn("A 25-lap stint: how hard the driver pushes sets the tyre temperature.", "2.6", "Temperature and pressure")
    c1, c2 = st.columns(2)
    push = c1.slider("How hard the driver pushes", 0.75, 1.05, 0.95, step=0.01, key="tp_push",
                     help="1.00 = on the limit in every corner. Below that, the driver is managing the tyres.")
    heat = c2.slider("Track heat", 0.6, 1.4, 1.0, step=0.05, key="tp_heat",
                     help="Higher: a hot track or a softer compound that warms quickly.")
    runs = {f"Your driver ({push:.2f})": T.stint_temperature(push=push, heat=heat),
            "Flat out (1.00)": T.stint_temperature(push=1.0, heat=heat),
            "Gentle (0.85)": T.stint_temperature(push=0.85, heat=heat)}
    rows = []
    for name, r in runs.items():
        rows.append(pd.DataFrame({"Lap": r["lap"], "Temperature (°C)": r["temperature"], "Grip": r["grip"], "Driver": name}))
    df = pd.concat(rows)
    colours = ["#e10600", "#e8b33a", "#27c2f4"]
    window = alt.Chart(pd.DataFrame({"lo": [70], "hi": [130]})).mark_rect(opacity=.10, color="#1fd6a0").encode(
        y="lo:Q", y2="hi:Q")
    temp = alt.Chart(df).mark_line(strokeWidth=2.5).encode(
        x="Lap:Q", y=alt.Y("Temperature (°C):Q", scale=alt.Scale(domain=[40, 170])),
        color=alt.Color("Driver:N", scale=alt.Scale(domain=list(runs), range=colours),
                        legend=alt.Legend(orient="top", title=None)))
    gripc = alt.Chart(df).mark_line(strokeWidth=2.5).encode(
        x="Lap:Q", y=alt.Y("Grip:Q", title="Grip (1 = best possible)", scale=alt.Scale(domain=[0, 1.05])),
        color=alt.Color("Driver:N", scale=alt.Scale(domain=list(runs), range=colours), legend=None))
    left, right = st.columns(2)
    left.altair_chart(dress(window + temp).properties(height=280), use_container_width=True)
    right.altair_chart(dress(gripc).properties(height=280), use_container_width=True)
    mine = runs[f"Your driver ({push:.2f})"]
    stat_strip([
        ("Tread temperature, mid-stint", f"{mine['temperature'][12]:.0f} °C", "the green band is the window", True),
        ("Grip, mid-stint", f"{mine['grip'][12]:.0%}", "of the best possible", False),
        ("Tread used after 25 laps", f"{mine['wear'][-1]:.0%}", "illustrative", False),
    ])
    st.caption("Teaching model with illustrative constants.")
