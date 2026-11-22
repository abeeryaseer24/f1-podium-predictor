"""Failure Watch: did a car's lap times show trouble before it retired?"""
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

import failure_watch as FW
from app_data import get_prepared_races
from charts import dress
from style import stat_strip
from ui_kit import board, section

TRADEOFF = Path(__file__).resolve().parent.parent / "data" / "processed" / "failure_tradeoff.csv"


@st.cache_data(ttl=86400, max_entries=40)
def analysis(folder):
    return FW.analyse(folder)


races = get_prepared_races()
seasons = sorted(races["season"].unique().tolist(), reverse=True)
c1, c2 = st.columns(2)
season = c1.selectbox("Season", seasons, key="fw_season")
in_season = races[races["season"] == season].sort_values("round")
names = {r.folder: f"Round {r.round} · {r.race_name}" for r in in_season.itertuples()}
folder = c2.selectbox("Race", list(names), index=len(names) - 1, format_func=names.get, key="fw_race")
a = analysis(folder)
drv = a["drivers"]
out = drv[drv["retired"]]
caught = out["warned_lap"].notna().sum()
stat_strip([
    ("Retirements", f"{len(out)}", "cars that didn't finish", True),
    ("Warned in advance", f"{caught} of {len(out)}", f"slow laps within {FW.HORIZON} laps of stopping", False),
    ("Warnings in this race", f"{sum(FW._runs(x) for x in drv['alerts'])}", "on all cars, including ones that finished", False),
])

if len(out):
    section("The cars that stopped", "Each retirement and whether its lap times warned of it first.")
    rows = []
    for _, r in out.sort_values("stop_lap").iterrows():
        rows.append({"colour": r["colour"], "cells": [
            (f"{r['code']} · {str(r['name']).title()}", r["team"]), (r["status"]),
            f"lap {int(r['stop_lap'])}",
            f"lap {int(r['warned_lap'])}" if pd.notna(r["warned_lap"]) else "no warning",
            (r["warning_laps"] if pd.notna(r["warning_laps"]) else -1,
             f"{int(r['warning_laps'])} laps ahead" if pd.notna(r["warning_laps"]) else "sudden")]})
    board([("Driver", "label"), ("Official reason", "text"), ("Stopped", "num"), ("First warning", "num"),
           ("Warning", "delta")], rows)

    section("Lap times before the stop", "How much slower than expected each retired car was, lap by lap "
            "(fuel and tyre age taken out). The dashed line is the warning level.")
    ids = out["driver_number"].tolist()
    lap_df = a["laps"][a["laps"]["driver_number"].isin(ids)].copy()
    who = dict(zip(drv["driver_number"], drv["code"]))
    lap_df["Driver"] = lap_df["driver_number"].map(who)
    colours = dict(zip(out["code"], out["colour"]))
    lines = alt.Chart(lap_df).mark_line(point=True, strokeWidth=2).encode(
        x=alt.X("lap:Q", title="Lap"), y=alt.Y("residual:Q", title="Slower than expected (s)", scale=alt.Scale(domain=[-3, 12], clamp=True)),
        color=alt.Color("Driver:N", scale=alt.Scale(domain=list(colours), range=list(colours.values())),
                        legend=alt.Legend(orient="top", title=None)),
        tooltip=["Driver", "lap", alt.Tooltip("residual:Q", format=".2f")])
    rule = alt.Chart(pd.DataFrame({"y": [FW.THRESHOLD]})).mark_rule(color="#e10600", strokeDash=[6, 4]).encode(y="y:Q")
    st.altair_chart(dress(lines + rule).properties(height=300), use_container_width=True)
else:
    st.caption("Every car finished this race.")

if TRADEOFF.exists():
    t = pd.read_csv(TRADEOFF)
    section("How good is it, honestly?", f"Over every race since 2023 ({int(t['retirements'].iloc[0])} retirements): a lower "
            "warning level catches more retirements but cries wolf more often.")
    rows = [{"colour": "#e10600" if abs(r.threshold - FW.THRESHOLD) < 1e-9 else "#8a8a96",
             "cells": [(f"{r.threshold:g} s slower", "used on this page" if abs(r.threshold - FW.THRESHOLD) < 1e-9 else ""),
                       (r.caught, f"{r.caught:.0%}"), (r.precision, f"{r.precision:.0%}"), (r.alerts_per_race, f"{r.alerts_per_race:.0f}")]}
            for r in t.itertuples()]
    board([("Warning level", "label"), ("Retirements caught", "bar"), ("Warnings that came true", "bar"),
           ("Warnings per race", "scale_low")], rows)
    st.caption("Lap times alone can't tell a failing car from one stuck in traffic or saving its tyres, so only a few "
               "warnings come true at any level, and crashes give no warning at all. Teams see hundreds of sensor channels "
               "that make this far easier.")
