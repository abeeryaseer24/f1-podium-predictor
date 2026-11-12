"""Tyre Lab: how much each tyre compound slows down as it wears, race by race."""
import altair as alt
import pandas as pd
import streamlit as st

from app_data import get_prepared_races, get_tyres
from ui_kit import kit_css, section

kit_css()
races = get_prepared_races()
if races.empty:
    st.info("No races prepared yet. The robot adds a few every 3 hours.")
    st.stop()

# ---------- pick a race ----------
left, right = st.columns(2)
season = left.selectbox("Season", sorted(races["season"].unique().tolist(), reverse=True))
in_season = races[races["season"] == season].sort_values("round")
names = {r.folder: f"Round {r.round} · {r.race_name}" for r in in_season.itertuples()}
folder = right.selectbox("Race", list(names), format_func=names.get)

result = get_tyres(folder)
compounds = result["compounds"]
if not compounds:
    st.info("Not enough clean laps on any tyre in this race to measure wear "
            "(this can happen with a wet race or a long safety car).")
    st.stop()

dark = st.session_state.dark
COLOURS = {"SOFT": "#e10600", "MEDIUM": "#f2c21b", "HARD": "#e8e8e8" if dark else "#8a8a96",
           "INTERMEDIATE": "#2ecc71", "WET": "#2b6cff"}
ref = result["ref"].title()
y_title = f"Seconds slower than a fresh {ref}"

# ---------- the chart: data points + one wear curve per compound ----------
curves = pd.DataFrame([
    {"Compound": c["name"].title(), "Tyre age (laps)": age,
     y_title: c["offset"] + c["wear"] * age}
    for c in compounds for age in range(0, c["max_age"] + 1)
])
points = result["points"].rename(columns={"compound": "Compound", "tyre_age": "Tyre age (laps)",
                                          "adjusted": y_title})
points["Compound"] = points["Compound"].str.title()
low, high = points[y_title].quantile([0.02, 0.98])          # hide the most extreme dots
points = points[points[y_title].between(low, high)]

domain = [c["name"].title() for c in compounds]
scale = alt.Scale(domain=domain, range=[COLOURS[c["name"]] for c in compounds])
text_colour, grid_colour = ("#f5f5f7", "#2c2c3a") if dark else ("#15151e", "#d9d9d4")

dots = alt.Chart(points).mark_circle(size=22, opacity=0.25).encode(
    x="Tyre age (laps):Q", y=alt.Y(f"{y_title}:Q"),
    color=alt.Color("Compound:N", scale=scale, legend=None))
lines = alt.Chart(curves).mark_line(strokeWidth=3.5).encode(
    x="Tyre age (laps):Q", y=alt.Y(f"{y_title}:Q"),
    color=alt.Color("Compound:N", scale=scale, legend=None))          # the tyre key sits above the chart
chart = ((dots + lines).properties(height=380)
         .configure(background="transparent")
         .configure_axis(labelColor=text_colour, titleColor=text_colour,
                         gridColor=grid_colour, domainColor=grid_colour)
         .configure_legend(labelColor=text_colour))
def tyre_chip(name):
    """A small tyre (coloured ring, like the real sidewall marking) with the compound's name."""
    colour = COLOURS[name.upper()]
    return (f'<span style="display:inline-flex;align-items:center;gap:7px;margin-right:18px;font-weight:600">'
            f'<span style="width:16px;height:16px;border-radius:50%;background:#1b1b22;'
            f'box-shadow:inset 0 0 0 4px {colour}"></span>{name.title()}</span>')


st.markdown('<div style="margin:.2rem 0 .4rem">' + "".join(tyre_chip(c["name"]) for c in compounds) + "</div>",
            unsafe_allow_html=True)
st.altair_chart(chart, width="stretch", theme=None)
st.caption("Each faint dot is one clean lap, with the driver's pace and the fuel load taken out. "
           "The lines are the model's wear curves.")

# ---------- one card per compound ----------
section("Compound by compound",
            "How quickly each tyre gives up its lap time, measured from clean racing laps.")
cards = st.columns(len(compounds))
for card, c in zip(cards, compounds):
    card.markdown(tyre_chip(c["name"]), unsafe_allow_html=True)
    card.metric("Wear per lap", f"{c['wear']:+.3f} s/lap")
    card.caption(f"Fresh: {c['offset']:+.2f} s vs {ref}  \n"
                 f"{c['laps']} clean laps  \n"
                 f"Longest stint: {c['max_age']} laps")

if len(compounds) > 1:
    best = min(compounds, key=lambda c: c["wear"])
    worst = max(compounds, key=lambda c: c["wear"])
    fastest = min(compounds, key=lambda c: c["offset"])
    st.markdown(f"**{best['name'].title()} lasts best here**, losing {best['wear']:.3f} s per lap "
                f"of wear, against {worst['wear']:.3f} s for {worst['name'].title()}. "
                f"A fresh {fastest['name'].title()} is the quickest tyre.")

# ---------- the key numbers for strategy ----------
section("Strategy numbers",
            "What the wear rates mean for a race: how long each tyre is worth running.")
m1, m2, m3 = st.columns(3)
m1.metric("Fuel effect", f"{-result['fuel']:.3f} s/lap",
          help="How much faster a car gets each lap as fuel burns off")
m2.metric("Pit stop loss", f"{result['pit_loss']:.1f} s" if result["pit_loss"] else "Not enough stops",
          help="Time lost by stopping, compared with staying out for the same two laps")
m3.metric("Model error", f"±{result['error']:.2f} s",
          help="Typical error per lap, measured on laps the model didn't learn from")
st.caption(f"Based on {result['clean_laps']} clean racing laps. A negative wear number means "
           "the track got faster than the tyre wore out.")