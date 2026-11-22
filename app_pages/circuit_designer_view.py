"""Circuit Designer: draw your own circuit and the lap simulator drives it as you draw."""
import statistics
from dataclasses import replace

import streamlit as st

import app_sim as A
import lapsim
from circuit_designer import designer

cal = A.get_calibration()
seasons = sorted({int(f[:4]) for f, c in cal.items() if c.get("usable")}, reverse=True)
season = st.selectbox("Car", seasons, format_func=lambda s: f"A typical {s} car", key="cd_season")
cars = [c["car"] for f, c in cal.items() if f.startswith(str(season)) and c.get("usable")]
typical = replace(lapsim.Car(), **{k: statistics.median(c[k] for c in cars)
                                   for k in ("mass", "power_kw", "wing", "grip")})

designer(typical, dark=st.session_state.dark)
st.caption(f"The car is the middle of every {season} car calibrated to a real circuit: {typical.power_kw:.0f} kW at the "
           f"wheels, {typical.mass:.0f} kg, grip {typical.grip:.2f}. So a lap here compares with the real circuits in the "
           "Lap Simulator. Flat ground, no kerbs and no DRS. The physics are explained in the Engineering Academy "
           "(Module 3, the lap simulator built step by step).")
