"""Circuit Profiles: every track that has held a Grand Prix, and who has won there."""
import altair as alt
import pandas as pd
import streamlit as st

from app_archive import (get_circuit_history, get_circuit_index, get_circuit_winners,
                         require_history)
from cards import cards_css, figures, glass, key_values, note
from charts import dress, name_scale
from style import empty_note

cards_css()
require_history()

index = get_circuit_index()
if index.empty:
    empty_note("No circuits found in the history files.")
    st.stop()

labels = {f'{row.circuit_name} ({int(row.races)} race'
          f'{"s" if row.races != 1 else ""})': row.circuit
          for row in index.itertuples()}
note("Every circuit that has held a round of the world championship. The <b>Circuit "
     "Explorer</b> page under Race shows the recent ones in 3D, with their real shape and "
     "elevation.")
pick = st.selectbox("Circuit", list(labels))
circuit_id = labels[pick]

row = index[index["circuit"] == circuit_id].iloc[0]
by_driver, by_team = get_circuit_winners(circuit_id)
history = get_circuit_history(circuit_id)

st.subheader(row["circuit_name"])
figures([
    (int(row["races"]), "Races held"),
    (int(row["first_season"]), "First"),
    (int(row["last_season"]), "Most recent"),
    (len(by_driver) if not by_driver.empty else 0, "Different winners"),
    (len(by_team) if not by_team.empty else 0, "Winning teams"),
])

glass("Where it is", key_values([
    ("Circuit", row["circuit_name"]),
    ("Town", row["locality"]),
    ("Country", row["country"]),
    ("Seasons", f'{int(row["first_season"])} to {int(row["last_season"])}'),
]))

try:
    lat, lon = float(row["latitude"]), float(row["longitude"])
    st.map(pd.DataFrame({"lat": [lat], "lon": [lon]}), zoom=6)
except (TypeError, ValueError):
    note("No coordinates for this circuit in the archive.")

if not by_driver.empty:
    st.subheader("Most wins here, drivers")
    top = by_driver.head(15)
    chart = (alt.Chart(top).mark_bar(cornerRadiusEnd=4, color="#e10600")
             .encode(x=alt.X("wins:Q", title="Wins at this circuit",
                             axis=alt.Axis(tickMinStep=1, format="d")),
                     y=alt.Y("driver_name:N", sort=top["driver_name"].tolist(), title=None),
                     tooltip=[alt.Tooltip("driver_name:N", title="Driver"),
                              alt.Tooltip("wins:Q", title="Wins")]))
    st.altair_chart(dress(chart).properties(height=max(200, 26 * len(top))),
                    width="stretch", theme=None)

if not by_team.empty:
    st.subheader("Most wins here, constructors")
    top = by_team.head(15)
    chart = (alt.Chart(top).mark_bar(cornerRadiusEnd=4)
             .encode(x=alt.X("wins:Q", title="Wins at this circuit",
                             axis=alt.Axis(tickMinStep=1, format="d")),
                     y=alt.Y("constructor_name:N", sort=top["constructor_name"].tolist(),
                             title=None),
                     color=alt.Color("constructor_name:N",
                                     scale=name_scale(top["constructor_name"].tolist()),
                                     legend=None),
                     tooltip=[alt.Tooltip("constructor_name:N", title="Team"),
                              alt.Tooltip("wins:Q", title="Wins")]))
    st.altair_chart(dress(chart).properties(height=max(200, 26 * len(top))),
                    width="stretch", theme=None)

if not history.empty:
    st.subheader("Every winner here")
    st.dataframe(
        history.rename(columns={"season": "Season", "race_name": "Race",
                                "driver_name": "Winner", "constructor_name": "Team",
                                "date": "Date"}),
        hide_index=True, width="stretch")

st.subheader("All circuits")
st.dataframe(
    index[["circuit_name", "locality", "country", "races", "first_season", "last_season"]]
    .rename(columns={"circuit_name": "Circuit", "locality": "Town", "country": "Country",
                     "races": "Races held", "first_season": "First",
                     "last_season": "Most recent"}),
    hide_index=True, width="stretch")
