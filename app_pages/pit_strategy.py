"""Pit and Strategy: how quick each team is in the box, and what tyres they chose."""
import altair as alt
import streamlit as st

from app_garage import (first_prepared, get_compound_use, get_prepared_rounds,
                        get_prepared_seasons, get_race_stints, get_race_stops,
                        get_seasons, get_team_stops)
from cards import cards_css, note
from charts import dress, simple_bars
from style import empty_note, stat_strip, team_info
from ui_kit import kit_css, league, section, sheet

COMPOUND_COLOURS = {"SOFT": "#e10600", "MEDIUM": "#f2c21b", "HARD": "#dcdcdc",
                    "INTERMEDIATE": "#39b54a", "WET": "#1e6fd9", "UNKNOWN": "#8a8a96"}

cards_css()
kit_css()

seasons = get_seasons()
# Open on a season that actually has race files. The current season is often one the
# robot has not prepared yet, and landing on an empty page makes the app look broken.
season = st.selectbox("Season", seasons, index=seasons.index(first_prepared(seasons)))

stops = get_team_stops(season)
if stops.empty:
    empty_note(f"No pit stop data for {season} yet.")
    ready = [s for s in get_prepared_seasons() if s in seasons]
    if ready:
        note("Pit stops are measured from the lap data, which is available for "
             f"<b>{', '.join(str(s) for s in ready)}</b>. Pick one of those above.")
    else:
        note("Pit stops are measured from the lap data, and none of it has been "
             "prepared yet. It appears on its own once the robot has run.")
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

section("Typical stop time",
        "The middle stop time of the season for each crew: half their stops were quicker than this.")
st.altair_chart(simple_bars(stops, "median_stop", "Seconds stationary (middle value)",
                            sort_ascending=True), width="stretch", theme=None)

section("The pit lane league",
        "Every crew by its typical stop. The bar is how close each is to the quickest "
        "crew of the season, so a short bar is seconds lost on every visit.")
quickest = float(stops["median_stop"].min())
league([{
    "pos": place, "name": team_info(row.constructor)[0],
    "colour": team_info(row.constructor)[1],
    "sub": f'{int(row.stops)} stops \u00b7 '
           f'{row.median_stop - quickest:+.2f}s against the quickest crew',
    "bar": quickest / float(row.median_stop),
    "figures": [(f"{row.median_stop:.2f}s", "typical"),
                (f"{row.best_stop:.2f}s", "fastest"),
                (f"{row.worst_stop:.2f}s", "slowest")],
} for place, row in enumerate(stops.sort_values("median_stop").itertuples(), start=1)])

# ---------- tyres over the season ----------

compounds = get_compound_use(season)
if not compounds.empty:
    section("Which tyres each team ran",
        "Laps completed on each compound across the season.")
    note("Teams that spend longer on the hard tyre are usually looking after it to make "
         "a one-stop work.")
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
        sheet([("Driver", "text"), ("Lap", "num"), ("Stationary", "num")],
              [[r.driver_name, int(r.lap_number), f"{r.pit_duration:.2f}s"]
               for r in race_stops.sort_values("pit_duration").itertuples()])

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
