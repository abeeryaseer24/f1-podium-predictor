"""Team Performance: how fast each car really was, race by race, measured from the lap
times rather than guessed from the results."""
import streamlit as st

from app_garage import default_season, get_seasons, get_team_pace, pace_available
from cards import cards_css, note
from charts import pace_lines, simple_bars
from style import empty_note, stat_strip, team_info

cards_css()

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

st.subheader("What the number means")
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

st.subheader("Car pace through the season")
note("Smoothed over the last three races, because one weekend on its own is noisy. "
     "A line stepping up usually means an upgrade landed; a line falling away often means "
     "everyone else moved on. Hover a point to see that single race too.")
st.altair_chart(pace_lines(pace), width="stretch", theme=None)

st.subheader("Average gap over the whole season")
st.altair_chart(simple_bars(season_avg, "pct_off", "Per cent off the fastest car",
                            sort_ascending=True), width="stretch", theme=None)

st.subheader("Race by race, exactly as measured")
show = pace.copy()
show["Team"] = show["constructor"].map(lambda t: team_info(t)[0])
st.dataframe(
    show[["round", "race_name", "Team", "pct_off", "smoothed", "clean_laps", "wet"]]
    .rename(columns={"round": "Round", "race_name": "Race", "pct_off": "Off the pace %",
                     "smoothed": "Smoothed %", "clean_laps": "Clean laps", "wet": "Wet"})
    .sort_values(["Round", "Off the pace %"]),
    hide_index=True, width="stretch")

note("<b>Worth knowing.</b> Pace is measured from race laps, so a car that spent the "
     "afternoon stuck in traffic looks slower than it was. Safety cars, a long first stint "
     "on hard tyres and a damaged floor all move the number. It says a team was quicker, "
     "not why.")
