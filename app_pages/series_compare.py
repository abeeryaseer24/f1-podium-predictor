"""Series Compare: one circuit lapped by an F1, F2, F3, Formula E and IndyCar-style car."""
import json

import numpy as np
import streamlit as st

import app_sim as A
import lapsim
import series_compare as SC
from scene_env import env_for
from sim3d import lap_view
from style import stat_strip
from ui_kit import GOOD, POOR, board, section

F1_COLOUR = "#e10600"


@st.cache_data(ttl=86400)
def data():
    return json.loads(SC.OUT.read_text(encoding="utf-8"))


d = data()
folder = A.pick_race("series")
track = A.get_track(folder)
cal = A.get_calibration()
f1_car = A.calibrated(folder)
laps = {"F1": A.run_car(folder, A.car_key(f1_car))}
for key, spec in d["cars"].items():
    car = lapsim.Car(**{**lapsim.asdict(f1_car), **spec["car"]})
    laps[key] = A.run_car(folder, A.car_key(car))
label = {"F1": "Formula 1", **{k: v["label"] for k, v in d["cars"].items()}}
colour = {"F1": F1_COLOUR, **{k: v["colour"] for k, v in d["cars"].items()}}
real = {p["series"]: p for p in d["poles"] if p["folder"] == folder}

tiles = []
for i, (k, sim) in enumerate(laps.items()):
    gap = sim["lap_time"] - laps["F1"]["lap_time"]
    sub = "the calibrated F1 car" if k == "F1" else f"{gap:+.1f} s · top {sim['speed_kmh'].max():.0f} km/h"
    if k in real:
        sub += f" · real pole {A.lap_str(real[k]['pole'])}"
    tiles.append((label[k], A.lap_str(sim["lap_time"]), sub, i == 0))
stat_strip(tiles)

section("Five cars, one lap", "They start together. The track is coloured by what limits the F1 car.")
lap_view(A.three_track(track, [A.MODE_COLOURS[m] for m in laps["F1"]["mode"]], A.MODE_LEGEND),
         [A.sim_car(sim, k.upper(), colour[k]) for k, sim in laps.items()],
         labels=A.corner_labels(folder, track), dark=st.session_state.dark, env=env_for(folder), height=480)

section("Speed all the way round")
st.altair_chart(A.speed_chart([(label[k], colour[k], sim["s"], sim["speed_kmh"]) for k, sim in laps.items()],
                              marks=A.corner_marks(folder, track)), use_container_width=True)

# ---------- where the time goes ----------
section("Where each car loses time to F1", "The lap split by how fast the F1 car is going there: slow corners, "
        "medium-speed sections, and fast sweepers and straights.")
f1_kmh = laps["F1"]["speed_kmh"]
zones = {"slow": f1_kmh < 150, "medium": (f1_kmh >= 150) & (f1_kmh < 250), "fast": f1_kmh >= 250}
ds = track.length / len(track.s)


def zone_times(sim):
    v = sim["speed"]
    dt = 2 * ds / (v + np.roll(v, -1))
    return {z: float(dt[m].sum()) for z, m in zones.items()}


base = zone_times(laps["F1"])
share = {z: m.mean() for z, m in zones.items()}
rows = []
for k, sim in laps.items():
    if k == "F1":
        continue
    loss = {z: t - base[z] for z, t in zone_times(sim).items()}
    rows.append({"colour": colour[k], "cells": [(label[k], f"{sum(loss.values()):+.1f} s in all"),
                                                 *[(loss[z], f"{loss[z]:+.1f} s") for z in ("slow", "medium", "fast")]]})
board([("Car", "label"), (f"Slow, under 150 km/h ({share['slow']:.0%} of the lap)", "bar"),
       (f"Medium, 150–250 ({share['medium']:.0%})", "bar"), (f"Fast, over 250 ({share['fast']:.0%})", "bar")], rows)

chk = d["check"]
st.caption(
    f"How it's built: every car runs on the lap simulator with its own weight, power, downforce and drag, using the F1 "
    f"car's wing level here. F2 and F3 each have one tuned number, their tyre grip, fitted to the real pole laps of the "
    f"F2 and F3 races on F1 weekends (Wikipedia's round articles, CC BY-SA 4.0); predicting circuits left out of the fit, "
    f"they're off by {chk['F2']['mean_abs_pct']:.1f}% (F2, {chk['F2']['poles']} poles) and {chk['F3']['mean_abs_pct']:.1f}% "
    f"(F3, {chk['F3']['poles']} poles) on average. Formula E and IndyCar never race on these circuits, so their cars use "
    f"published numbers only: {d['cars']['FE']['source']}; {d['cars']['Indy']['source']}. A point-mass model: no "
    f"tyre warm-up, energy limits, DRS or push-to-pass.")
