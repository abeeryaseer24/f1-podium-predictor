"""Head to Head: any two drivers from any era, side by side.

Everything is a mirrored bar rather than a table, because the only question anyone
asks here is "who is further ahead, and by how much" — and a bar answers that before
you have read a single number.
"""
import streamlit as st

from app_archive import get_driver_index, get_head_to_head, require_history
from cards import cards_css, note
from style import empty_note, team_info
from ui_kit import chip, esc, fade, kit_css, section, versus

cards_css()
kit_css()
require_history()

index = get_driver_index()
if len(index) < 2:
    empty_note("Not enough drivers in the history files.")
    st.stop()

labels = {f'{row.driver_name} ({int(row.first_season)}–{int(row.last_season)})': row.driver
          for row in index.itertuples()}
keys = list(labels)

left_column, right_column = st.columns(2)
with left_column:
    a_label = st.selectbox("Driver", keys, index=0)
with right_column:
    b_label = st.selectbox("Against", keys, index=min(1, len(keys) - 1))

if labels[a_label] == labels[b_label]:
    empty_note("Pick two different drivers.")
    st.stop()

result = get_head_to_head(labels[a_label], labels[b_label])
a, b = result["a"], result["b"]

# Each driver wears the colour of the team they raced for most, which makes the bars
# mean something instead of being two arbitrary colours.
LEFT = team_info(a.get("team_id", ""))[1]
RIGHT = team_info(b.get("team_id", ""))[1]
if LEFT.lower() == RIGHT.lower():            # two Ferrari men would be unreadable
    LEFT, RIGHT = "#e10600", "#27f4d2"


def who_they_were(driver, colour):
    """A short profile in badges, instead of three rows of a table."""
    badges = [chip(driver["nationality"], colour),
              chip(f'{driver["first_season"]}–{driver["last_season"]}', colour),
              chip(f'Best finish P{driver["best_finish"]}', colour)]
    if driver["titles"]:
        badges.insert(0, chip(f'{driver["titles"]}× champion', "#d8b45a", solid=True))
    teams = "".join(chip(t, "#8a8a96") for t in driver["teams"][:6])
    more = (f'<span class="kt-chip" style="background:{fade("#8a8a96", .16)};'
            f'color:#8a8a96">+{len(driver["teams"]) - 6} more</span>'
            if len(driver["teams"]) > 6 else "")
    return (f'<div style="margin-bottom:10px"><div style="font-family:\'Saira Condensed\','
            f'sans-serif;font-weight:800;font-size:1.3rem;text-transform:uppercase;'
            f'color:{colour};line-height:1.1">{esc(driver["name"])}</div></div>'
            f'<div class="kt-chips">{"".join(badges)}</div>'
            f'<div class="kt-chips" style="margin-top:8px">{teams}{more}</div>')


section("Who they are",
        "Where each of them came from, how long they raced and who for.")
one, two = st.columns(2)
with one:
    st.markdown(f'<div class="pp-glass">{who_they_were(a, LEFT)}</div>',
                unsafe_allow_html=True)
with two:
    st.markdown(f'<div class="pp-glass">{who_they_were(b, RIGHT)}</div>',
                unsafe_allow_html=True)

# ---------- the totals ----------

section("Careers, side by side",
        "Every bar is measured against whichever of them has more, so the longer bar "
        "is the leader and the empty space is the gap.")
versus(a["name"], b["name"], [
    ("Titles", a["titles"], b["titles"], a["titles"], b["titles"]),
    ("Wins", a["wins"], b["wins"], a["wins"], b["wins"]),
    ("Podiums", a["podiums"], b["podiums"], a["podiums"], b["podiums"]),
    ("Poles", a["poles"], b["poles"], a["poles"], b["poles"]),
    ("Starts", a["starts"], b["starts"], a["starts"], b["starts"]),
    ("Points", a["points"], b["points"], f'{a["points"]:,.0f}', f'{b["points"]:,.0f}'),
], LEFT, RIGHT)
note("Career points are not comparable across eras: a win was worth 8 points in 1950 "
     "and is worth 25 now, and seasons are far longer than they were. The totals above "
     "also reward a long career, which is what the rates below take out.")

# ---------- the rates ----------


def rate(driver, key):
    return 100 * driver[key] / driver["starts"] if driver["starts"] else 0.0


section("The same career, per start",
        "A driver with more starts will win more races. These are the same records "
        "divided by how many Grands Prix each of them actually began, which is the "
        "fairer comparison when one career was much longer than the other.")
versus(a["name"], b["name"], [
    ("Win rate", rate(a, "wins"), rate(b, "wins"),
     f'{rate(a, "wins"):.1f}%', f'{rate(b, "wins"):.1f}%'),
    ("Podium rate", rate(a, "podiums"), rate(b, "podiums"),
     f'{rate(a, "podiums"):.1f}%', f'{rate(b, "podiums"):.1f}%'),
    ("Pole rate", rate(a, "poles"), rate(b, "poles"),
     f'{rate(a, "poles"):.1f}%', f'{rate(b, "poles"):.1f}%'),
    ("Finish rate", rate(a, "finishes"), rate(b, "finishes"),
     f'{rate(a, "finishes"):.1f}%', f'{rate(b, "finishes"):.1f}%'),
    ("Points per start", a["points"] / max(a["starts"], 1), b["points"] / max(b["starts"], 1),
     f'{a["points"] / max(a["starts"], 1):.1f}', f'{b["points"] / max(b["starts"], 1):.1f}'),
], LEFT, RIGHT, middle="per start")

# ---------- when they actually met ----------

section("When they raced each other",
        "Only the Grands Prix both of them started.")
if result["races_together"] == 0:
    empty_note(f'{a["name"]} and {b["name"]} never started the same Grand Prix.')
    note("They raced in different eras, so the career numbers above are the only honest "
         "comparison, and even those are shaped by very different cars, seasons and rules.")
else:
    seasons = result["seasons"]
    span = (f'{seasons[0]}' if len(seasons) == 1 else f'{seasons[0]} to {seasons[-1]}')
    meta = f'{result["races_together"]} races together, {span}'
    if result["as_teammates"]:
        meta += f' · {result["as_teammates"]} of them in the same team'
    note(meta)
    versus(a["name"], b["name"], [
        ("Finished ahead", result["ahead_a"], result["ahead_b"],
         result["ahead_a"], result["ahead_b"]),
        ("Started ahead", result["grid_a"], result["grid_b"],
         result["grid_a"], result["grid_b"]),
    ], LEFT, RIGHT, middle="met")
    note("<b>Finished ahead</b> only counts races where both drivers reached the finish, "
         "so one car breaking down does not hand the other a free win. It compares two "
         "drivers in different cars, which is why the teammate rows on the "
         "<b>Teammate Battles</b> page are a fairer test of the driver alone.")
