"""Pit Crew: run a pit stop yourself and see where your time ranks among the real stops."""
import streamlit as st

import pit_crew as P
from ui_kit import board, section


@st.cache_data(ttl=86400)
def data():
    return P.stats()


d = data()
P.game(d, dark=st.session_state.dark)
st.caption("Keys: space for Start, GO and RELEASE; 1–4 (or Q W A S) for the four wheels. On a phone, tap the buttons "
           "and the wheels.")

section(f"How the teams do it, {d['season']}", "Each team's typical stationary time and its best, from every stop "
        "OpenF1 timed this season.")
board([("Team", "label"), ("Typical stop", "scale_low"), ("Best", "num")],
      [{"colour": t["colour"], "cells": [(t["team"], f"{t['stops']} stops"), (t["median"], f"{t['median']:.2f} s"),
                                         f"{t['best']:.2f} s"]} for t in d["teams"]], ranked=True)
st.caption(f"Stationary times from OpenF1's pit data, {d['count']:,} stops in all (it times the stop only in recent "
           f"seasons); stops over {P.STOP_MAX:g} s are left out as repairs or penalties. In the game the crews take "
           "1.5 to 2 s per wheel, roughly what the best real crews manage; the rest is your reactions.")
