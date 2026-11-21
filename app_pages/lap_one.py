"""Lap One: places gained and lost between the grid and the end of the first lap."""
import altair as alt
import pandas as pd
import streamlit as st

import race_story as R
from charts import dress, theme
from style import stat_strip
from ui_kit import GOOD, POOR, diverge, section, sheet

MIN_STARTS = 10


@st.cache_data(ttl=600)
def starts():
    return R.all_lap_ones()


data = starts()
if data.empty:
    st.info("No races prepared yet.")
    st.stop()

c1, c2 = st.columns(2)
seasons = ["All seasons"] + sorted(data["season"].unique().tolist(), reverse=True)
season = c1.selectbox("Season", seasons)
places = ["Every circuit"] + sorted(data["location"].unique().tolist())
place = c2.selectbox("Circuit", places)
d = data.copy()
if season != "All seasons":
    d = d[d["season"] == season]
if place != "Every circuit":
    d = d[d["location"] == place]
if d.empty:
    st.info("No starts match.")
    st.stop()

# What a car usually gains from each grid slot, over everything we have: the fair yardstick
slot_mean = data.groupby("grid")["gained"].mean()
d["vs_expected"] = d["gained"] - d["grid"].map(slot_mean)

races_n = d[["season", "round"]].drop_duplicates().shape[0]
moved = (d["gained"] != 0).mean()
pole_side = d[d["grid"] % 2 == 1]["gained"].mean()
other_side = d[d["grid"] % 2 == 0]["gained"].mean()
stat_strip([
    ("Starts", f"{len(d)}", f"in {races_n} races", True),
    ("Changed position", f"{moved:.0%}", "of cars by the end of lap 1", False),
    ("Biggest gain", f"+{d['gained'].max()}", "places on one opening lap", False),
    ("Odd vs even grid slots", f"{pole_side:+.2f} / {other_side:+.2f}", "average places gained", False),
])

# ---------- by grid slot ----------
section("Where you start, what you gain", "Average places gained on lap 1 from each grid slot. "
        "Front-runners can only lose places, back-markers can only gain, so the pattern is partly arithmetic.")
by_slot = d.groupby("grid").agg(gained=("gained", "mean"), n=("gained", "size")).reset_index()
by_slot["colour"] = by_slot["gained"].map(lambda v: GOOD if v >= 0 else POOR)
text, grid_c, muted = theme()
chart = alt.Chart(by_slot).mark_bar(cornerRadius=3).encode(
    x=alt.X("grid:O", title="Grid slot", axis=alt.Axis(labelAngle=0)),
    y=alt.Y("gained:Q", title="Average places gained"),
    color=alt.Color("colour:N", scale=None),
    tooltip=[alt.Tooltip("grid:O", title="Grid"), alt.Tooltip("gained:Q", format="+.2f", title="Places gained"),
             alt.Tooltip("n:Q", title="Starts")])
st.altair_chart(dress(chart).properties(height=280), use_container_width=True)
st.caption("Odd slots (1, 3, 5…) are on the same side of the grid as pole, usually the racing line. "
           "Whether that side is cleaner varies by circuit; pick one above to see.")

# ---------- drivers ----------
section("The best starters", f"Places gained on lap 1 compared with what the average car gains from the same grid "
        f"slot, per start. Drivers with at least {MIN_STARTS} starts in this selection.")
by_driver = d.groupby(["code", "name"]).agg(score=("vs_expected", "mean"), n=("gained", "size"),
                                            colour=("colour", "last"), team=("team", "last")).reset_index()
by_driver = by_driver[by_driver["n"] >= MIN_STARTS].sort_values("score", ascending=False)
if len(by_driver):
    diverge([{"name": str(r.name).title(), "sub": f"{r.team} · {r.n} starts", "colour": r.colour,
              "value": round(r.score * 100)} for r in by_driver.itertuples()],
            left_label="Loses places (hundredths per start)", right_label="Gains places (hundredths per start)")
    st.caption("A value of +50 means half a place better than an average car from the same slot, every start.")
else:
    st.caption(f"Nobody has {MIN_STARTS} starts in this selection. Widen it above.")

# ---------- circuits ----------
if place == "Every circuit":
    section("Which circuits shuffle the order", "Average number of places each car moves (either way) on lap 1.")
    by_circuit = d.assign(moves=d["gained"].abs()).groupby("location").agg(
        moves=("moves", "mean"), races=("round", "nunique")).reset_index().sort_values("moves", ascending=False)
    cchart = alt.Chart(by_circuit).mark_bar(cornerRadius=3, color="#e10600").encode(
        y=alt.Y("location:N", sort="-x", title=None), x=alt.X("moves:Q", title="Places moved per car"),
        tooltip=["location", alt.Tooltip("moves:Q", format=".2f")])
    st.altair_chart(dress(cchart).properties(height=max(240, 18 * len(by_circuit))), use_container_width=True)

# ---------- biggest moves ----------
section("The biggest opening laps", "Most places gained between the grid and the end of lap 1.")
top = d.sort_values(["gained", "season"], ascending=[False, False]).head(12)
sheet([("Race", "text"), ("Driver", "tag"), ("Grid", "num"), ("After lap 1", "num"), ("Gained", "num")],
      [[f"{r.race_name} {r.season}", (r.colour, r.code), r.grid, r.after_lap1, f"+{r.gained}"] for r in top.itertuples()])

with st.expander("How this is worked out"):
    st.markdown("""
Grid slots come from the official results (Jolpica). A pit-lane start counts as starting last.
The position after lap 1 comes from OpenF1's lap data. Races where lap 1 was stopped by a red
flag before positions were recorded are left out.

**Fair comparison.** A car starting 20th gains places almost automatically, and the polesitter
can only lose them. So drivers are compared with what the *average* car gained from the *same*
grid slot across every race here. Being in a slow car, or starting next to a crash, still
shows up, so read small differences with care.
""")
