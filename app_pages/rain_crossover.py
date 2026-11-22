"""Rain Crossover: in mixed-weather races, when slicks became faster than intermediates (or the other way),
and who switched at the right moment."""
import altair as alt
import pandas as pd
import streamlit as st

import crossover as X
from app_data import get_race_info
from charts import dress
from style import stat_strip
from ui_kit import board, section

COLOURS = {"Wet tyres": "#1fd6a0", "Slicks": "#e8b33a"}


@st.cache_data(ttl=86400)
def races():
    return X.mixed_races()


@st.cache_data(ttl=86400, max_entries=30)
def analysis(folder):
    return X.analyse(folder)


folders = races()
if not folders:
    st.info("No race run partly in the wet has been prepared yet.")
    st.stop()
names = {f: f"{get_race_info(f)['race_name']} {get_race_info(f)['season']}" for f in folders}
folder = st.selectbox("Mixed-weather race", folders[::-1], format_func=names.get, key="rc_race")
a = analysis(folder)
sw = a["switches"]
cross = a["crossings"]

late = sw.dropna(subset=["laps_off"]) if len(sw) else sw
best_call = late.loc[late["laps_off"].abs().idxmin()] if len(late) else None
stat_strip([
    ("Crossovers", f"{len(cross)}", ", ".join(f"lap {c['lap']} to {c['to'].lower()}" for c in cross) or "none found", True),
    ("Tyre switches", f"{len(sw)}", "between wet tyres and slicks", False),
    ("Laps with rain", f"{len(a['rain_laps'])}", "from the circuit's weather station", False),
    ("Best-timed switch", best_call["code"] if best_call is not None else "–",
     (f"lap {int(best_call['lap'])}, {abs(int(best_call['laps_off']))} lap{'s' if abs(int(best_call['laps_off'])) != 1 else ''} "
      f"{'late' if best_call['laps_off'] > 0 else 'early' if best_call['laps_off'] < 0 else 'off'}") if best_call is not None else "", False),
])

section("Wet tyres against slicks, lap by lap", "Median lap time of the cars on each kind of tyre (clean laps only). "
        "Blue bands mark rain at the circuit; the red lines are crossovers (dashed where estimated).")
# Every lap, so a tyre with no cars on it shows a gap in its line instead of a straight join
full = a["laps"].set_index("lap_number").reindex(range(1, int(a["laps"]["lap_number"].max()) + 1)).reset_index()
full = full.rename(columns={"index": "lap_number"})
laps = full.melt(id_vars="lap_number", value_vars=["Wet tyres", "Slicks"], var_name="Tyres", value_name="Lap time (s)")
layers = []
if a["rain_laps"]:
    layers.append(alt.Chart(pd.DataFrame({"lap": a["rain_laps"], "lap2": [l + 1 for l in a["rain_laps"]]})).mark_rect(
        color="#2b6cff", opacity=.12).encode(x="lap:Q", x2="lap2:Q"))
layers.append(alt.Chart(laps).mark_line(point=True, strokeWidth=2.5).encode(
    x=alt.X("lap_number:Q", title="Lap"), y=alt.Y("Lap time (s):Q", scale=alt.Scale(zero=False)),
    color=alt.Color("Tyres:N", scale=alt.Scale(domain=list(COLOURS), range=list(COLOURS.values())),
                    legend=alt.Legend(orient="top", title=None)),
    tooltip=["Tyres", "lap_number", alt.Tooltip("Lap time (s):Q", format=".2f")]))
if cross:
    cdf = pd.DataFrame(cross)
    cdf["kind"] = cdf["measured"].map({True: "measured", False: "estimated"})
    layers.append(alt.Chart(cdf).mark_rule(color="#e10600", strokeWidth=2).encode(
        x="lap:Q", strokeDash=alt.condition(alt.datum.measured, alt.value([1, 0]), alt.value([6, 4])),
        tooltip=["lap", "to", "kind"]))
st.altair_chart(dress(alt.layer(*layers)).properties(height=320), use_container_width=True)
if any(not c["measured"] for c in cross):
    st.caption("Dashed: the two kinds of tyre never ran clean laps side by side, so the crossover is estimated as the lap "
               "by which half the field had switched.")

if len(sw):
    section("Who switched when", "Each tyre change against the nearest crossover the same way. Green is close to it, red far off.")
    rows = []
    for _, r in sw.sort_values("lap").iterrows():
        off = r["laps_off"]
        txt = "–" if pd.isna(off) else ("on the lap" if off == 0 else f"{abs(int(off))} {'late' if off > 0 else 'early'}")
        rows.append({"colour": r["colour"], "cells": [
            (r["code"], r["team"]), f"lap {int(r['lap'])}", (COLOURS[r["to"]], f"to {r['to'].lower()}"),
            f"lap {int(r['crossover'])}" if pd.notna(r["crossover"]) else "–",
            (abs(off) if pd.notna(off) else 0, txt),
            f"≈ {r['cost']:.0f} s" if pd.notna(r["cost"]) and r["cost"] else "–"]})
    board([("Driver", "label"), ("Switched", "num"), ("To", "tag"), ("Crossover", "num"), ("Timing", "scale_low"),
           ("Time on the wrong tyre", "num")], rows)
st.caption("Time on the wrong tyre is only given where the crossover was measured: the gap between the two groups on "
           "the laps between the switch and the crossover.")
