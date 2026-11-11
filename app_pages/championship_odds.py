"""Championship Odds: the rest of the season replayed thousands of times, to see who
still wins the drivers' and constructors' titles."""
import altair as alt
import streamlit as st

from app_garage import default_season, get_championship_odds, get_seasons
from cards import cards_css, note
from charts import dress, team_scale
from predictor import clean_name
from style import empty_note, stat_strip, team_info

cards_css()

seasons = get_seasons()
if not seasons:
    empty_note("No results have been downloaded yet.")
    st.stop()

season = default_season()
result = get_championship_odds(season)

if result.get("finished"):
    empty_note(f"The {season} season is over, so there is nothing left to simulate.")
    note("Open <b>Season Rewind</b> or <b>Driver Standings</b> to see how it finished.")
    st.stop()

if "error" in result:
    empty_note(f"The odds cannot be worked out right now: {result['error']}")
    note("This page needs the season calendar and the next race's grid, both of which "
         "come from the internet. Try again in a few minutes.")
    st.stop()

drivers = result["drivers"]
teams = result["teams"]
leader = drivers.iloc[0]
team_leader = teams.iloc[0]
alive = int(drivers["alive"].sum())

stat_strip([
    ("Most likely champion", clean_name(leader["driver"]),
     f'{leader["title_chance"]:.0f}% of simulated seasons', True),
    ("Most likely team", team_info(team_leader["constructor"])[0],
     f'{team_leader["title_chance"]:.0f}% of simulated seasons', False),
    ("Races left", str(result["races_left"]),
     f'{result["sprints_left"]} sprint{"s" if result["sprints_left"] != 1 else ""}', False),
    ("Still mathematically alive", str(alive),
     f'{result["most_points_left"]} points still on the table', False),
])

grid_note = ("the real starting grid for the next race"
             if result["grid_source"] != "estimated"
             else "an estimated grid, because qualifying has not happened yet")
note(f'The rest of the season was replayed <b>{result["simulations"]:,}</b> times, '
     f'starting from the {result["next_race"]} and using {grid_note}.')

# ---------- drivers ----------

st.subheader("Drivers' championship")
data = drivers[drivers["title_chance"] > 0.05].copy()
if data.empty:
    data = drivers.head(5).copy()
data["Driver"] = data["driver"].map(clean_name)
data["Team"] = data["constructor"].map(lambda t: team_info(t)[0])
scale = team_scale(sorted(data["constructor"].unique()))

chart = (alt.Chart(data).mark_bar(cornerRadiusEnd=4)
         .encode(x=alt.X("title_chance:Q", title="Chance of the title (%)"),
                 y=alt.Y("Driver:N", sort=data["Driver"].tolist(), title=None),
                 color=alt.Color("Team:N", scale=scale, legend=None),
                 tooltip=["Driver", "Team",
                          alt.Tooltip("title_chance:Q", title="Title chance %", format=".1f"),
                          alt.Tooltip("points_now:Q", title="Points now"),
                          alt.Tooltip("expected_points:Q", title="Expected final points")]))
st.altair_chart(dress(chart).properties(height=max(200, 30 * len(data))),
                width="stretch", theme=None)

show = drivers.copy()
show["Driver"] = show["driver"].map(clean_name)
show["Team"] = show["constructor"].map(lambda t: team_info(t)[0])
show["Title chance"] = show["title_chance"].map(lambda v: f"{v:.1f}%")
show["Top three chance"] = show["top3_chance"].map(lambda v: f"{v:.1f}%")
show["Likely final points"] = (show["low_points"].astype(int).astype(str) + " to "
                               + show["high_points"].astype(int).astype(str))
show["Still possible"] = show["alive"].map({True: "Yes", False: "Out of reach"})
st.dataframe(
    show[["Driver", "Team", "points_now", "Title chance", "Top three chance",
          "expected_points", "Likely final points", "Still possible"]]
    .rename(columns={"points_now": "Points now", "expected_points": "Expected points"}),
    hide_index=True, width="stretch")

# ---------- constructors ----------

st.subheader("Constructors' championship")
team_data = teams[teams["title_chance"] > 0.05].copy()
if team_data.empty:
    team_data = teams.head(5).copy()
team_data["Team"] = team_data["constructor"].map(lambda t: team_info(t)[0])
chart = (alt.Chart(team_data).mark_bar(cornerRadiusEnd=4)
         .encode(x=alt.X("title_chance:Q", title="Chance of the title (%)"),
                 y=alt.Y("Team:N", sort=team_data["Team"].tolist(), title=None),
                 color=alt.Color("Team:N",
                                 scale=team_scale(sorted(team_data["constructor"].unique())),
                                 legend=None),
                 tooltip=["Team",
                          alt.Tooltip("title_chance:Q", title="Title chance %", format=".1f"),
                          alt.Tooltip("points_now:Q", title="Points now"),
                          alt.Tooltip("expected_points:Q", title="Expected final points")]))
st.altair_chart(dress(chart).properties(height=max(180, 32 * len(team_data))),
                width="stretch", theme=None)

team_show = teams.copy()
team_show["Team"] = team_show["constructor"].map(lambda t: team_info(t)[0])
team_show["Title chance"] = team_show["title_chance"].map(lambda v: f"{v:.1f}%")
team_show["Likely final points"] = (team_show["low_points"].astype(int).astype(str) + " to "
                                    + team_show["high_points"].astype(int).astype(str))
team_show["Still possible"] = team_show["alive"].map({True: "Yes", False: "Out of reach"})
st.dataframe(
    team_show[["Team", "points_now", "Title chance", "expected_points",
               "Likely final points", "Still possible"]]
    .rename(columns={"points_now": "Points now", "expected_points": "Expected points"}),
    hide_index=True, width="stretch")

# ---------- how it works ----------

st.subheader("How these numbers are made")
note("Every remaining race is drawn from the same model that makes our podium predictions: "
     "each driver has a strength, and the finishing order is drawn from those strengths with "
     "the right amount of luck mixed in. Drivers retire at roughly the rate they have this "
     "season. Points are awarded the normal way, sprints included, and the season is run "
     f'{result["simulations"]:,} times. The percentage is simply how often each driver or '
     "team came out on top.")
note("<b>What it cannot know.</b> It assumes the rest of the season looks like the next "
     "race, so an upgrade that has not landed yet, a wet weekend, a driver swap or a "
     "penalty are all missing. <b>Still possible</b> in the table is different: that is "
     "pure arithmetic, comparing the gap with the points still available, and it is always "
     "right even when the percentage says the chance is tiny.")
