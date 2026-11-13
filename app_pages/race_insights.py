"""Race Insights: the weather, the flags and the position-swapping behind any race
since 2023."""
import altair as alt
import streamlit as st

from app_garage import first_prepared, get_prepared_seasons, get_seasons
from app_insights import (get_control, get_overtaking, get_places_from_grid,
                          get_position_flow, get_prepared_races, get_weather,
                          get_weather_summary)
from cards import cards_css, figures, glass, key_values, note
from charts import dress, team_scale
from predictor import clean_name
from style import empty_note, stat_strip, team_info
from ui_kit import diverge, feed, kit_css, section

cards_css()
kit_css()

# One colour per kind of race control message, so the feed can be skimmed by its stripes.
MESSAGE_COLOUR = {
    "Red flag": "#c0202a", "Safety car": "#e8b33a", "Disqualified": "#c0202a",
    "Penalty given": "#e4544a", "Reprimand": "#e8b33a",
    "Warning or black and white flag": "#e8b33a", "Lap time deleted": "#6fa8dc",
    "Under investigation": "#a98ae0", "No further action": "#1fd6a0",
    "Chequered flag": "#f3f1ea", "DRS": "#27f4d2", "Flag or track status": "#8a8a96",
}

seasons = get_seasons()
season = st.selectbox("Season", seasons, index=seasons.index(first_prepared(seasons)))
races = get_prepared_races(season)

if not races:
    empty_note(f"Nothing prepared for {season} yet.")
    ready = [s for s in get_prepared_seasons() if s in seasons]
    if ready:
        note("This page reads lap-by-lap data, which only exists for seasons the robot "
             f"has prepared. Ready so far: <b>{', '.join(str(s) for s in ready)}</b>. "
             "Pick one of those above.")
    else:
        note("This page reads lap-by-lap data, and none of it has been prepared yet. "
             "It appears on its own once the robot has run.")
    st.stop()

labels = {f'Round {rnd} · {name}': (folder, rnd) for rnd, name, folder in races}
pick = st.selectbox("Race", list(labels), index=len(labels) - 1)
folder, round_number = labels[pick]

summary = get_weather_summary(folder)
overtaking = get_overtaking(folder)
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

section("The weather through the race",
        "Track and air temperature from the start of the session to the flag.")
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

section("Every position, lap by lap",
        "One line per driver. Higher line = further ahead.")
flow = get_position_flow(folder)
if flow.empty:
    empty_note("No lap-by-lap positions for this race.")
else:
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

moves = get_places_from_grid(season, round_number, folder)
if not moves.empty:
    section("Places won and lost from the grid",
            "Where each driver started on the grid against where they finished. A bar "
            "to the right is places made up, a bar to the left is places lost.")
    diverge([{
        "name": clean_name(row.driver),
        "sub": f'P{int(row.grid)} on the grid, finished P{int(row.finish_position)}'
               + ("" if row.finished else f' · {row.status.lower()}'),
        "colour": team_info(row.constructor)[1],
        "value": int(row.places_gained),
    } for row in moves.itertuples()])
    note("Measured from the official starting grid, so a move at the first corner counts "
         "the way you saw it. It does not separate overtaking from pit stops and cars "
         "retiring ahead, but it does show who went forwards.")

if overtaking.get("leaders"):
    figures([(overtaking["lead_changes"], "Lead changes"),
             (len(set(overtaking["leaders"])), "Drivers who led"),
             (overtaking["laps"], "Laps")])
    note("Led in order: " + " → ".join(overtaking["leaders"]))

# ---------- race control ----------

if not control.empty:
    section("What race control said",
        "Every message of the afternoon, grouped by what kind of message it was.")
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
        items = []
        for row in control.itertuples():
            lap = getattr(row, "lap_number", None)
            lap_text = "" if str(lap) in ("nan", "<NA>", "None") else int(lap)
            items.append({"lap": lap_text, "lap_label": "lap", "chip": row.kind,
                          "colour": MESSAGE_COLOUR.get(row.kind, "#8a8a96"),
                          "who": row.driver_name or "", "text": row.message})
        feed([{"title": pick.split(" · ")[-1],
               "meta": f"{len(items)} messages, in the order they were sent",
               "items": items}])

note("The <b>Penalties Log</b> page pulls the stewards' decisions out of these messages "
     "and adds them up across the season.")
