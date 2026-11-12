"""Reliability: how often each team's cars reached the finish, and which weekends they
lost them at.

There used to be a chart and a table of retirement *reasons* here. The results feed
stopped naming them a few seasons ago — every retirement now comes back as the single
word "Retired" — so for a recent season those were two pictures of nothing. The causes
are still shown for the older seasons that have them, and for the rest the page shows
which races the cars were lost at instead, which is real and more use anyway.
"""
import streamlit as st

from app_garage import (default_season, get_dnf_grid, get_reasons_recorded,
                        get_reliability, get_seasons)
from cards import cards_css, note
from charts import cause_bars
from style import empty_note, stat_strip, team_info
from ui_kit import chip, heat, kit_css, league, section

cards_css()
kit_css()

seasons = get_seasons()
season = st.selectbox("Season", seasons, index=seasons.index(default_season()))
summary, causes = get_reliability(season)

if summary.empty:
    empty_note(f"No results for {season} yet.")
    st.stop()

best = summary.iloc[0]
worst = summary.iloc[-1]
total_dnfs = int(summary["dnfs"].sum())
total_entries = int(summary["entries"].sum())

stat_strip([
    ("Most reliable", team_info(best["constructor"])[0],
     f'{best["finish_rate"]:.0f}% of cars finished', True),
    ("Least reliable", team_info(worst["constructor"])[0],
     f'{worst["finish_rate"]:.0f}% of cars finished', False),
    ("Cars that stopped", str(total_dnfs), f"out of {total_entries} starts", False),
    ("Across the field", f'{100 * (1 - total_dnfs / max(total_entries, 1)):.0f}%',
     "of all cars were classified", False),
])

note("A car counts as finishing if it was classified at the end, including cars a lap or "
     "more down. Everything else, from an engine letting go to a first-lap crash, counts "
     "as not finishing.")

# ---------- the league ----------

section("The reliability league",
        "Every team by the share of its cars that reached the finish. The bar is the "
        "finish rate itself, so a short bar is a long season in the garage.")
league([{
    "pos": place,
    "name": team_info(row.constructor)[0],
    "colour": team_info(row.constructor)[1],
    "sub": f'{int(row.finishes)} classified from {int(row.entries)} starts',
    "bar": float(row.finish_rate) / 100,
    "tag": (chip("perfect", "#1fd6a0") if row.dnfs == 0 else ""),
    "figures": [(f'{row.finish_rate:.0f}%', "finished"),
                (int(row.dnfs), "stopped"),
                (int(row.entries), "starts")],
} for place, row in enumerate(summary.itertuples(), start=1)])

# ---------- which weekends ----------

grid = get_dnf_grid(season)
if not grid.empty:
    section("Where the cars were lost",
            "Every team against every race. Green is both cars home, amber is one "
            "car lost, red is a double retirement. Three reds in a row is a pattern; "
            "one is usually somebody else's mistake.")
    rounds = sorted(grid["round"].unique())
    names = {r: team_info(r)[0] for r in grid["constructor"].unique()}
    order = [team_info(row.constructor)[0] for row in summary.itertuples()]
    colours = {team_info(row.constructor)[0]: team_info(row.constructor)[1]
               for row in summary.itertuples()}
    titles = {}
    cells = {}
    for row in grid.itertuples():
        label = f"R{row.round}"
        titles[label] = row.race_name
        team = names.get(row.constructor, row.constructor)
        text = "—" if row.dnfs == 0 else str(int(row.dnfs))
        goodness = 1.0 if row.dnfs == 0 else (0.45 if row.dnfs == 1 else 0.0)
        cells[(team, label)] = (text, goodness)
    heat(order, [f"R{r}" for r in rounds], cells,
         legend=("Both cars lost", "Both cars home"),
         row_colours=colours, column_titles=titles)
    note("A dash means both cars were classified. Scroll the grid sideways on a phone.")

# ---------- why, when the feed says why ----------

recorded = get_reasons_recorded(season)
if recorded >= 3 and not causes.empty:
    section("Why the others stopped",
            "The feed writes the reason in many different words. They are grouped here "
            "into a handful of plain ones, so 'Power Unit', 'Engine' and 'Turbo' all "
            "land together.")
    st.altair_chart(cause_bars(causes), width="stretch", theme=None)
else:
    section("Why the others stopped",
            "Not something we can show for this season, and it is worth saying why.")
    st.markdown(
        f'<div class="kt-chips">{chip("no reasons published", "#8a8a96")}</div>',
        unsafe_allow_html=True)
    note("The results feed used to say what broke — gearbox, engine, suspension, "
         f"collision. For {season} it returns the single word <i>Retired</i> for almost "
         "every car, so a chart of causes would be one bar saying nothing. Pick an "
         "older season from the box at the top and the real reasons appear. The grid "
         "above is built from which cars finished, which is recorded properly, so it "
         "is right either way.")
