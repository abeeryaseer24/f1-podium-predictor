"""Race Insights: the weather, the flags and the position-swapping behind any race
since 2023."""
import altair as alt
import streamlit as st

from app_garage import default_season, get_seasons
from app_insights import (get_control, get_movers, get_overtaking, get_position_flow,
                          get_prepared_races, get_weather, get_weather_summary)
from cards import cards_css, figures, glass, key_values, note
from charts import dress, team_scale
from style import empty_note, stat_strip, team_info

cards_css()

seasons = get_seasons()
season = st.selectbox("Season", seasons, index=seasons.index(default_season()))
races = get_prepared_races(season)

if not races:
    empty_note(f"No prepared race files for {season}.")
    note("This page reads the race files in <code>data/races/</code>, which the robot "
         "builds from OpenF1 and which start in 2023. If the season is recent, its races "
         "may not have been prepared yet.")
    st.stop()

labels = {f'Round {rnd} · {name}': folder for rnd, name, folder in races}
pick = st.selectbox("Race", list(labels), index=len(labels) - 1)
folder = labels[pick]

summary = get_weather_summary(folder)
overtaking = get_overtaking(folder)
movers = get_movers(folder)
control = get_control(folder)

stat_strip([
    ("Conditions", "Wet" if summary.get("wet") else "Dry",
     f'track {summary["track"]["average"]:.0f}°C' if "track" in summary else "", True),
    ("Places changed", str(overtaking.get("places_changed", 0)),
     f'over {overtaking.get("laps", 0)} laps', False),
    ("Lead changes", str(overtaking.get("lead_changes", 0)),
     f'{len(overtaking.get("leaders", []))} driver(s) led', False),
    ("Race control messages", str(len(control)), "flags, stewards and more", False),
])

# ---------- weather ----------

st.subheader("The weather through the race")
table = get_weather(folder)
if table.empty:
    empty_note("No weather readings for this race.")
else:
    if summary:
        glass("Conditions", key_values([
            ("Air temperature",
             f'{summary["air"]["low"]:.0f} to {summary["air"]["high"]:.0f} °C'
             if "air" in summary else ""),
            ("Track temperature",
             f'{summary["track"]["low"]:.0f} to {summary["track"]["high"]:.0f} °C'
             if "track" in summary else ""),
            ("Humidity", f'{summary["humidity"]["average"]:.0f}%'
             if "humidity" in summary else ""),
            ("Wind", f'{summary["wind"]["average"]:.1f} m/s average'
             if "wind" in summary else ""),
            ("Rain", "Yes, at some point" if summary.get("wet") else "None recorded"),
        ]))
    have = [c for c in ("air_temperature", "track_temperature") if c in table.columns]
    if have:
        melted = table.melt(id_vars="minute", value_vars=have,
                            var_name="reading", value_name="celsius")
        melted["reading"] = melted["reading"].map(
            {"air_temperature": "Air", "track_temperature": "Track"})
        chart = (alt.Chart(melted).mark_line(strokeWidth=2.5)
                 .encode(x=alt.X("minute:Q", title="Minutes into the session"),
                         y=alt.Y("celsius:Q", title="Degrees C",
                                 scale=alt.Scale(zero=False)),
                         color=alt.Color("reading:N", title=None,
                                         scale=alt.Scale(domain=["Track", "Air"],
                                                         range=["#e10600", "#27f4d2"])),
                         tooltip=[alt.Tooltip("minute:Q", title="Minute", format=".0f"),
                                  "reading",
                                  alt.Tooltip("celsius:Q", title="°C", format=".1f")]))
        st.altair_chart(dress(chart), width="stretch", theme=None)
    note("The track is almost always hotter than the air, and it cools through an evening "
         "race. A falling track temperature makes the tyres harder to switch on and "
         "changes what the strategists do.")

# ---------- position flow ----------

st.subheader("Every position, lap by lap")
flow = get_position_flow(folder)
if flow.empty:
    empty_note("No lap-by-lap positions for this race.")
else:
    note("One line per driver. Lower on the chart is further up the road. Flat lines are "
         "a procession; crossing lines are the racing.")
    top = int(flow["position"].max())
    scale = team_scale(sorted(flow["constructor"].dropna().unique()))
    data = flow.dropna(subset=["constructor"]).copy()
    data["Team"] = data["constructor"].map(lambda t: team_info(t)[0])
    chart = (alt.Chart(data).mark_line(strokeWidth=2)
             .encode(x=alt.X("lap_number:Q", title="Lap"),
                     y=alt.Y("position:Q", title="Position",
                             scale=alt.Scale(domain=[top + 0.5, 0.5]),
                             axis=alt.Axis(tickMinStep=1, format="d")),
                     color=alt.Color("Team:N", scale=scale, title=None),
                     detail="driver_name:N",
                     tooltip=[alt.Tooltip("driver_name:N", title="Driver"), "Team",
                              alt.Tooltip("lap_number:Q", title="Lap"),
                              alt.Tooltip("position:Q", title="Position")]))
    st.altair_chart(dress(chart).properties(height=420), width="stretch", theme=None)

# ---------- who gained ----------

if not movers.empty:
    st.subheader("Who made up ground")
    note("Position at the end of the first recorded lap against the finish. It does not "
         "separate overtaking from pit stops and retirements ahead, but it does show who "
         "went forwards.")
    data = movers.dropna(subset=["constructor"]).copy()
    data["Team"] = data["constructor"].map(lambda t: team_info(t)[0])
    chart = (alt.Chart(data).mark_bar(cornerRadiusEnd=4)
             .encode(x=alt.X("places_gained:Q", title="Places gained"),
                     y=alt.Y("driver_name:N", sort=data["driver_name"].tolist(),
                             title=None),
                     color=alt.Color("Team:N",
                                     scale=team_scale(sorted(data["constructor"].unique())),
                                     legend=None),
                     tooltip=[alt.Tooltip("driver_name:N", title="Driver"), "Team",
                              alt.Tooltip("early_position:Q", title="Early on"),
                              alt.Tooltip("final_position:Q", title="Finished"),
                              alt.Tooltip("places_gained:Q", title="Gained")]))
    st.altair_chart(dress(chart).properties(height=max(240, 26 * len(data))),
                    width="stretch", theme=None)

if overtaking.get("leaders"):
    figures([(overtaking["lead_changes"], "Lead changes"),
             (len(set(overtaking["leaders"])), "Drivers who led"),
             (overtaking["laps"], "Laps")])
    note("Led in order: " + " → ".join(overtaking["leaders"]))

# ---------- race control ----------

if not control.empty:
    st.subheader("What race control said")
    counts = (control.groupby("kind", as_index=False).size()
              .rename(columns={"size": "messages"}).sort_values("messages",
                                                                ascending=False))
    chart = (alt.Chart(counts).mark_bar(cornerRadiusEnd=4, color="#e10600")
             .encode(x=alt.X("messages:Q", title="Messages",
                             axis=alt.Axis(tickMinStep=1, format="d")),
                     y=alt.Y("kind:N", sort=counts["kind"].tolist(), title=None),
                     tooltip=["kind", "messages"]))
    st.altair_chart(dress(chart).properties(height=max(180, 30 * len(counts))),
                    width="stretch", theme=None)
    with st.expander("Every message, in order"):
        st.dataframe(
            control[["lap_number", "kind", "driver_name", "message"]]
            .rename(columns={"lap_number": "Lap", "kind": "Kind",
                             "driver_name": "Driver", "message": "Message"}),
            hide_index=True, width="stretch")

note("The <b>Penalties Log</b> page pulls the stewards' decisions out of these messages "
     "and adds them up across the season.")
