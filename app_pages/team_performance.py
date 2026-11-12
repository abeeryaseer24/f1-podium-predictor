"""Team Performance: how fast each car really was, race by race, measured from the lap
times rather than guessed from the results."""
import streamlit as st

from app_garage import default_season, get_seasons, get_team_pace, pace_available
from cards import cards_css, note
from charts import pace_lines, simple_bars
from style import empty_note, stat_strip, team_info
from ui_kit import heat, kit_css, section

cards_css()
kit_css()

if not pace_available():
    empty_note("The pace files have not been built yet.")
    note("Run <code>python src/pace.py</code> once. It reads the race files already in "
         "<code>data/races/</code> and writes <code>data/processed/pace_teams.csv</code> "
         "and <code>pace_drivers.csv</code>. No downloading is needed.")
    st.stop()

seasons = get_seasons()
season = st.selectbox("Season", seasons, index=seasons.index(default_season()))
dry_only = st.toggle("Dry races only", value=True,
                     help="Wet races say more about the driver and the gamble than the car.")

pace = get_team_pace(season, dry_only)
if pace.empty:
    empty_note(f"No lap data for {season}. Pace only goes back to 2023, which is where "
               "OpenF1's lap times begin.")
    st.stop()

section("What the number means",
        "One figure for how quick each car really was, measured from lap times rather than guessed from the results.")
note("For every race we take each driver's clean racing laps, average their fastest "
     "quarter, and compare the team's better car with the fastest car of the weekend. "
     "<b>0.0%</b> is the quickest car that weekend. <b>1.0%</b> is about nine tenths of a "
     "second slower on a ninety second lap. Lower is faster.")

latest = pace[pace["round"] == pace["round"].max()]
season_avg = (pace.groupby("constructor", as_index=False)["pct_off"].mean()
              .round(3).sort_values("pct_off"))
best = season_avg.iloc[0]
races = pace["round"].nunique()

stat_strip([
    ("Fastest car this season", team_info(best["constructor"])[0],
     f'{best["pct_off"]:.2f}% off on average', True),
    ("Races measured", str(races), "dry races only" if dry_only else "every race", False),
    ("Quickest last time out",
     team_info(latest.sort_values("pct_off").iloc[0]["constructor"])[0]
     if not latest.empty else "—",
     latest.iloc[0]["race_name"] if not latest.empty else "", False),
])

section("Car pace through the season",
        "Smoothed over the last three races, because one weekend on its own is noisy.")
note("A line stepping up usually means an upgrade landed; a line falling away often "
     "means everyone else moved on. Hover or tap a point to see that single race too.")
st.altair_chart(pace_lines(pace), width="stretch", theme=None)

section("Average gap over the whole season",
        "Each team’s mean distance from the quickest car of the weekend. Lower is faster.")
st.altair_chart(simple_bars(season_avg, "pct_off", "Per cent off the fastest car",
                            sort_ascending=True), width="stretch", theme=None)

section("Every car at every race",
        "The whole season in one grid: each team against each round, coloured by how "
        "far off the quickest car they were that weekend. Green is on the pace, red is "
        "a long way off. Read along a row to watch a car come good, or down a column "
        "to find a circuit that suited one team.")
grid = pace.copy()
grid["Team"] = grid["constructor"].map(lambda t: team_info(t)[0])
rounds = sorted(grid["round"].unique())
order = [team_info(c)[0] for c in season_avg["constructor"]]
colours = {team_info(c)[0]: team_info(c)[1] for c in season_avg["constructor"]}
worst = float(grid["pct_off"].max()) or 1.0
cells, titles = {}, {}
for row in grid.itertuples():
    label = f"R{int(row.round)}"
    titles[label] = row.race_name
    cells[(row.Team, label)] = (f"{row.pct_off:.1f}", 1 - (float(row.pct_off) / worst))
heat(order, [f"R{r}" for r in rounds], cells,
     legend=("Furthest off", "Quickest car"), row_colours=colours, column_titles=titles,
     missing_label="race not measured")
note("The number in each square is the per cent off the quickest car that weekend. An "
     "empty square means that race was not measured: either it was wet and the dry-only "
     "switch is on, or there were too few clean laps to judge.")

note("<b>Worth knowing.</b> Pace is measured from race laps, so a car that spent the "
     "afternoon stuck in traffic looks slower than it was. Safety cars, a long first stint "
     "on hard tyres and a damaged floor all move the number. It says a team was quicker, "
     "not why.")
