"""AI Strategist: a reinforcement-learning agent learns pit strategy by trial and error, then takes on the real teams."""
import json

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import rl_strategist as RL
from app_data import get_race_info
from charts import dress
from style import stat_strip
from ui_kit import GOOD, POOR, board, section

TYRE = {"SOFT": "#e4544a", "MEDIUM": "#e8b33a", "HARD": "#d9d9d4"}


@st.cache_data(ttl=600)
def runs():
    return {f: json.loads((RL.OUT / f"{f}.json").read_text()) for f in RL.trained()}


data = runs()
if not data:
    st.info("The AI strategist hasn't been trained on any race yet. The robot trains it on new races after each run.")
    st.stop()
folders = sorted(data, reverse=True)
folder = st.selectbox("Race", folders, format_func=lambda f: data[f]["race"], key="ai_race")
o = data[folder]
real_tyres_all = [c for _, c in o["real_plan"]]
real_lengths = [b - a for a, b in zip([0] + [l for l, _ in o["real_plan"][:-1]], [l for l, _ in o["real_plan"]])]
# Wet tyres, red-flag tyre changes or very short stints mean the real stops weren't a dry-race strategy
comparable = len(o["real_plan"]) <= 4 and all(c in TYRE for c in real_tyres_all) and min(real_lengths) >= 4
if not comparable:
    st.warning(f"{o['winner']}'s real stops in this race include wet tyres, a red flag or very short stints, so they "
               "aren't a fair comparison for a dry-race strategy. The AI is compared with the best fixed plan only.")

stat_strip([
    ("AI against the winner's stops", f"{o['real_mean'] - o['rl_mean']:+.1f} s" if comparable else "not comparable",
     f"faster on average · better in {o['rl_beats_real']:.0%} of races" if comparable else "see the note above", True),
    ("AI against the best fixed plan", f"{o['fixed_mean'] - o['rl_mean']:+.1f} s", f"better in {o['rl_beats_fixed']:.0%} of races", False),
    ("Reacted to a safety car", f"{o['reacted_to_sc']:.0%}", "of races, by boxing early", False),
    ("Practice", f"{o['races_tried']:,}", f"simulated races per plan · {o['train_seconds']} s", False),
])


def plan_cells(stops, tyres, laps):
    edges = [0] + list(stops) + [laps]
    return " → ".join(f"{t.title()} {edges[k + 1] - edges[k]}" for k, t in enumerate(tyres))


section("Three strategies, the same 400 races", "Each raced alone on identical random safety cars, so only the strategy differs.")
real_tyres = [c for _, c in o["real_plan"]]
real_stops = [l for l, _ in o["real_plan"][:-1]]
p = o["policy"]
rows = [
    {"colour": "#e10600", "cells": [("AI strategist", f"box early if a safety car comes within {p['window']} laps of a stop"),
                                     plan_cells(p["stops"], p["tyres"], o["laps"]), (0.0, "±0.0 s")]},
    {"colour": "#8a8a96", "cells": [("Best fixed plan", "searched over every one- and two-stop combination"),
                                     plan_cells(o["best_fixed"]["stops"], o["best_fixed"]["tyres"], o["laps"]),
                                     (o["rl_mean"] - o["fixed_mean"], f"{o['fixed_mean'] - o['rl_mean']:+.1f} s")]},
] + ([{"colour": "#27c2f4", "cells": [(f"{o['winner']}'s real stops", "the race winner's strategy, replayed"),
                                       plan_cells(real_stops, real_tyres, o["laps"]),
                                       (o["rl_mean"] - o["real_mean"], f"{o['real_mean'] - o['rl_mean']:+.1f} s")]}]
      if comparable else [])
board([("Strategy", "label"), ("Stints (tyre, laps)", "text"), ("Slower than the AI by", "delta")], rows)

section("How it learnt", "Average race time of the best tenth of each generation of strategies it tried. It starts by guessing "
        "and settles on what works.")
curve = pd.DataFrame({"Generation": np.arange(1, len(o["curve"]) + 1), "Time lost to tyres and stops (s)": o["curve"]})
st.altair_chart(dress(alt.Chart(curve).mark_line(point=True, color="#e10600", strokeWidth=3).encode(
    x="Generation:Q", y=alt.Y("Time lost to tyres and stops (s):Q", scale=alt.Scale(zero=False)))).properties(height=240),
    use_container_width=True)

key, label = ("vs_real", "Seconds faster than the real stops") if comparable else ("vs_fixed", "Seconds faster than the best fixed plan")
section("Race by race", f"{label} in each of the 400 races (right is better).")
g = pd.DataFrame({label: o["gains"][key]})
st.altair_chart(dress(alt.Chart(g).mark_bar(color="#e10600", opacity=.85).encode(
    x=alt.X(f"{label}:Q", bin=alt.Bin(maxbins=30)), y=alt.Y("count():Q", title="Races"))).properties(height=220),
    use_container_width=True)
left, right = st.columns([3, 2], vertical_alignment="center")
left.caption(f"The car races alone, so the AI ignores traffic, rivals' moves and track position, which real teams can't. "
             f"Built from the race's own tyre and pit data (pit loss {o['pit_loss']:.1f} s, about {o['sc_rate']:.1f} safety cars per race).")
right.page_link("app_pages/academy_m12.py", label="Learn it: Academy 12.7 Reinforcement learning",
                icon=":material/school:", query_params={"ch": "12.7"})
