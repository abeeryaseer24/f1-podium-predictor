"""Driver Standings: the drivers' championship for any season, with the charts behind it."""
import altair as alt
import streamlit as st

from app_garage import (default_season, get_driver_progress, get_driver_table, get_seasons,
                        sprint_points_included)
from cards import cards_css, note, standings_rows
from charts import dress, team_scale
from predictor import clean_name
from style import empty_note, stat_strip, team_info

cards_css()

seasons = get_seasons()
if not seasons:
    empty_note("No results have been downloaded yet.")
    st.stop()

season = st.selectbox("Season", seasons, index=seasons.index(default_season()))
table = get_driver_table(season)
progress = get_driver_progress(season)

if table.empty:
    empty_note(f"No results for {season} yet.")
    st.stop()

leader = table.iloc[0]
gap = (table["points"].iloc[0] - table["points"].iloc[1]) if len(table) > 1 else 0
rounds = int(progress["round"].max())
winners = int((table["wins"] > 0).sum())

stat_strip([
    ("Leader", clean_name(leader["driver"]), f'{leader["points"]:.0f} points', True),
    ("Lead over second", f"{gap:.0f}", "points", False),
    ("Rounds raced", str(rounds), f"{len(table)} drivers", False),
    ("Different winners", str(winners), "this season", False),
])

if not sprint_points_included():
    note("Sprint points are not counted yet. Run <code>python src/sprint_loader.py</code> "
         "once to add them.")

# ---------- the table ----------

rows = []
for row in table.itertuples():
    team_name, colour = team_info(row.constructor)
    rows.append((int(row.position), colour, clean_name(row.driver), team_name, [
        (f"{row.points:.0f}", "Points"),
        (int(row.wins), "Wins"),
        (int(row.podiums), "Podiums"),
        (int(row.poles), "Poles"),
    ]))
standings_rows(rows)

# ---------- the charts ----------

TOP = 10
leaders = table.head(TOP)["driver"].tolist()
shown = progress[progress["driver"].isin(leaders)].copy()
shown = shown.rename(columns={"driver": "driver_id"})
shown["constructor"] = shown["constructor"].fillna("unknown")

st.subheader(f"Points through the season, top {TOP}")
note("Only the leading drivers are drawn, otherwise the chart turns into spaghetti. "
     "Two drivers from the same team share a colour, so hover a line to see who is who.")
chart_data = shown.rename(columns={"driver_id": "driver"})
chart_data["driver"] = chart_data["driver"].map(clean_name)
chart_data["Team"] = chart_data["constructor"].map(lambda t: team_info(t)[0])

scale = team_scale(sorted(chart_data["constructor"].unique()))
base = alt.Chart(chart_data).encode(
    x=alt.X("round:Q", title="Round", axis=alt.Axis(tickMinStep=1, format="d")),
    color=alt.Color("Team:N", scale=scale, title=None),
    detail="driver:N",
    tooltip=[alt.Tooltip("driver:N", title="Driver"), "Team",
             alt.Tooltip("race_name:N", title="Race"),
             alt.Tooltip("cum_points:Q", title="Points"),
             alt.Tooltip("position:Q", title="Place")])
st.altair_chart(
    dress(base.mark_line(strokeWidth=3, interpolate="monotone")
          .encode(y=alt.Y("cum_points:Q", title="Points"))),
    width="stretch", theme=None)

st.subheader(f"Championship place after every race, top {TOP}")
top_place = int(chart_data["position"].max())
bumps = base.encode(y=alt.Y("position:Q", title="Championship place",
                            scale=alt.Scale(domain=[top_place + 0.5, 0.5]),
                            axis=alt.Axis(tickMinStep=1, format="d")))
st.altair_chart(dress(bumps.mark_line(strokeWidth=3) + bumps.mark_circle(size=50)),
                width="stretch", theme=None)

st.subheader("Points scored at each race")
bars = (alt.Chart(chart_data[chart_data["points"] > 0]).mark_bar()
        .encode(x=alt.X("round:O", title="Round"),
                y=alt.Y("points:Q", title="Points that race"),
                color=alt.Color("Team:N", scale=scale, title=None),
                tooltip=[alt.Tooltip("driver:N", title="Driver"), "Team",
                         alt.Tooltip("points:Q", title="Points")]))
st.altair_chart(dress(bars), width="stretch", theme=None)
