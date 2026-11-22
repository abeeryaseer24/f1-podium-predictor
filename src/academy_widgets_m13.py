"""Live demos for Academy Module 13 (circuits): the circuit map, the 3D tours and the designer."""
import json
import statistics
from dataclasses import replace
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

import app_sim as A
import lapsim
from app_data import get_race_file
from charts import dress
from circuit_designer import designer
from scene_env import env_for
from sim3d import lap_view
from style import stat_strip
from ui_kit import GOOD, POOR, board, diverge

TOURS = Path(__file__).resolve().parent.parent / "data" / "processed" / "circuit_tours.json"


@st.cache_data(ttl=86400)
def tours():
    return json.loads(TOURS.read_text(encoding="utf-8")) if TOURS.exists() else []


def _name(t):
    return t["race_name"].replace(" Grand Prix", "")


# ---------- 13.1 how circuits differ ----------

def circuit_map():
    data = tours()
    if not data:
        st.info("The circuit tours haven't been built yet.")
        return
    # gains as a share of the lap, so long and short circuits compare fairly
    df = pd.DataFrame([{"Circuit": _name(t), "Power": -t["sensitivity"]["power"] / t["lap"] * 100,
                        "Downforce": -t["sensitivity"]["downforce"] / t["lap"] * 100, "Average km/h": t["avg_kmh"],
                        "Full throttle": t["full_throttle"], "Wing": t["wing"]} for t in data])
    points = alt.Chart(df).mark_circle(size=140, opacity=.9).encode(
        x=alt.X("Power:Q", title="Gained from 10 kW more power (% of the lap)"),
        y=alt.Y("Downforce:Q", title="Gained from 5% more downforce (% of the lap)"),
        color=alt.Color("Average km/h:Q", scale=alt.Scale(scheme="redyellowgreen"), legend=alt.Legend(orient="top")),
        tooltip=["Circuit", alt.Tooltip("Power:Q", format=".2f"), alt.Tooltip("Downforce:Q", format=".2f"),
                 alt.Tooltip("Average km/h:Q", format=".0f"), alt.Tooltip("Full throttle:Q", format=".0%"), "Wing"])
    labels = points.mark_text(align="left", dx=8, fontSize=10).encode(text="Circuit", color=alt.value("#a3a3b2"))
    st.altair_chart(dress(points + labels).properties(height=420), use_container_width=True)
    power_end = df.loc[(df["Power"] / df["Downforce"]).idxmax(), "Circuit"]
    aero_end = df.loc[(df["Downforce"] / df["Power"]).idxmax(), "Circuit"]
    st.caption(f"Right and low: power circuits, like {power_end}. Up and left: downforce circuits, like {aero_end}. "
               "Each dot is the lap simulator's calibrated car at that circuit's most recent race.")


# ---------- 13.2 circuit tours ----------

def _gear_text(c):
    return f"gear {c['gear']}"


def circuit_tour():
    data = tours()
    if not data:
        st.info("The circuit tours haven't been built yet.")
        return
    names = {t["folder"]: f"{t['race_name']} {t['season']}" for t in sorted(data, key=lambda t: t["race_name"])}
    folder = st.selectbox("Circuit", list(names), format_func=names.get, key="w13_tour")
    t = next(x for x in data if x["folder"] == folder)
    stat_strip([
        ("Lap", A.lap_str(t["lap"]), f"simulator · real {A.lap_str(t['real_lap'])}", True),
        ("Length", f"{t['length_km']:.2f} km", f"{len(t['corners'])} corners · {t['braking_zones']} braking zones", False),
        ("Average speed", f"{t['avg_kmh']:.0f} km/h", f"top {t['top_kmh']} · slowest {t['min_kmh']}", False),
        ("Full throttle", f"{t['full_throttle']:.0%}", f"wing level {t['wing']:.2f} of 1", False),
    ])

    # the flyover: onboard with the simulated car, the real lap as a ghost
    track = A.get_track(folder)
    car = A.calibrated(folder)
    sim = A.run_car(folder, A.car_key(car))
    real_t, real_s = lapsim.real_progress(get_race_file(folder, "track"), track)
    ghost = "#f5f5f7" if st.session_state.get("dark", True) else "#15151e"
    lap_view(A.three_track(track, [A.MODE_COLOURS[m] for m in sim["mode"]], A.MODE_LEGEND),
             [A.sim_car(sim, "SIM", A.SIM_COLOUR), {"name": "REAL", "colour": ghost, "t": real_t, "s": real_s}],
             labels=A.corner_labels(folder, track), dark=st.session_state.get("dark", True),
             env=env_for(folder), view="onboard", height=480, note="Hills shown 4× higher")
    st.caption("Press Play for the flyover. Onboard rides with the simulated car; Overview shows the whole circuit.")

    # corner by corner
    rows = []
    for c in t["corners"]:
        braking = (f"from {c['brake_from_kmh']} km/h, {c['brake_m']} m before" if c["brake_m"] else
                   "no braking (a lift or flat)")
        rows.append({"colour": "#e10600" if c["overtaking"] else "#8a8a96", "cells": [
            (c["label"], "overtaking spot" if c["overtaking"] else _gear_text(c)),
            (c["sim_kmh"], f"{c['sim_kmh']} km/h"), f"{c['real_kmh']} km/h", braking,
            (c["brake_g"] or 0, f"{c['brake_g']:.1f} g" if c["brake_g"] else "–"),
            (c["lat_g"], f"{c['lat_g']:.1f} g")]})
    board([("Corner", "label"), ("Apex (simulator)", "scale"), ("Apex (real)", "num"), ("Braking", "text"),
           ("Braking g", "bar"), ("Cornering g", "bar")], rows)
    st.caption("Red edge: an overtaking spot, a stop from above 270 km/h to below 160 km/h after a long full-throttle "
               "run. The real apex speed comes from the race's fastest lap.")

    # what matters most here
    s = t["sensitivity"]
    items = [("10 kW more power", s["power"]), ("5% more downforce", s["downforce"]),
             ("5% less drag", s["drag"]), ("10 kg less mass", s["mass"])]
    diverge([{"name": label, "sub": f"{gain:+.3f} s a lap", "value": round(-gain * 1000),
              "colour": GOOD if gain < 0 else POOR} for label, gain in sorted(items, key=lambda kv: kv[1])],
            left_label="Slower (ms a lap)", right_label="Faster (ms a lap)")
    extra = []
    if t.get("wear_factor") is not None:
        extra.append(f"tyre wear {t['wear_factor']:.1f}× a typical circuit")
    if t.get("pit_loss") is not None:
        extra.append(f"a pit stop costs about {t['pit_loss']:.0f} s")
    if t.get("altitude_m", 0) > 800:
        extra.append(f"{t['altitude_m']} m above sea level, so the air is thinner")
    if extra:
        st.caption("Also here: " + " · ".join(extra) + ".")


# ---------- 13.4 designing a circuit ----------

def designer_widget():
    cal = A.get_calibration()
    cars = [c["car"] for f, c in cal.items() if c.get("usable") and f.startswith(str(max(int(k[:4]) for k in cal)))]
    typical = replace(lapsim.Car(), **{k: statistics.median(c[k] for c in cars) for k in ("mass", "power_kw", "wing", "grip")})
    designer(typical, dark=st.session_state.get("dark", True), height=740)
