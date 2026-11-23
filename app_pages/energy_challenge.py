"""Energy Challenge: set a deploy window on every straight and beat the engineer's lap. A leaderboard per circuit."""
import numpy as np
import streamlit as st
import streamlit.components.v1 as components

import app_sim as A
import energy_game as G
import picks
from scene_env import env_for
from sim3d import lap_view
from style import stat_strip
from ui_kit import GOLD, GOOD, banner, board, section

COOKIE = "pp_player"
PHASE_COLOURS = {"deploy": "#1fd6a0", "harvest": "#2b6cff", "clip": "#e4544a", "engine": "#8a8a96"}
PHASE_LEGEND = [("Deploying", "#1fd6a0"), ("Harvesting", "#2b6cff"), ("Battery empty (clipping)", "#e4544a"),
                ("Engine only", "#8a8a96")]
MEDALS = {"gold": ("🥇", "Gold", "You matched or beat the engineer. Post it to the board.", GOLD),
          "silver": ("🥈", "Silver", "Within a tenth of the engineer.", "#c0c0c8"),
          "bronze": ("🥉", "Bronze", "Quicker than deploying everywhere. The engineer is still ahead.", "#cd7f32")}


def player():
    if "player" not in st.session_state:
        st.session_state.player = picks.clean_code(st.context.cookies.get(COOKIE)) or picks.new_player_code()
    return st.session_state.player


@st.cache_resource(max_entries=40)
def setup(folder):
    return G.setup(folder, A.get_track(folder))


@st.cache_data(ttl=3600, max_entries=500)
def run(folder, mode, plan):
    car, track, pu = setup(folder)
    return G.lap(car, track, pu, None if plan is None else [list(w) for w in plan], mode)


@st.cache_data(ttl=24 * 3600, max_entries=60)
def engineer(folder, mode):
    """From the precomputed file, or searched now for a circuit the robot hasn't reached yet."""
    stored = G.load_par().get(folder, {}).get("engineer", {}).get(mode)
    if stored:
        return stored["time"], stored["plan"]
    car, track, pu = setup(folder)
    return G.par(car, track, pu, mode)


@st.cache_data(ttl=30)
def leaderboard(folder, mode):
    return G.scores(folder, mode)


folder = A.pick_race("energy_ch")
mode = st.radio("Lap", G.MODES, horizontal=True, key="ec_mode",
                format_func={"qualifying": "Qualifying (start with a full battery)",
                             "race": "Race (spend only what you harvest)"}.get)

base = run(folder, mode, None)
zones = base["straights"]
key = f"ec_{folder}_{mode}"

# ---------- your plan ----------
section("Your deploy plan", "Drag each straight's window: the motor helps only between the two handles.")
def reset(to):
    for k in range(len(zones)):
        st.session_state[f"{key}_{k}"] = tuple(int(round(x * 100)) for x in to[k])
b1, b2, _ = st.columns([1.5, 1, 2.5])
b1.button("Deploy everywhere", on_click=reset, args=([(0, 1)] * len(zones),), use_container_width=True, key=f"{key}_all")
b2.button("Nothing", on_click=reset, args=([(0, 0)] * len(zones),), use_container_width=True, key=f"{key}_none")
cols = st.columns(2)
plan = []
for k, (_, _, s, e) in enumerate(zones):
    st.session_state.setdefault(f"{key}_{k}", (0, 100))
    lo, hi = cols[k % 2].slider(f"S{k + 1} · {int(e - s):,} m", 0, 100, step=int(G.STEP * 100),
                                format="%d%%", key=f"{key}_{k}")
    plan.append((lo / 100, hi / 100))
plan = tuple(plan)

yours = run(folder, mode, plan)
par_time, par_plan = engineer(folder, mode)
t, everywhere = yours["lap_time"], base["lap_time"]
got = G.medal(t, everywhere, par_time)
stat_strip([
    ("Your lap", A.lap_str(t), f"{t - everywhere:+.3f} s on deploying everywhere", True),
    ("Deploy everywhere", A.lap_str(everywhere), "beat it for bronze", False),
    ("The engineer", A.lap_str(par_time), f"you are {t - par_time:+.3f} s", False),
    ("Battery empty", f"{yours['clip_share']:.0%}", "of your deploy zones (clipping)", False),
])
if got:
    banner(*MEDALS[got])

# ---------- the lap ----------
track = A.get_track(folder)
ghost = "#f5f5f7" if st.session_state.dark else "#15151e"
def car_of(r, name, colour):
    return {"name": name, "colour": colour, "t": np.r_[r["time"], r["lap_time"]],
            "s": np.r_[r["s"], r["s"][-1] + (r["s"][1] - r["s"][0])]}
labels = A.corner_labels(folder, track) + [
    {"text": f"S{k + 1}", "i": int((i + j) / 2) // A.THREE_EVERY, "kind": "corner"} for k, (i, j, _, _) in enumerate(zones)]
lap_view(A.three_track(track, [PHASE_COLOURS[p] for p in yours["phase"]], PHASE_LEGEND),
         [car_of(yours, "YOU", "#e10600"), car_of(base, "ALL", ghost)],
         labels=labels, dark=st.session_state.dark, env=env_for(folder), height=440)

# ---------- post it ----------
section("Leaderboard", "Each player's best lap on this circuit. Laps are recomputed from the plan, so they can't be faked.")
me = player()
c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
nick = c1.text_input("Name on the board", max_chars=20, key="ec_nick", placeholder="Anonymous")
if c2.button("Post my lap", type="primary", use_container_width=True, key=f"{key}_post"):
    try:
        saved = G.save_score(me, folder, mode, t, plan, nick)
        leaderboard.clear()
        st.toast("Posted." if saved else "Your best here is already quicker; the board keeps that one.")
        if picks.clean_code(st.context.cookies.get(COOKIE)) != me:
            components.html(f"<script>document.cookie = '{COOKIE}={me}; path=/; max-age=63072000; SameSite=Lax';</script>",
                            height=0)
    except Exception as error:
        st.warning(picks.describe_error(error, G.TABLE))

try:
    rows = leaderboard(folder, mode)
except Exception as error:
    rows = []
    st.warning(picks.describe_error(error, G.TABLE))
board_rows = [{"colour": "#e10600" if r["player"] == me else None,
               "cells": [(r.get("nickname") or "Anonymous", "you" if r["player"] == me else ""), A.lap_str(r["lap_time"]),
                         (round((par_time - r["lap_time"]) * 1000), f"{(r['lap_time'] - par_time):+.3f} s"),
                         {"gold": "🥇", "silver": "🥈", "bronze": "🥉"}.get(G.medal(r["lap_time"], everywhere, par_time), "")]}
              for r in rows[:10]]
board_rows.append({"colour": GOOD, "cells": [("The engineer", "our search"), A.lap_str(par_time), (0, "±0.000 s"), "🥇"]})
board_rows.sort(key=lambda r: r["cells"][2][0], reverse=True)
board([("Driver", "label"), ("Lap", "num"), ("To the engineer", "delta"), ("", "text")], board_rows, ranked=True)

with st.expander("Show the engineer's plan"):
    st.caption("Found by moving each window's ends a step at a time and keeping every change that helps: "
               "good, not provably the best, so it can be beaten.")
    board([("Straight", "label"), ("Deploy from", "num"), ("to", "num")],
          [{"colour": "#1fd6a0", "cells": [(f"S{k + 1}", f"{int(zones[k][3] - zones[k][2]):,} m"),
                                           f"{a:.0%}", f"{b:.0%}"]} for k, (a, b) in enumerate(par_plan)])
    st.button("Load it", on_click=reset, args=(par_plan,), key=f"{key}_load")

st.caption("A 2026 car (active aero on) on this circuit's calibrated chassis; teaching model with rounded public "
           "power-unit figures. How deployment works is in the Engineering Academy's power unit module.")
