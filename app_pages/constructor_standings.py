"""Constructor Standings: the teams' championship for any season, with the charts
that show how it got there."""
import streamlit as st

from app_garage import (default_season, get_constructor_progress, get_constructor_table,
                        get_seasons, sprint_points_included)
from cards import cards_css, note, standings_rows
from charts import gap_to_leader, points_lines, points_per_race, position_bumps
from predictor import clean_name
from style import empty_note, stat_strip, team_info
from ui_kit import kit_css, section

cards_css()
kit_css()

seasons = get_seasons()
if not seasons:
    empty_note("No results have been downloaded yet.")
    st.stop()

season = st.selectbox("Season", seasons, index=seasons.index(default_season()))
table = get_constructor_table(season)
progress = get_constructor_progress(season)

if table.empty:
    empty_note(f"No results for {season} yet.")
    st.stop()

leader = table.iloc[0]
rounds = int(progress["round"].max())
total_points = float(table["points"].sum())

stat_strip([
    ("Leader", team_info(leader["constructor"])[0], f'{leader["points"]:.0f} points', True),
    ("Rounds raced", str(rounds), f"{len(table)} teams scoring", False),
    ("Points on the board", f"{total_points:.0f}", "shared out so far", False),
    ("Closest gap", f'{table["points"].iloc[0] - table["points"].iloc[1]:.0f}'
     if len(table) > 1 else "—", "first to second", False),
])

if not sprint_points_included():
    note("Sprint points are not counted yet. Run <code>python src/sprint_loader.py</code> once "
         "to add them; without it, sprint weekends are short by up to 8 points per driver.")

# ---------- the table ----------

rows = []
for row in table.itertuples():
    name, colour = team_info(row.constructor)
    drivers = ", ".join(clean_name(d).split()[-1] for d in row.drivers)
    rows.append((int(row.position), colour, name, drivers, [
        (f"{row.points:.0f}", "Points"),
        (int(row.wins), "Wins"),
        (int(row.podiums), "Podiums"),
        (int(row.dnfs), "DNFs"),
    ]))
standings_rows(rows)

# ---------- the charts ----------

section("Points through the season",
            "Every team's running total, round by round.")
note("Every team's running total, race by race. The steeper the line, the better the run.")
st.altair_chart(points_lines(progress), width="stretch", theme=None)

section("Who was where, after every race",
            "Championship position after each round. Lines crossing means the order changed.")
note("Championship place after each round. Higher on the chart is better.")
st.altair_chart(position_bumps(progress), width="stretch", theme=None)

section("Points scored at each race",
            "What each team took home from each weekend, not the running total.")
note("One row per team, best season first. Each bar is a single Grand Prix, and every "
     "row is drawn against the same scale, so a tall bar really was a big weekend and "
     "a gap is a weekend with nothing. The most one team can score is 43 points at a "
     "normal race, or 58 at a sprint weekend. Tap a bar for the race and the score.")
st.altair_chart(points_per_race(progress), width="stretch", theme=None)

st.subheader("How far behind the leader")
note("Zero is the team leading the championship at that point in the season.")
st.altair_chart(gap_to_leader(progress), width="stretch", theme=None)
