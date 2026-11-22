"""Race Director: real incidents from race control. Make the stewards' call, then see what they decided."""
import numpy as np
import pandas as pd
import streamlit as st

import stewards as S
from style import stat_strip
from ui_kit import GOOD, POOR, board, chips, section

ROUND = 8
LEVEL = {c: k for k, c in enumerate(S.CHOICES)}


@st.cache_data(ttl=86400)
def incidents():
    return S.all_incidents()


df = incidents()
if df.empty:
    st.info("No incidents with a decision have been found yet.")
    st.stop()

reasons = ["Any"] + df["reason"].value_counts().index.tolist()
c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
reason = c1.selectbox("Kind of incident", reasons, key="rd_reason")
pool = df if reason == "Any" else df[df["reason"] == reason]
if c2.button("New set of incidents", use_container_width=True, key="rd_new") or "rd_set" not in st.session_state \
        or st.session_state.get("rd_for") != reason:
    st.session_state["rd_set"] = pool.sample(min(ROUND, len(pool)), random_state=np.random.randint(1e9)).index.tolist()
    st.session_state["rd_for"] = reason
    st.session_state["rd_round"] = st.session_state.get("rd_round", 0) + 1
    st.session_state["rd_done"] = False
chosen = df.loc[st.session_state["rd_set"]]
rnd = st.session_state["rd_round"]

section("Your calls", "Each one really happened. Read it, then choose what you'd have done as a steward.")
answers = {}
for i, (idx, r) in enumerate(chosen.iterrows(), start=1):
    with st.container(border=True):
        st.markdown(f"**{i}. {r['race']}** · lap {r['lap'] if pd.notna(r['lap']) else '–'}")
        st.markdown(r["incident"])
        chips([(r["reason"], "#e8b33a")])
        answers[idx] = st.radio("Your decision", S.CHOICES, index=None, horizontal=True, key=f"rd_{rnd}_{idx}",
                                label_visibility="collapsed")
        if st.session_state.get("rd_done"):
            right = answers[idx] == r["decision"]
            who = f" for {r['penalised']}" if pd.notna(r.get("penalised")) and r.get("penalised") else ""
            mark = "⚪" if answers[idx] is None else ("✅" if right else "❌")
            st.markdown(f"{mark} The stewards: **{r['decision']}{who}**")

if st.button("Reveal the stewards' decisions", type="primary", key=f"rd_reveal_{rnd}"):
    st.session_state["rd_done"] = True
    st.rerun()

if st.session_state.get("rd_done"):
    given = [(answers[i], chosen.at[i, "decision"]) for i in chosen.index if answers[i]]
    score = sum(a == b for a, b in given)
    strict = np.mean([LEVEL[a] - LEVEL[b] for a, b in given]) if given else 0
    stat_strip([
        ("Matched the stewards", f"{score} of {len(chosen)}", "exact same decision", True),
        ("Your style", ("Stricter" if strict > 0.25 else "More lenient" if strict < -0.25 else "Spot on") if given else "–",
         "than the real stewards, on average" if given else "answer some incidents first", False),
    ])

section("How the stewards rule", "Every decided incident since 2023, by kind. Bars show the share of each decision.")
rows = []
for why, g in df.groupby("reason"):
    if len(g) < 6:
        continue
    share = g["decision"].value_counts(normalize=True)
    rows.append({"colour": GOOD if share.get(S.CHOICES[0], 0) > 0.5 else POOR,
                 "cells": [(why, f"{len(g)} incidents"), *[(share.get(c, 0), f"{share.get(c, 0):.0%}") for c in S.CHOICES]]})
rows.sort(key=lambda r: -r["cells"][1][0])
board([("Incident", "label"), *[(c, "bar") for c in S.CHOICES]], rows)
st.caption("From OpenF1's race-control feed. Incidents investigated after the race are left out, because their decisions "
           "aren't in the feed. Green edge: usually no action; red: usually a penalty.")
