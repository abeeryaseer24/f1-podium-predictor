"""Champions: every drivers' and constructors' title since 1950."""
import altair as alt
import streamlit as st

from app_archive import get_champions, get_title_counts, require_history
from cards import cards_css, note
from charts import dress, name_scale
from style import empty_note, stat_strip, team_info
from ui_kit import GOLD, chip, kit_css, league, section

cards_css()
kit_css()
require_history()

table = get_champions()
if table.empty:
    empty_note("No champions found in the history files.")
    st.stop()

drivers = get_title_counts("driver")
teams = get_title_counts("team")
latest = table.iloc[-1]


def joint_best(counted, name_column):
    """The record holders and their total. Several people can share a record, and a
    card that only shows the first of them is simply wrong."""
    if counted.empty:
        return "—", ""
    top = int(counted.iloc[0]["titles"])
    held = counted[counted["titles"] == top][name_column].tolist()
    if len(held) == 1:
        return held[0], f"{top} championships"
    if len(held) == 2:
        return " & ".join(held), f"{top} championships each"
    return f"{held[0]} and {len(held) - 1} others", f"{top} championships each"


best_driver, best_driver_note = joint_best(drivers, "driver_name")
best_team, best_team_note = joint_best(teams, "team_name")

stat_strip([
    ("Seasons", str(len(table)),
     f'{int(table["season"].min())} to {int(table["season"].max())}', True),
    ("Most titles, driver", best_driver, best_driver_note, False),
    ("Most titles, team", best_team, best_team_note, False),
    ("Latest champion", latest["driver_name"] or "—", str(int(latest["season"])), False),
])

# ---------- the two leaderboards ----------

section("Titles per driver",
        "Everyone who has won the drivers' championship, most first. Hover or tap a "
        "bar for the years.")
top_drivers = drivers.head(20)
chart = (alt.Chart(top_drivers).mark_bar(cornerRadiusEnd=4, color="#e10600")
         .encode(x=alt.X("titles:Q", title="Championships",
                         axis=alt.Axis(tickMinStep=1, format="d")),
                 y=alt.Y("driver_name:N", sort=top_drivers["driver_name"].tolist(), title=None),
                 tooltip=[alt.Tooltip("driver_name:N", title="Driver"),
                          alt.Tooltip("titles:Q", title="Titles"),
                          alt.Tooltip("years:N", title="Years")]))
st.altair_chart(dress(chart).properties(height=max(220, 26 * len(top_drivers))),
                width="stretch", theme=None)

section("Titles per constructor",
        "The same for teams, each in its own colour.")
top_teams = teams.head(20)
chart = (alt.Chart(top_teams).mark_bar(cornerRadiusEnd=4)
         .encode(x=alt.X("titles:Q", title="Championships",
                         axis=alt.Axis(tickMinStep=1, format="d")),
                 y=alt.Y("team_name:N", sort=top_teams["team_name"].tolist(), title=None),
                 color=alt.Color("team_name:N", scale=name_scale(top_teams["team_name"].tolist()),
                                 legend=None),
                 tooltip=[alt.Tooltip("team_name:N", title="Team"),
                          alt.Tooltip("titles:Q", title="Titles"),
                          alt.Tooltip("years:N", title="Years")]))
st.altair_chart(dress(chart).properties(height=max(220, 26 * len(top_teams))),
                width="stretch", theme=None)
note("There was no constructors' championship until 1958, so the early seasons have a "
     "drivers' champion only.")

# ---------- every season, as a timeline ----------

section("Every season since 1950",
        "Newest first, in the champion's team colour. The bar is how many races they "
        "won that year, measured against the best anyone has ever managed.")

most_wins_ever = max(1, int(table["driver_wins"].max()))
team_colour = {}
for row in teams.itertuples():
    team_colour[row.team_name] = team_info(row.team)[1]

rows = []
for row in table.sort_values("season", ascending=False).itertuples():
    colour = team_colour.get(row.driver_team) or "#8a8a96"
    if colour == "#8a8a96":
        # the champion's team may not have won a constructors' title, so look it up
        colour = team_info(str(row.driver_team).lower().replace(" ", "_"))[1]
    double = (row.team_name and row.driver_team
              and row.team_name.lower() == str(row.driver_team).lower())
    tag = chip("double", GOLD) if double else ""
    sub = (f'{row.driver_team} · constructors: {row.team_name}' if row.team_name
           else f'{row.driver_team} · no constructors\' title that year')
    rows.append({
        "pos": int(row.season), "name": row.driver_name or "—", "sub": sub,
        "colour": colour, "bar": (row.driver_wins or 0) / most_wins_ever, "tag": tag,
        "figures": [(int(row.driver_wins), "wins"), (f"{row.driver_points:,.0f}", "points")],
    })
league(rows, wide_position=True)
note("A <b>double</b> is a season where the champion's own team also won the "
     "constructors' title. Points are not comparable between eras.")
