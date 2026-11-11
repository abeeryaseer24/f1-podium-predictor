"""Pit and Strategy: how quick each team is in the box, and what tyres they chose."""
import altair as alt
import streamlit as st

from app_garage import (default_season, get_compound_use, get_prepared_rounds,
                        get_race_stints, get_race_stops, get_seasons, get_team_stops)
from cards import cards_css, note
from charts import dress, simple_bars
from style import empty_note, stat_strip, team_info

COMPOUND_COLOURS = {"SOFT": "#e10600", "MEDIUM": "#f2c21b", "HARD": "#dcdcdc",
                    "INTERMEDIATE": "#39b54a", "WET": "#1e6fd9", "UNKNOWN": "#8a8a96"}

cards_css()

seasons = get_seasons()
season = st.selectbox("Season", seasons, index=seasons.index(default_season()))

stops = get_team_stops(season)
if stops.empty:
    empty_note(f"No pit stop data for {season}.")
    note("Pit stops come from the prepared race files in <code>data/races/</code>, which "
         "start in 2023. If the season is recent, the robot may not have prepared its "
         "races yet.")
    st.stop()

quickest = stops.iloc[0]
fastest_single = stops.loc[stops["best_stop"].idxmin()]

stat_strip([
    ("Quickest crew", team_info(quickest["constructor"])[0],
     f'{quickest["median_stop"]:.2f}s typical stop', True),
    ("Fastest single stop", f'{fastest_single["best_stop"]:.2f}s',
     team_info(fastest_single["constructor"])[0], False),
    ("Stops measured", str(int(stops["stops"].sum())), f"across {season}", False),
])

note("This is the time the car is stationary in the box, which is the number teams quote. "
     "Anything over 10 seconds is left out, because that is a repair or a penalty being "
     "served rather than a pit stop.")

st.subheader("Typical stop time")
st.altair_chart(simple_bars(stops, "median_stop", "Seconds stationary (middle value)",
                            sort_ascending=True), width="stretch", theme=None)

st.subheader("The whole table")
table = stops.copy()
table["Team"] = table["constructor"].map(lambda t: team_info(t)[0])
st.dataframe(
    table[["Team", "stops", "median_stop", "best_stop", "worst_stop"]]
    .rename(columns={"stops": "Stops", "median_stop": "Typical (s)",
                     "best_stop": "Fastest (s)", "worst_stop": "Slowest (s)"}),
    hide_index=True, width="stretch")

# ---------- tyres over the season ----------

compounds = get_compound_use(season)
if not compounds.empty:
    st.subheader("Which tyres each team ran")
    note("Laps completed on each compound. Teams that spend longer on the hard tyre are "
         "usually looking after it to make a one-stop work.")
    data = compounds.copy()
    data["Team"] = data["constructor"].map(lambda t: team_info(t)[0])
    order = (data.groupby("Team")["laps"].sum().sort_values(ascending=False).index.tolist())
    present = [c for c in COMPOUND_COLOURS if c in set(data["compound"])]
    chart = (alt.Chart(data).mark_bar()
             .encode(x=alt.X("laps:Q", title="Laps", stack="normalize"),
                     y=alt.Y("Team:N", sort=order, title=None),
                     color=alt.Color("compound:N", title="Tyre",
                                     scale=alt.Scale(domain=present,
                                                     range=[COMPOUND_COLOURS[c] for c in present])),
                     tooltip=["Team", alt.Tooltip("compound:N", title="Tyre"),
                              alt.Tooltip("laps:Q", title="Laps")]))
    st.altair_chart(dress(chart).properties(height=max(220, 30 * len(order))),
                    width="stretch", theme=None)

# ---------- one race in detail ----------

rounds = get_prepared_rounds(season)
if rounds:
    st.subheader("One race in detail")
    labels = {f'Round {r} · {name}': folder for r, name, folder in rounds}
    pick = st.selectbox("Race", list(labels), index=len(labels) - 1)
    folder = labels[pick]

    race_stops = get_race_stops(folder)
    if not race_stops.empty:
        best = race_stops.loc[race_stops["pit_duration"].idxmin()]
        st.markdown(f'**Fastest stop of the race:** {best["driver_name"]} '
                    f'({team_info(best["constructor"])[0]}) in '
                    f'{best["pit_duration"]:.2f}s on lap {int(best["lap_number"])}.')
        st.dataframe(
            race_stops[["driver_name", "lap_number", "pit_duration"]]
            .sort_values("pit_duration")
            .rename(columns={"driver_name": "Driver", "lap_number": "Lap",
                             "pit_duration": "Stationary (s)"}),
            hide_index=True, width="stretch")

    stints = get_race_stints(folder)
    if not stints.empty:
        st.markdown("**Tyre strategy, driver by driver**")
        present = [c for c in COMPOUND_COLOURS if c in set(stints["compound"])]
        chart = (alt.Chart(stints).mark_bar(height=14)
                 .encode(x=alt.X("start_lap:Q", title="Lap"),
                         x2="end_lap:Q",
                         y=alt.Y("driver_name:N", title=None,
                                 sort=alt.EncodingSortField("start_lap", op="min")),
                         color=alt.Color("compound:N", title="Tyre",
                                         scale=alt.Scale(domain=present,
                                                         range=[COMPOUND_COLOURS[c] for c in present])),
                         tooltip=[alt.Tooltip("driver_name:N", title="Driver"),
                                  alt.Tooltip("compound:N", title="Tyre"),
                                  alt.Tooltip("start_lap:Q", title="From lap"),
                                  alt.Tooltip("end_lap:Q", title="To lap"),
                                  alt.Tooltip("laps:Q", title="Laps")]))
        st.altair_chart(dress(chart).properties(height=max(260, 22 * stints["driver_name"].nunique())),
                        width="stretch", theme=None)
