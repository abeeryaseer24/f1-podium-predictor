"""Guess the Driver: two teammates' laps from the same race. Which one is whose? Then see the AI's call."""
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import driving_style as DS
from charts import dress
from style import stat_strip
from ui_kit import GOOD, POOR, board, chips, section

ROUND = 5
COL_A, COL_B = "#e10600", "#27f4d2"


@st.cache_data(ttl=86400)
def load():
    return DS.load_model(), pd.read_parquet(DS.GAME_LAPS)


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


def first_name(code):
    return str(model["names"].get(code, code)).split(" ")[0].title()


def full_name(code):
    parts = str(model["names"].get(code, code)).split(" ")
    return " ".join([parts[0].title(), *[p.title() for p in parts[1:]]])


def tell(code, top=3):
    """'brakes later, smoother on the throttle' from the driver's strongest habits vs teammates."""
    sig = model["signatures"].get(code)
    if not sig:
        return "not enough laps to say"
    words = [DS.WORDS[h["feature"]][0 if h["z"] > 0 else 1] for h in sig["habits"][:top] if abs(h["z"]) >= 0.15]
    return ", ".join(words) if words else "no strong habits: drives a lot like their teammates"


def pick_rounds(pool, n, seed):
    """n team-races with one lap from each driver, on the same tyre when possible."""
    rng = np.random.default_rng(seed)
    keys = pool[["folder", "team"]].drop_duplicates().to_numpy().tolist()
    rng.shuffle(keys)
    rounds = []
    for folder, team in keys[:n]:
        grp = pool[(pool["folder"] == folder) & (pool["team"] == team)]
        drivers = sorted(grp["driver"].unique())
        laps = {d: grp[grp["driver"] == d] for d in drivers}
        pair = None
        for _, la in laps[drivers[0]].iterrows():
            same = laps[drivers[1]][laps[drivers[1]]["compound"] == la["compound"]]
            if len(same):
                pair = (la.name, same.index[0])
                break
        if pair is None:
            pair = (laps[drivers[0]].index[0], laps[drivers[1]].index[0])
        if rng.random() < 0.5:
            pair = pair[::-1]
        rounds.append(pair)
    return rounds


def traces(row_a, row_b):
    """Long table of both laps on the distance grid."""
    out = []
    for label, r in (("Lap A", row_a), ("Lap B", row_b)):
        dist = np.linspace(0, r["length"], len(r["speed"])) / 1000
        out.append(pd.DataFrame({"km": dist, "Speed": r["speed"], "Throttle": r["throttle"],
                                 "Brake": np.array(r["brake"]) * 100, "Lap": label}))
    return pd.concat(out, ignore_index=True)


def lap_charts(row_a, row_b, key):
    t = traces(row_a, row_b)
    colours = alt.Scale(domain=["Lap A", "Lap B"], range=[COL_A, COL_B])
    speed = alt.Chart(t).mark_line(strokeWidth=1.6).encode(
        x=alt.X("km:Q", title=None, axis=alt.Axis(labels=False)), y=alt.Y("Speed:Q", title="Speed (km/h)"),
        color=alt.Color("Lap:N", scale=colours, legend=alt.Legend(orient="top", title=None)),
        tooltip=["Lap", alt.Tooltip("km:Q", format=".2f"), "Speed"])
    st.altair_chart(dress(speed).properties(height=210), use_container_width=True, key=f"{key}_s")
    for pedal, height, last in (("Throttle", 90, False), ("Brake", 60, True)):
        chart = alt.Chart(t).mark_line(strokeWidth=1.2, interpolate="step-after" if pedal == "Brake" else "linear").encode(
            x=alt.X("km:Q", title="Distance round the lap (km)" if last else None, axis=alt.Axis(labels=last)),
            y=alt.Y(f"{pedal}:Q", title=f"{pedal} (%)", axis=alt.Axis(values=[0, 100])),
            color=alt.Color("Lap:N", scale=colours, legend=None),
            tooltip=["Lap", alt.Tooltip("km:Q", format=".2f"), pedal])
        st.altair_chart(dress(chart).properties(height=height), use_container_width=True, key=f"{key}_{pedal}")


def model_call(row_a, row_b, a):
    """P(Lap A is driver a), from the model that never saw this race, and the habits it leaned on."""
    p = float(sigmoid(row_a["oof_score_a"] - row_b["oof_score_a"]))
    b = [d for d in (row_a["driver"], row_b["driver"]) if d != a][0]
    classes = model["classes"]
    reasons = []
    if a in classes and b in classes:
        w = np.array(model["coef"][classes.index(a)]) - np.array(model["coef"][classes.index(b)])
        for k, f in enumerate(model["features"]):
            xa = (row_a[f] - model["mu"][f]) / model["sd"][f]
            xb = (row_b[f] - model["mu"][f]) / model["sd"][f]
            reasons.append((f, w[k] * (xa - xb)))
    lean = 1 if p >= 0.5 else -1
    reasons = sorted([r for r in reasons if r[1] * lean > 0], key=lambda r: -abs(r[1]))[:2]
    return p, reasons


try:
    model, game = load()
except FileNotFoundError:
    st.info("The driving-style model hasn't been built yet.")
    st.stop()

# ---------- the controls ----------

seasons = ["Any"] + sorted(game["season"].unique().tolist(), reverse=True)
teams = ["Any"] + sorted(game["team"].unique().tolist())
c1, c2, c3 = st.columns([1, 2, 1], vertical_alignment="bottom")
season = c1.selectbox("Season", seasons, key="gd_season")
team = c2.selectbox("Team", teams, key="gd_team")
pool = game if season == "Any" else game[game["season"] == season]
pool = pool if team == "Any" else pool[pool["team"] == team]
want = (season, team)
if pool.empty:
    st.info("No laps for that choice yet.")
    st.stop()
if c3.button("New set of laps", use_container_width=True, key="gd_new") or "gd_set" not in st.session_state \
        or st.session_state.get("gd_for") != want:
    st.session_state["gd_set"] = pick_rounds(pool, ROUND, np.random.randint(1e9))
    st.session_state["gd_for"] = want
    st.session_state["gd_round"] = st.session_state.get("gd_round", 0) + 1
    st.session_state["gd_done"] = False
rounds = st.session_state["gd_set"]
rnd = st.session_state["gd_round"]
done = st.session_state.get("gd_done", False)

section("Whose lap is it?", "Each pair is two teammates in the same race: same car, same day, usually the same tyre. "
        "The traces and the habits are your clues. The AI gets the same laps, from races it never trained on.")

answers, results = {}, []
for i, (ia, ib) in enumerate(rounds, start=1):
    ra, rb = game.loc[ia], game.loc[ib]
    a, b = sorted([ra["driver"], rb["driver"]])
    with st.container(border=True):
        st.markdown(f"**{i}. {ra['race_name']} {int(ra['season'])}** · {ra['team']}")
        chips([(f"Lap A · lap {int(ra['lap'])} · {DS.lap_clock(ra['lap_time'])}", COL_A),
               (f"Lap B · lap {int(rb['lap'])} · {DS.lap_clock(rb['lap_time'])}", COL_B),
               (str(ra["compound"]).title() if ra["compound"] == rb["compound"] else
                f"{str(ra['compound']).title()} vs {str(rb['compound']).title()}", "#8a8a96")])
        lap_charts(ra, rb, f"gd_{rnd}_{i}")
        diffs = sorted(DS.FEATURES, key=lambda f: -abs((ra[f] - rb[f]) / model["sd"][f]))[:4]
        board([("Habit, against the team's average", "label"), ("Lap A", "num"), ("Lap B", "num")],
              [{"colour": ra["colour"], "cells": [(DS.FEATURES[f], ""), DS.show(f, ra[f]), DS.show(f, rb[f])]}
               for f in diffs])
        st.caption(f"What we know: **{full_name(a)}** {tell(a)}. **{full_name(b)}** {tell(b)}.")
        choice = st.radio("Lap A was driven by", [full_name(a), full_name(b)], index=None, horizontal=True,
                          key=f"gd_{rnd}_{i}")
        answers[i] = choice
        truth = full_name(ra["driver"])
        p_a, reasons = model_call(ra, rb, a)
        ai_pick = a if p_a >= 0.5 else b
        ai_conf = max(p_a, 1 - p_a)
        results.append({"you": None if choice is None else choice == truth, "ai": full_name(ai_pick) == truth})
        if done:
            mark = "⚪" if choice is None else ("✅" if choice == truth else "❌")
            ai_mark = "✅" if full_name(ai_pick) == truth else "❌"
            st.markdown(f"{mark} Lap A was **{truth}**, Lap B was **{full_name(rb['driver'])}**.")
            why = "; ".join(f"{DS.FEATURES[f].lower()}" for f, _ in reasons) or "nothing stood out"
            st.markdown(f"{ai_mark} The AI said Lap A was **{full_name(ai_pick)}** ({ai_conf:.0%} sure). "
                        f"It leaned most on: {why}.")

if st.button("Reveal who drove", type="primary", key=f"gd_reveal_{rnd}"):
    st.session_state["gd_done"] = True
    st.rerun()

if done:
    answered = [r for r in results if r["you"] is not None]
    you = sum(r["you"] for r in answered)
    ai = sum(r["ai"] for r in results)
    stat_strip([
        ("You", f"{you} of {len(rounds)}", "laps named correctly" if answered else "answer some pairs first", True),
        ("The AI", f"{ai} of {len(rounds)}", "on races it never trained on", False),
        ("A coin", f"{len(rounds) / 2:g} of {len(rounds)}", "what guessing gets on average", False),
    ])

# ---------- how good is it ----------

score = model["score"]
section("How good is the AI, honestly?", f"Tested on {score['races']} whole races it never saw, "
        f"{score['laps']:,} laps in all. Each lap is a two-way choice between teammates, so a coin gets 50%.")
stat_strip([
    ("One lap", f"{score['lap_accuracy']:.0%}", "teammate named correctly from a single lap", True),
    ("A whole race", f"{score['race_accuracy']:.0%}", "when it votes over all of a driver's laps", False),
    ("Guessing", "50%", "a coin flip", False),
])
rows = [{"colour": model["teams"].get(next((d for d, t in model["teams"].items() if t["team"] == tm), ""), {}).get("colour"),
         "cells": [(tm, f"{v['laps']:,} laps"), (v["accuracy"], f"{v['accuracy']:.0%}")]}
        for tm, v in score["by_team"].items() if v["laps"] >= 40]
board([("Team", "label"), ("Single laps named correctly", "bar")], rows)

section("Every driver's tell", "The habits that most set each driver apart from their teammates, "
        "averaged over every clean lap since 2023.")
rows = []
for code, sig in sorted(model["signatures"].items(), key=lambda kv: model["teams"].get(kv[0], {}).get("team", "")):
    if sig["laps"] < 60:
        continue
    t = model["teams"].get(code, {})
    top = sig["habits"][0]
    rows.append({"colour": t.get("colour"), "cells": [
        (full_name(code), t.get("team", "")), tell(code),
        (abs(top["z"]), f"{abs(top['z']):.1f} σ"), f"{sig['laps']:,}"]})
board([("Driver", "label"), ("Compared with their teammates", "text"), ("Strongest tell", "bar"), ("Laps", "num")], rows)

st.caption("How it works: OpenF1's car data (speed, throttle, brake, gear, rpm, about four samples a second) for up to "
           "12 clean racing laps per driver per race. Sixteen habits are measured on each lap, then compared with the "
           "team's own average for that race, so the car, the circuit and the weather cancel out. A logistic regression "
           "learns each driver's pattern. What it can't do: four samples a second blurs braking points by about 20 m, "
           "steering isn't in the public data, and some 'habits' are really pace: the faster teammate carries more speed. "
           "A driver with few laps, or one who changed team, is harder to read.")
