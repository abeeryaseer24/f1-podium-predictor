"""Model Report Card: are the model's percentages worth trusting?"""
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

import report_card as R
from charts import dress, theme
from style import stat_strip
from ui_kit import GOOD, POOR, board, section

FILE = Path(__file__).resolve().parent.parent / "data" / "predictions" / "backtest_probs.csv"


@st.cache_data(ttl=600)
def load():
    return pd.read_csv(FILE) if FILE.exists() else pd.DataFrame()


probs = load()
if probs.empty:
    st.info("The report card is built after the next retrain.")
    st.stop()

seasons = sorted(probs["season"].unique().tolist())
choice = st.segmented_control("Seasons", ["All"] + [str(s) for s in seasons], default="All")
d = probs if choice in (None, "All") else probs[probs["season"] == int(choice)]

model_b = R.brier(d["podium_chance"], d["podium"])
grid_b = R.brier(d["grid_podium_chance"], d["podium"])
skill = R.skill(d["podium_chance"], d["grid_podium_chance"], d["podium"])
stat_strip([
    ("Podium Brier score", f"{model_b:.4f}", "0 is perfect; lower is better", True),
    ("Grid-only baseline", f"{grid_b:.4f}", "each grid slot's past podium rate", False),
    ("Skill vs the grid", f"{skill:+.1%}", "better than the baseline" if skill > 0 else "worse than the baseline", False),
    ("Predictions graded", f"{len(d):,}", f"{d[['season', 'round']].drop_duplicates().shape[0]} races, never seen in training", False),
])
st.caption("Every season was predicted by a model trained only on the seasons before it. "
           "The baseline knows only where each driver starts and how often that slot has reached the podium before.")

# ---------- calibration ----------
section("When the model says 30%, does it happen 30% of the time?",
        "Every podium chance, grouped into bands. On the diagonal is perfect; above it the model was too "
        "cautious, below it too confident. Bigger dots are bands with more predictions.")
text, grid, muted = theme()
cal = R.calibration(d["podium_chance"], d["podium"])
base_cal = R.calibration(d["grid_podium_chance"], d["podium"])
cal["Who"], base_cal["Who"] = "Model", "Grid baseline"
both = pd.concat([cal, base_cal])
diag = alt.Chart(pd.DataFrame({"x": [0, 1], "y": [0, 1]})).mark_line(strokeDash=[4, 4], color=muted).encode(
    x="x:Q", y="y:Q")
pts = alt.Chart(both).mark_line(point=alt.OverlayMarkDef(filled=True), strokeWidth=2).encode(
    x=alt.X("predicted:Q", title="Predicted podium chance", axis=alt.Axis(format="%"), scale=alt.Scale(domain=[0, 1])),
    y=alt.Y("happened:Q", title="How often it happened", axis=alt.Axis(format="%"), scale=alt.Scale(domain=[0, 1])),
    color=alt.Color("Who:N", scale=alt.Scale(domain=["Model", "Grid baseline"], range=["#e10600", "#8a8a96"]),
                    legend=alt.Legend(orient="top", title=None)),
    size=alt.Size("n:Q", legend=None, scale=alt.Scale(range=[30, 400])),
    tooltip=["Who", alt.Tooltip("predicted:Q", format=".0%"), alt.Tooltip("happened:Q", format=".0%"),
             alt.Tooltip("n:Q", title="Predictions")])
st.altair_chart(dress(diag + pts).properties(height=360), use_container_width=True)

# ---------- by season ----------
section("Season by season", "Brier score for podium chances (lower is better), against the grid baseline.")
table = R.by_season(probs)
board([("Season", "label"), ("Model", "scale_low"), ("Grid baseline", "scale_low"), ("Skill vs grid", "delta"),
       ("Log loss", "scale_low"), ("Winner Brier", "scale_low")],
      [{"colour": GOOD if r.skill > 0 else POOR,
        "cells": [(str(r.season), f"{r.races} races" + (" · so far" if r.season == table["season"].max() else "")),
                  (r.brier, f"{r.brier:.4f}"), (r.grid_brier, f"{r.grid_brier:.4f}"), (r.skill, f"{r.skill:+.1%}"),
                  (r.log_loss, f"{r.log_loss:.3f}"), (r.win_brier, f"{r.win_brier:.4f}")]}
       for r in table.itertuples()])
st.caption("Pills run green to red within each column (lower is better for every score). "
           "The edge is green where the model beat the grid baseline that season.")

# ---------- finish ranges ----------
section("How far off can a prediction be?", "For each predicted position, the range of real finishes that "
        "held 80% of the time in the test. The dot is the middle finish.")
ranges = R.finish_ranges(d)
ranges = ranges[ranges["predicted_position"] <= 20]
rule = alt.Chart(ranges).mark_rule(strokeWidth=6, color="#e10600", opacity=.35).encode(
    x=alt.X("predicted_position:O", title="Predicted position", axis=alt.Axis(labelAngle=0)),
    y=alt.Y("low:Q", title="Real finishing position", scale=alt.Scale(reverse=True, domain=[1, 22])), y2="high:Q",
    tooltip=[alt.Tooltip("predicted_position:O", title="Predicted"), alt.Tooltip("low:Q", title="From"),
             alt.Tooltip("high:Q", title="To"), alt.Tooltip("n:Q", title="Cases")])
mid = alt.Chart(ranges).mark_point(filled=True, size=60, color="#e10600").encode(
    x="predicted_position:O", y="median:Q")
st.altair_chart(dress(rule + mid).properties(height=320), use_container_width=True)
p1 = ranges[ranges["predicted_position"] == 1]
p10 = ranges[ranges["predicted_position"] == 10]
if len(p1) and len(p10):
    st.caption(f"A driver predicted to win finished between P{int(p1['low'].iloc[0])} and P{int(p1['high'].iloc[0])} "
               f"80% of the time. One predicted P10: between P{int(p10['low'].iloc[0])} and P{int(p10['high'].iloc[0])}.")

with st.expander("What these scores mean"):
    st.markdown(f"""
- **Brier score.** For every driver in every race, take the model's podium chance, subtract 1 if
  they made the podium (0 if not), square it, and average. Always guessing the average rate
  (3 in {probs.groupby(['season', 'round']).size().mean():.0f}) scores about 0.13. Perfect is 0.
- **Log loss.** Like Brier, but a confident miss (95% on someone who finishes 12th) costs much more.
- **Skill vs the grid.** 1 − (model's Brier ÷ baseline's Brier). +5% means the model's chances
  are 5% closer to reality than the baseline's. Below zero, the baseline did better.
- **Honest reading.** Qualifying already tells you most of what happens on Sunday, so the
  baseline is hard to beat. The model's edge over it is small and not there every season.
""")
