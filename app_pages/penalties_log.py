"""Penalties Log: every stewards' decision of a season, as race control broadcast it.

The log used to be a spreadsheet that repeated the race name on every one of its rows
and cut the decision off at the edge of a phone. It is a feed now: one card per
incident, grouped under the race it happened at, which is how race control actually
sends them.
"""
import altair as alt
import streamlit as st

from app_garage import first_prepared, get_prepared_seasons, get_seasons
from app_insights import get_prepared_races, get_season_penalties
from cards import cards_css, note
from charts import dress
from insights import STEWARD_KINDS
from style import empty_note, stat_strip, team_info
from ui_kit import feed, kit_css, league, section

cards_css()
kit_css()

# A colour per kind of decision, so the feed can be read by its stripes alone.
KIND_COLOUR = {
    "Disqualified": "#c0202a",
    "Penalty given": "#e4544a",
    "Reprimand": "#e8b33a",
    "Warning or black and white flag": "#e8b33a",
    "Lap time deleted": "#6fa8dc",
    "Under investigation": "#a98ae0",
    "No further action": "#1fd6a0",
}
SHORT = {"Warning or black and white flag": "Warning",
         "Under investigation": "Investigating",
         "No further action": "No action",
         "Lap time deleted": "Lap deleted"}

seasons = get_seasons()
season = st.selectbox("Season", seasons, index=seasons.index(first_prepared(seasons)))
races = get_prepared_races(season)
log = get_season_penalties(season)

if log.empty:
    empty_note(f"No stewards' decisions found for {season}.")
    ready = [s for s in get_prepared_seasons() if s in seasons]
    if ready:
        note("Decisions are read from the race control messages broadcast during each "
             "race, which only exist for seasons the robot has prepared. Ready so far: "
             f"<b>{', '.join(str(s) for s in ready)}</b>. Pick one of those above.")
    else:
        note("Decisions are read from the race control messages broadcast during each "
             "race, and none of it has been prepared yet. It appears on its own once "
             "the robot has run.")
    st.stop()

given = log[log["kind"].isin(("Penalty given", "Disqualified"))]
investigated = log[log["kind"] == "Under investigation"]
deleted = log[log["kind"] == "Lap time deleted"]

stat_strip([
    ("Penalties given", str(len(given)), f'across {log["round"].nunique()} races', True),
    ("Incidents investigated", str(len(investigated)),
     "not all of them led to a penalty", False),
    ("Lap times deleted", str(len(deleted)), "mostly track limits", False),
    ("Races covered", f'{log["round"].nunique()} of {len(races)}',
     "races with files prepared", False),
])

note("These come from what race control actually broadcast during each race, so they "
     "cover in-race decisions. Penalties handed out after the chequered flag, and grid "
     "penalties announced on a Saturday, often do not appear in the race messages.")

# ---------- by driver ----------

named = log[log["driver_name"].astype(str) != ""]
counts = (named[named["kind"].isin(STEWARD_KINDS)]
          .dropna(subset=["constructor"])
          .groupby(["driver_name", "constructor"], as_index=False).size()
          .rename(columns={"size": "decisions"})
          .sort_values("decisions", ascending=False))
if not counts.empty:
    section("Who the stewards spoke to most",
            "Every driver race control named this season, most-mentioned first. A "
            "driver high on this list is not necessarily a dirty racer: an incident "
            "they were the victim of is logged against both cars.")
    worst = int(counts["decisions"].max())
    league([{
        "pos": place, "name": row.driver_name,
        "colour": team_info(row.constructor)[1],
        "sub": team_info(row.constructor)[0],
        "bar": row.decisions / worst,
        "figures": [(int(row.decisions), "decisions")],
    } for place, row in enumerate(counts.itertuples(), start=1)])

# ---------- by kind ----------

section("What kind of decision",
        "How the season's messages split between the stewards looking at something, "
        "letting it go, and actually punishing it.")
kinds = (log.groupby("kind", as_index=False).size()
         .rename(columns={"size": "count"}).sort_values("count", ascending=False))
most = int(kinds["count"].max())
league([{
    "pos": place, "name": row.kind,
    "colour": KIND_COLOUR.get(row.kind, "#8a8a96"),
    "sub": f'{100 * row.count / len(log):.0f}% of everything race control said',
    "bar": row.count / most,
    "figures": [(int(row.count), "messages")],
} for place, row in enumerate(kinds.itertuples(), start=1)], show_position=False)

# ---------- by race ----------

section("Which races the stewards were busiest at",
        "Decisions per round. A spike is usually one chaotic afternoon rather than a "
        "strict panel.")
per_race = (log.groupby(["round", "race_name"], as_index=False).size()
            .rename(columns={"size": "decisions"}).sort_values("round"))
chart = (alt.Chart(per_race).mark_bar(cornerRadiusEnd=4, color="#e10600")
         .encode(x=alt.X("round:O", title="Round"),
                 y=alt.Y("decisions:Q", title="Decisions",
                         axis=alt.Axis(tickMinStep=1, format="d")),
                 tooltip=[alt.Tooltip("race_name:N", title="Race"),
                          alt.Tooltip("decisions:Q", title="Decisions")]))
st.altair_chart(dress(chart).properties(height=300), width="stretch", theme=None)

# ---------- the log itself ----------

section("The log itself",
        "Every decision in the order it was broadcast, grouped under its race. Tap the "
        "chips to show only the kinds you care about.")
kind_filter = st.multiselect("Show", list(STEWARD_KINDS), default=list(STEWARD_KINDS))
shown = log[log["kind"].isin(kind_filter)] if kind_filter else log

if shown.empty:
    empty_note("Nothing matches that choice.")
    st.stop()

newest_first = sorted(shown["round"].unique(), reverse=True)
PER_PAGE = 6
if len(newest_first) > PER_PAGE:
    page_count = (len(newest_first) + PER_PAGE - 1) // PER_PAGE
    page = st.selectbox("Races", list(range(1, page_count + 1)),
                        format_func=lambda n: f"Races {n * PER_PAGE - PER_PAGE + 1}"
                                              f"–{min(n * PER_PAGE, len(newest_first))}"
                                              " (newest first)")
    chosen = newest_first[(page - 1) * PER_PAGE: page * PER_PAGE]
else:
    chosen = newest_first

groups = []
for rnd in chosen:
    block = shown[shown["round"] == rnd].sort_values("lap_number", na_position="first")
    items = []
    for row in block.itertuples():
        lap = "" if str(row.lap_number) in ("nan", "<NA>", "None") else int(row.lap_number)
        items.append({
            "lap": lap, "lap_label": "lap",
            "chip": SHORT.get(row.kind, row.kind),
            "colour": KIND_COLOUR.get(row.kind, "#8a8a96"),
            "who": row.driver_name or "",
            "text": row.message,
        })
    groups.append({"title": block.iloc[0]["race_name"],
                   "meta": f'Round {int(rnd)} · {len(block)} decision'
                           f'{"s" if len(block) != 1 else ""}',
                   "items": items})
feed(groups)
note("The wording is race control's own, copied straight from the message. A message "
     "with no lap number was sent before the race started or after it ended.")
