"""Power Units: how many engine parts each driver has used, and how close they are to
a grid penalty.

There is no free API for this. The FIA publishes it as a PDF after each race, so the
changes are logged by hand in data/power_units.csv and this page counts them up.
"""
import pandas as pd
import streamlit as st

from app_garage import PU_ALLOWANCE, default_season, get_power_units, get_seasons, power_unit_counts
from cards import cards_css, note
from predictor import clean_name
from style import empty_note, stat_strip, team_info

cards_css()

seasons = get_seasons()
season = st.selectbox("Season", seasons, index=seasons.index(default_season()))

log = get_power_units()
log = log[log["season"] == season] if not log.empty else log
counts = power_unit_counts(season)

if counts.empty:
    empty_note(f"No drivers found for {season}.")
    st.stop()

over = counts[counts["used"] > counts["allowance"]]
close = counts[(counts["used"] == counts["allowance"])]

stat_strip([
    ("Changes logged", str(len(log)), f"in {season}", True),
    ("Parts over the limit", str(len(over)), "each one cost a grid penalty", False),
    ("On their last part", str(len(close)), "one more means a penalty", False),
])

if log.empty:
    note("<b>Nothing has been logged for this season yet</b>, so every driver is shown on "
         "their first part of each type. That is almost certainly out of date. Add one row "
         "to <code>data/power_units.csv</code> for each new part fitted and this page will "
         "count them. The FIA publishes the list after every race weekend.")

st.subheader("The 2026 rules")
note("A driver may use a set number of each part across the season. The first part over "
     "the limit costs <b>10 grid places</b>, and every part after that costs <b>5</b>. "
     "Penalties add up, and anything over 15 places means a start from the back.")
st.dataframe(
    pd.DataFrame({"Part": list(PU_ALLOWANCE), "Allowed per season": list(PU_ALLOWANCE.values())}),
    hide_index=True, width="stretch")

st.subheader("Where every driver stands")
show = counts.copy()
show["Driver"] = show["driver"].map(clean_name)
show["Team"] = show["constructor"].map(lambda t: team_info(t)[0])
show["Used of allowed"] = show["used"].astype(str) + " of " + show["allowance"].astype(str)
grid = show.pivot_table(index=["Team", "Driver"], columns="component",
                        values="used", aggfunc="max")
order = [c for c in PU_ALLOWANCE if c in grid.columns]
st.dataframe(grid[order], width="stretch")
note("Each number is how many of that part the driver has used, counting the one the car "
     "started the season with. Compare it with the table above.")

if not over.empty:
    st.subheader("Already past the limit")
    warn = over.copy()
    warn["Driver"] = warn["driver"].map(clean_name)
    warn["Team"] = warn["constructor"].map(lambda t: team_info(t)[0])
    st.dataframe(
        warn[["Driver", "Team", "component", "used", "allowance", "next_penalty"]]
        .rename(columns={"component": "Part", "used": "Used", "allowance": "Allowed",
                         "next_penalty": "Next one costs (places)"}),
        hide_index=True, width="stretch")

if not log.empty:
    st.subheader("Every change logged this season")
    show_log = log.copy()
    show_log["Driver"] = show_log["driver"].map(clean_name)
    st.dataframe(
        show_log[["round", "Driver", "component", "note"]]
        .rename(columns={"round": "Round", "component": "Part", "note": "Note"})
        .sort_values("Round", ascending=False),
        hide_index=True, width="stretch")

st.subheader("How to keep this up to date")
note("Open <code>data/power_units.csv</code> and add one line for every new part a driver "
     "takes. The columns are "
     "<code>season, round, driver, constructor, component, note</code>. "
     "Use the driver id the rest of the app uses, for example <code>max_verstappen</code>, "
     "and spell the part exactly as it appears in the rules table above. "
     "The part the car started the season with is already counted, so only log changes.")
