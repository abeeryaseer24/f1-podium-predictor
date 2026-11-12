"""Driver Profiles: any driver who has started a Grand Prix since 1950."""
import altair as alt
import streamlit as st

from app_archive import (get_driver_career, get_driver_index, get_driver_seasons,
                         require_history)
from cards import cards_css, figures, glass, key_values, note, ordinal
from charts import dress
from style import empty_note
from ui_kit import GOLD, kit_css, league, section

cards_css()
kit_css()
require_history()

index = get_driver_index()
if index.empty:
    empty_note("No drivers found in the history files.")
    st.stop()

names = dict(zip(index["driver"], index["driver_name"]))
labels = {f'{row.driver_name} ({int(row.first_season)}–{int(row.last_season)}, '
          f'{int(row.wins)} win{"s" if row.wins != 1 else ""})': row.driver
          for row in index.itertuples()}

note("Every driver who has started a Grand Prix, sorted by race wins. The modern "
     "<b>Driver Cards</b> page has more for the current grid, including lap time pace and "
     "teammate comparisons, which only exist for recent seasons.")
pick = st.selectbox("Driver", list(labels))
driver_id = labels[pick]

career = get_driver_career(driver_id)
seasons = get_driver_seasons(driver_id)
if not career:
    empty_note("No races found for that driver.")
    st.stop()

st.subheader(career["name"])
figures([
    (career["titles"], "Titles"),
    (career["wins"], "Wins"),
    (career["podiums"], "Podiums"),
    (career["poles"], "Poles"),
    (career["starts"], "Starts"),
    (f'{career["points"]:,.0f}', "Points"),
])

glass("Career", key_values([
    ("Nationality", career["nationality"]),
    ("Raced", f'{career["first_season"]} to {career["last_season"]}'),
    ("Championships",
     f'{career["titles"]} ({career["title_years"]})' if career["titles"] else "None"),
    ("Best finish", f'P{career["best_finish"]}'),
    ("Win rate", f'{100 * career["wins"] / career["starts"]:.1f}% of starts'),
    ("Podium rate", f'{100 * career["podiums"] / career["starts"]:.1f}% of starts'),
    ("Teams", ", ".join(career["teams"])),
]))

if seasons.empty:
    st.stop()

if "championship_place" in seasons.columns and seasons["championship_place"].notna().any():
    section("Championship place by season",
            "Where they finished in the table each year. Lower is better.")
    note("Lower on the chart is better.")
    places = seasons.dropna(subset=["championship_place"])
    top = int(places["championship_place"].max())
    chart = (alt.Chart(places).mark_line(strokeWidth=3, point=True, color="#e10600")
             .encode(x=alt.X("season:O", title=None),
                     y=alt.Y("championship_place:Q", title="Championship place",
                             scale=alt.Scale(domain=[top + 0.5, 0.5]),
                             axis=alt.Axis(tickMinStep=1, format="d")),
                     tooltip=[alt.Tooltip("season:O", title="Season"),
                              alt.Tooltip("championship_place:Q", title="Place"),
                              alt.Tooltip("team:N", title="Team"),
                              alt.Tooltip("points:Q", title="Points")]))
    st.altair_chart(dress(chart).properties(height=280), width="stretch", theme=None)

section("Wins and podiums by season",
            "How the good results were spread across the career.")
melted = seasons.melt(id_vars="season", value_vars=["wins", "podiums"],
                      var_name="kind", value_name="count")
melted["kind"] = melted["kind"].map({"wins": "Wins", "podiums": "Podiums"})
chart = (alt.Chart(melted).mark_bar()
         .encode(x=alt.X("season:O", title=None),
                 y=alt.Y("count:Q", title="Races",
                         axis=alt.Axis(tickMinStep=1, format="d")),
                 color=alt.Color("kind:N", title=None,
                                 scale=alt.Scale(domain=["Podiums", "Wins"],
                                                 range=["#8a8a96", "#e10600"])),
                 tooltip=[alt.Tooltip("season:O", title="Season"), "kind",
                          alt.Tooltip("count:Q", title="Races")]))
st.altair_chart(dress(chart).properties(height=300), width="stretch", theme=None)

section("Season by season",
        "Every year of the career, newest first. The bar is how many races they won "
        "that season against their own best year.")
show = seasons.copy()
if "championship_place" not in show.columns:
    show["championship_place"] = float("nan")
best_year = max(float(show["wins"].max()), 1e-9)
rows = []
for r in show.sort_values("season", ascending=False).itertuples():
    place = r.championship_place
    place_text = ordinal(place) if place == place else "unplaced"
    rows.append({
        "pos": int(r.season), "name": r.team, "colour": GOLD,
        "sub": f'{place_text} in the championship \u00b7 best finish P{int(r.best_finish)}',
        "bar": float(r.wins) / best_year,
        "figures": [(int(r.races), "races"), (int(r.wins), "wins"),
                    (int(r.podiums), "podiums"), (f"{r.points:g}", "points")],
    })
league(rows, wide_position=True)
