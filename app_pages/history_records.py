"""Records: the all-time leaderboards for drivers and constructors."""
import altair as alt
import streamlit as st

from app_archive import get_driver_records, get_team_records, require_history
from archive import FASTEST_LAP_FROM, METRICS
from cards import cards_css, note
from charts import dress, name_scale
from style import empty_note, stat_strip

cards_css()
require_history()

labels = {key: value[0] for key, value in METRICS.items()}
left, middle, right = st.columns([2, 2, 1])
with left:
    metric = st.selectbox("Record", list(labels), format_func=lambda k: labels[k])
with middle:
    who = st.selectbox("For", ["Drivers", "Constructors"])
with right:
    active = st.toggle("Active only", value=False,
                       help="Only those who have raced in the last two seasons.")

table = (get_driver_records(metric, active, 25) if who == "Drivers"
         else get_team_records(metric, active, 25))

if table.empty:
    empty_note("Nothing to show for that choice.")
    st.stop()

name_column = "driver_name" if who == "Drivers" else "constructor_name"
best = table.iloc[0]
value_label = labels[metric]
decimals = 1 if metric == "points" else 0

stat_strip([
    (f"Most {value_label.lower()}", best[name_column], f'{best["value"]:,.{decimals}f}', True),
    ("Second", table.iloc[1][name_column] if len(table) > 1 else "—",
     f'{table.iloc[1]["value"]:,.{decimals}f}' if len(table) > 1 else "", False),
    ("Shown", f"top {len(table)}",
     "active only" if active else "everyone, all time", False),
])

if metric == "fastest_laps":
    note(f"The API only records who set the fastest lap from {FASTEST_LAP_FROM} onwards, "
         "so this leaderboard starts there and is not an all-time list.")
if metric == "poles":
    note("Pole is counted as starting first. In the earliest seasons the starting grid is "
         "sometimes missing from the records, so the oldest numbers can be a little short.")
if metric == "points":
    note("Career points are not comparable across the years. A win was worth 8 points in "
         "1950, 9 from 1961, 10 from 1991 and 25 from 2010, and seasons are much longer "
         "now, so modern drivers tower over the rest of this list.")

st.subheader(f"{value_label}: top {len(table)}")
chart = (alt.Chart(table).mark_bar(cornerRadiusEnd=4)
         .encode(x=alt.X("value:Q", title=value_label),
                 y=alt.Y(f"{name_column}:N", sort=table[name_column].tolist(), title=None),
                 color=(alt.Color(f"{name_column}:N",
                                  scale=name_scale(table[name_column].tolist()), legend=None)
                        if who == "Constructors" else alt.value("#e10600")),
                 tooltip=[alt.Tooltip(f"{name_column}:N", title=who[:-1]),
                          alt.Tooltip("value:Q", title=value_label),
                          alt.Tooltip("starts:Q", title="Race starts"),
                          alt.Tooltip("first_season:Q", title="From", format="d"),
                          alt.Tooltip("last_season:Q", title="To", format="d")]))
st.altair_chart(dress(chart).properties(height=max(260, 26 * len(table))),
                width="stretch", theme=None)

show = table.copy()
show["Seasons"] = (show["first_season"].astype(int).astype(str) + "–"
                   + show["last_season"].astype(int).astype(str))
show["Per start"] = (show["value"] / show["starts"]).round(3)
st.dataframe(
    show[[name_column, "value", "starts", "Per start", "Seasons"]]
    .rename(columns={name_column: who[:-1], "value": value_label, "starts": "Race starts"}),
    hide_index=True, width="stretch")
note("<b>Per start</b> is the record divided by races entered. It flatters drivers from "
     "the short seasons of the 1950s, when a championship was seven or eight races, and it "
     "is hard on anyone who stayed in the sport long after their best car.")
