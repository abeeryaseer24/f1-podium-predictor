"""Qualifying Game: Q1, Q2 and Q3 against the real laps of a real session."""
import streamlit as st

import quali_rules as Q
from app_sim import lap_str
from style import stat_strip
from ui_kit import GOLD, GOOD, POOR, banner, board, section

KEY = "quali_game"
PLANS = {"late": "One run, late (faster track, more risk)", "early": "One run, early (clear track)",
         "both": "Two runs, early and late (uses two new sets)"}
SEG = {1: "Q1", 2: "Q2", 3: "Q3"}

if not Q.DATA:
    st.info("The qualifying sessions haven't been prepared yet.")
    st.stop()

g = st.session_state.get(KEY)
if g is None:
    races = sorted(Q.DATA.values(), key=lambda r: r["folder"], reverse=True)
    names = {r["folder"]: f"{r['race_name']} {r['season']}" for r in races}
    c1, c2 = st.columns(2)
    folder = c1.selectbox("Session", list(names), format_func=names.get, key="qg_race")
    race = Q.DATA[folder]
    team_list = sorted(Q.teams(race))
    team = c2.selectbox("Your car", team_list, key=f"qg_team_{folder}")
    stand_in = Q.replaced(race, team)
    st.caption(f"You take {stand_in['name']}'s place. Your rivals are the other drivers' real laps from this session; "
               f"the track got {abs(race['evolution']):.3f} s faster every minute.")
    if st.button("Go to Q1", type="primary"):
        st.session_state[KEY] = Q.new_game(folder, team)
        st.rerun()
    st.stop()

race = Q.DATA[g["folder"]]
stat_strip([
    ("Session", f"{race['race_name'].replace(' Grand Prix', '')} {race['season']}", g["team"], True),
    ("Now", "Done" if g["over"] else SEG[g["seg"]], f"{race['q2']} go through Q1, {race['q3']} through Q2", False),
    ("New tyre sets", f"{g['sets']}", "a used set costs about 0.35 s", False),
])

# ---------- the last segment ----------
for e in reversed(g["log"][-1:]):
    through = {1: race["q2"], 2: race["q3"], 3: 1}[e["seg"]]
    ok = e["seg"] == 3 or e["pos"] <= through
    head = (f"{SEG[e['seg']]}: P{e['pos']} of {e['of']}, " + (lap_str(e["best"]) if e["best"] else "no time"))
    text = "; ".join(e["notes"]) or "a clean lap"
    if e["cut"] and e["best"]:
        text += f". The cut was {lap_str(e['cut'])} ({e['best'] - e['cut']:+.3f} s)."
    banner("⏱", head, text, GOOD if ok else POOR)

# ---------- finished ----------
if g["over"]:
    real, last_seg = Q.real_result(race, g)
    real_best = min(b["time"] for b in real["best"].values())
    grid = g["grid"]
    banner("🏁", f"You qualify P{grid}", f"In reality {real['name']} reached {SEG[last_seg]} with a best of "
           f"{lap_str(real_best)}.", GOLD if grid <= 3 else (GOOD if grid <= 10 else POOR))
    if st.button("Try again", type="primary"):
        del st.session_state[KEY]
        st.rerun()
else:
    seg = g["seg"]
    section(f"Your {SEG[seg]} plan", "When to run, whether to chase a tow, and how hard to push.")
    plan = st.radio("Runs", list(PLANS), format_func=PLANS.get, key=f"qg_plan_{seg}")
    c1, c2 = st.columns(2)
    tow = c1.toggle("Chase a tow on the straights", key=f"qg_tow_{seg}")
    push = c2.radio("Push", ["safe", "limit"], format_func={"safe": "A safe lap", "limit": "On the limit"}.get,
                    horizontal=True, key=f"qg_push_{seg}")
    if st.button(f"Run {SEG[seg]}", type="primary"):
        st.session_state[KEY] = Q.run_segment(dict(g), plan, tow, push)
        st.rerun()

# ---------- the timesheet ----------
if g["log"]:
    e = g["log"][-1]
    through = {1: race["q2"], 2: race["q3"], 3: 99}[e["seg"]]
    section(f"{SEG[e['seg']]} timesheet", "Real laps from the session, and yours. Below the line is out.")
    top = e["order"][0][3]
    rows = []
    for i, (code, team, colour, t) in enumerate(e["order"], start=1):
        you = code == "YOU"
        rows.append({"colour": "#e10600" if you else colour,
                     "cells": [("You" if you else code, team), lap_str(t) if t < 900 else "no time",
                               "—" if i == 1 else (f"+{t - top:.3f}" if t < 900 else ""),
                               "out" if i > through else ""]})
    board([("Driver", "label"), ("Lap", "num"), ("Gap", "num"), ("", "text")], rows, ranked=True)

st.caption("The lap times, cut lines and track evolution are real (OpenF1's qualifying laps, split into Q1, Q2 and "
           "Q3 where the knockout pauses). The risks and gains of each choice are illustrative: traffic and yellow "
           "flags on late runs, the tow (worth more at power circuits), mistakes on the limit, and about 0.35 s for a "
           "used set of tyres.")
