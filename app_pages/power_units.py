"""Power Units: how many engine parts each driver has used, and how close they are to
a grid penalty.

There is no free API for this. The FIA publishes it as a PDF after each race, so the
changes are logged by hand in data/power_units.csv and this page counts them up.
"""
import streamlit as st

from app_garage import PU_ALLOWANCE, default_season, get_power_units, get_seasons, power_unit_counts
from cards import cards_css, note
from predictor import clean_name
from style import empty_note, stat_strip, team_info
from ui_kit import chip, heat, kit_css, section, sheet

cards_css()
kit_css()

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

section("The 2026 rules",
        "A driver may use a set number of each part across the season. The first part "
        "over the limit costs <b>10 grid places</b>, and every part after that costs "
        "<b>5</b>. Penalties add up, and anything over 15 places means a start from "
        "the back.")
st.markdown('<div class="kt-chips">' + "".join(
    chip(f"{part} · {allowed}", "#6fa8dc") for part, allowed in PU_ALLOWANCE.items()
) + "</div>", unsafe_allow_html=True)

section("Where every driver stands",
        "Each driver against each part of the power unit, coloured by how much of "
        "their allowance is gone. Green means spare parts in hand; red means the next "
        "one costs grid places.")
show = counts.copy()
show["Driver"] = show["driver"].map(clean_name)
show["Team"] = show["constructor"].map(lambda t: team_info(t)[0])
parts = [c for c in PU_ALLOWANCE if c in set(show["component"])]
order, colours, cells = [], {}, {}
for row in show.sort_values(["Team", "Driver"]).itertuples():
    if row.Driver not in order:
        order.append(row.Driver)
        colours[row.Driver] = team_info(row.constructor)[1]
    allowed = max(int(row.allowance), 1)
    left = max(0, allowed - int(row.used))
    cells[(row.Driver, row.component)] = (f"{int(row.used)}/{allowed}",
                                          min(1.0, left / allowed))
heat(order, parts, cells, legend=("Out of parts", "Plenty left"),
     row_colours=colours, missing_label="no parts logged")
note("Each square is how many of that part the driver has used out of the allowance, "
     "counting the one the car started the season with.")

if not over.empty:
    section("Already past the limit",
            "Drivers who have used more of a part than the rules allow. The next one "
            "of that part costs them grid places.")
    warn = over.copy()
    warn["Driver"] = warn["driver"].map(clean_name)
    sheet([("Driver", "text"), ("Team", "tag"), ("Part", "text"), ("Used", "num"),
           ("Allowed", "num"), ("Next one costs", "text")],
          [[r.Driver, (team_info(r.constructor)[1], team_info(r.constructor)[0]),
            r.component, int(r.used), int(r.allowance),
            f"{int(r.next_penalty)} places"] for r in warn.itertuples()])

if not log.empty:
    section("Every change logged this season",
            "Each new part fitted, newest first, exactly as it was written into "
            "data/power_units.csv.")
    show_log = log.copy()
    show_log["Driver"] = show_log["driver"].map(clean_name)
    sheet([("Round", "num"), ("Driver", "text"), ("Part", "text"), ("Note", "wrap")],
          [[int(r.round), r.Driver, r.component, r.note]
           for r in show_log.sort_values("round", ascending=False).itertuples()])

# The instructions for keeping data/power_units.csv up to date used to sit here, in
# front of every visitor. They are maintenance notes, not something a reader of the
# page needs, so they live in About → The live system now.
