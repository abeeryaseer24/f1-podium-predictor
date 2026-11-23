"""Team Radio: every published radio message of a race, transcribed and sorted by topic."""
import altair as alt
import pandas as pd
import streamlit as st

import race_story as R
import team_radio as TR
from app_data import get_prepared_races, get_race_file, get_race_info
from charts import dress
from style import stat_strip
from ui_kit import feed, section

MIN_CALLS = 30          # don't quote a percentage from a handful of clips
TOPIC_COLOURS = {"Pit stop call": "#e10600", "Tyres": "#e8b33a", "Weather": "#2b6cff", "Car problem": "#ff7a1a",
                 "Incident or penalty": "#c04dff", "Celebration": "#1fd6a0", "Pace and gaps": "#27c2f4",
                 "Other": "#8a8a96"}


@st.cache_data(ttl=600)
def radio_races():
    races = get_prepared_races()
    if races.empty:
        return races
    has = races["folder"].map(lambda f: (R.RACES_DIR / f / "team_radio.parquet").exists())
    return races[has]


@st.cache_data(ttl=600)
def box_check():
    """Across every transcribed race: how often a 'box' call is followed by a real stop within 2 laps."""
    hits = total = 0
    for folder in radio_races()["folder"]:
        radio = get_race_file(folder, "team_radio")
        pits = get_race_file(folder, "pits")
        said = radio["text"].fillna("")
        calls = radio[said.str.contains(r"\bbox\b", case=False, regex=True)
                      & ~said.str.contains("retire", case=False)]
        for _, c in calls.iterrows():
            stops = pits[pits["driver_number"] == c["driver_number"]]["lap_number"]
            total += 1
            hits += bool(((stops >= c["lap"]) & (stops <= c["lap"] + 2)).any())
    return hits, total


races = radio_races()
if races.empty:
    st.info("No race has its team radio transcribed yet. The robot adds a few after each run.")
    st.stop()

seasons = sorted(races["season"].unique().tolist(), reverse=True)
c1, c2 = st.columns(2)
season = c1.selectbox("Season", seasons)
in_season = races[races["season"] == season].sort_values("round")
names = {r.folder: f"Round {r.round} · {r.race_name}" for r in in_season.itertuples()}
folder = c2.selectbox("Race", list(names), index=len(names) - 1, format_func=names.get)

radio = get_race_file(folder, "team_radio").copy()
info = get_race_info(folder)
who = R.drivers(info)
radio["code"] = radio["driver_number"].map(lambda n: who.get(int(n), {}).get("code", str(n)))
radio["text"] = radio["text"].fillna("").replace("", "(no words recognised)")

c3, c4 = st.columns(2)
codes = sorted(radio["code"].unique().tolist())
pick_drivers = c3.multiselect("Drivers", codes, placeholder="Everyone")
pick_topics = c4.multiselect("Topics", list(TOPIC_COLOURS), placeholder="Every topic")
shown = radio
if pick_drivers:
    shown = shown[shown["code"].isin(pick_drivers)]
if pick_topics:
    shown = shown[shown["topic"].isin(pick_topics)]

hits, total = box_check()
top_topic = radio[radio["topic"] != TR.OTHER]["topic"].value_counts()
stat_strip([
    ("Radio messages", f"{len(radio)}", f"published from the {info['race_name']}", True),
    ("Most talked about", top_topic.index[0] if len(top_topic) else "–",
     f"{int(top_topic.iloc[0])} messages" if len(top_topic) else "", False),
    ("Most on the radio", radio["code"].value_counts().index[0], f"{int(radio['code'].value_counts().iloc[0])} messages", False),
    ("'Box' calls that led to a stop", f"{hits / total:.0%}" if total >= MIN_CALLS else "Too few yet",
     f"within 2 laps, {total} calls across {len(races)} races" if total >= MIN_CALLS
     else f"{total} 'box' calls published so far; shown from {MIN_CALLS}", False),
])

# ---------- timeline ----------
section("The race on the radio", "Every published message by lap and driver, coloured by topic. Hover for the words.")
radio_chart = alt.Chart(shown).mark_circle(size=120, opacity=.9).encode(
    x=alt.X("lap:Q", title="Lap"), y=alt.Y("code:N", title=None, sort=codes),
    color=alt.Color("topic:N", scale=alt.Scale(domain=list(TOPIC_COLOURS), range=list(TOPIC_COLOURS.values())),
                    legend=alt.Legend(orient="top", title=None, columns=4)),
    tooltip=[alt.Tooltip("code:N", title="Driver"), alt.Tooltip("lap:Q", title="Lap"),
             alt.Tooltip("topic:N", title="Topic"), alt.Tooltip("text:N", title="Said")])
st.altair_chart(dress(radio_chart).properties(height=max(260, 22 * shown["code"].nunique())),
                use_container_width=True)

# ---------- the messages ----------
section("Every message", "Automatic transcripts: names and engineering slang are often misheard. "
        "Listen links play Formula 1's own recording.")
items = [{"lap": int(r.lap), "chip": r.topic, "colour": TOPIC_COLOURS.get(r.topic, "#8a8a96"),
          "who": f"{r.code} · {who.get(int(r.driver_number), {}).get('team', '')}", "text": r.text,
          "link": (r.url, "Listen")} for r in shown.sort_values("t").itertuples()]
if items:
    feed([{"title": f"{info['race_name']} {info['season']}", "meta": f"{len(items)} messages", "items": items}])
else:
    st.caption("Nothing matches those filters.")

