"""Career Mode: from Formula 4 at 15 to Formula 1, one season at a time, on real seasons."""
import streamlit as st

import career_game as G
from style import stat_strip
from ui_kit import GOLD, GOOD, POOR, banner, board, section

KEY = "career"


def money(m):
    return f"{m:+.2f} M" if m else "±0"


c = st.session_state.get(KEY)

# ---------- start ----------
if c is None:
    st.markdown("You're 15, with a helmet, a family and some backing. Every season you pick a team and how hard to "
                "push. Each year is drawn from a real season of a driver in the same seat, so the ladder is as cruel "
                "here as it really is. Get the Super Licence points, impress the F1 teams, and keep the money from "
                "running out.")
    backing = st.radio("Your backing", list(G.BACKING), index=1, horizontal=True, key="career_backing")
    if st.button("Start your career", type="primary"):
        st.session_state[KEY] = G.new_career(backing)
        st.rerun()
    st.stop()

# ---------- where you are ----------
last_tier = c["f1_tier"] if c["series"] == "F1" else (c["history"][-1]["tier"] if c["history"] else None)
here = G.TIERS[last_tier] if last_tier else ""
stat_strip([
    ("Age", f"{c['age']}", f"season {c['year']}", True),
    ("Budget", f"{c['budget']:.2f} M", "junior programme pays most bills" if c["academy"] else "your own money and sponsors", False),
    ("Racing in", G.NAMES[c["series"]] if c["history"] else "—", here if c["history"] else "your first season is next", False),
    ("Super Licence", f"{G.sl_window(c):g}", f"points over three seasons (40 needed)", False),
])

last = c["history"][-1] if c["history"] else None
if last:
    tone = GOOD if last["pos"] <= 3 else (GOLD if last["pos"] <= 10 else POOR)
    extra = f" Scouts rated your F1 chances at {last['f1_chance']:.0%}." if "f1_chance" in last else ""
    wins = f"{last['wins']} win" + ("" if last["wins"] == 1 else "s")
    banner("🏁", f"{last['year']} {G.NAMES[last['series']]}: P{last['pos']}, {last['points']:g} points, {wins}",
           f"A season like {last['like']}. {last['note']}{extra} Money: {money(last['money'])}"
           + (f" · Super Licence +{last['sl']:g}" if last["sl"] else ""), tone)

# ---------- the end ----------
if c["over"]:
    s = G.summary(c)
    banner("🏆" if s["f1_seasons"] else "🧳", "Career over", c["over"], GOLD if s["f1_seasons"] else POOR)
    stat_strip([
        ("Formula 1", f"{s['f1_seasons']} seasons", f"about {s['f1_starts']} starts" if s["f1_seasons"] else "never started a Grand Prix", True),
        ("F1 wins", f"{s['f1_wins']}", f"{s['titles']} world titles", False),
        ("Junior titles", f"{s['junior_titles']}", "F4, F3 and F2 championships", False),
        ("Your hidden talent", f"{c['talent']:.2f}", "on a 0 to 1 scale; 0.5 is a typical driver here", False),
    ])
    if st.button("Start a new career", type="primary"):
        del st.session_state[KEY]
        st.rerun()

# ---------- an F1 offer ----------
elif c["offer"]:
    banner("📞", "A Formula 1 team is on the phone", f"A {G.TIERS[c['offer']].lower()} offers you a race seat for "
           f"{c['year']}, at {G.SALARY[c['offer']]:g} M a year.", GOOD)
    a, b = st.columns(2)
    if a.button("Sign the contract", type="primary", use_container_width=True):
        st.session_state[KEY] = G.accept_offer(c)
        st.rerun()
    if b.button("Turn it down and stay in F2", use_container_width=True):
        st.session_state[KEY] = {**c, "offer": None}
        st.rerun()

# ---------- choose next season ----------
else:
    section(f"Your {c['year']} season", "Front-running teams give you the best car and cost the most.")
    opts = G.options(c)
    labels = {o: (f"{G.NAMES[o[0]]} · {G.TIERS[o[1]]} · paid {o[2]:g} M" if o[0] == "F1"
                  else f"{G.NAMES[o[0]]} · {G.TIERS[o[1]]} · costs {o[2]:g} M") for o in opts}
    pick = st.radio("Seat", opts, format_func=labels.get, key=f"career_pick_{len(c['history'])}")
    push = st.toggle("Push hard all season (bigger wins, bigger crashes)", key=f"career_push_{len(c['history'])}")
    if st.button("Race the season", type="primary"):
        st.session_state[KEY] = G.next_season(c, pick[0], pick[1], push)
        st.rerun()

# ---------- the story so far ----------
if c["history"]:
    section("Your career so far")
    rows = []
    for h in reversed(c["history"]):
        rows.append({"colour": GOOD if h["pos"] <= 3 else (GOLD if h["pos"] <= 10 else POOR),
                     "cells": [(f"{h['year']} · {G.NAMES[h['series']]}", f"age {h['age']} · {G.TIERS[h['tier']].lower()}"
                                + (" · pushed" if h["push"] else "")),
                               f"P{h['pos']}", f"{h['points']:g}", f"{h['wins']}", (h["sl"], f"{h['sl']:g}" if h["sl"] else "–"),
                               (h["money"], money(h["money"]))]})
    board([("Season", "label"), ("Place", "num"), ("Points", "num"), ("Wins", "num"), ("SL points", "bar"),
           ("Money", "delta")], rows)
    if not c["over"] and st.button("Give up and start again"):
        del st.session_state[KEY]
        st.rerun()

