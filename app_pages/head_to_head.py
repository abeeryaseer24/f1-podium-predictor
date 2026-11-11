"""Head to Head: any two drivers from any era, side by side."""
import streamlit as st

from app_archive import get_driver_index, get_head_to_head, require_history
from cards import cards_css, head_to_head as h2h_bar, note
from style import empty_note

LEFT, RIGHT = "#e10600", "#27f4d2"

cards_css()
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

st.subheader("Careers, side by side")
rows = [
    ("Championships", a["titles"], b["titles"]),
    ("Race wins", a["wins"], b["wins"]),
    ("Podiums", a["podiums"], b["podiums"]),
    ("Poles", a["poles"], b["poles"]),
    ("Race starts", a["starts"], b["starts"]),
    ("Career points", int(a["points"]), int(b["points"])),
]
blocks = [h2h_bar(label, "whole career", a["name"], b["name"], left, right, LEFT, RIGHT)
          for label, left, right in rows]
st.markdown(f'<div class="pp-h2h">{"".join(blocks)}</div>', unsafe_allow_html=True)

st.subheader("When they raced each other")
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
    blocks = [
        h2h_bar("Finished ahead", meta, a["name"], b["name"],
                result["ahead_a"], result["ahead_b"], LEFT, RIGHT),
        h2h_bar("Started ahead", "on the grid", a["name"], b["name"],
                result["grid_a"], result["grid_b"], LEFT, RIGHT),
    ]
    st.markdown(f'<div class="pp-h2h">{"".join(blocks)}</div>', unsafe_allow_html=True)
    note("<b>Finished ahead</b> only counts races where both drivers reached the finish, "
         "so one car breaking down does not hand the other a free win. It compares two "
         "drivers in different cars, which is why the teammate rows on the "
         "<b>Teammate Battles</b> page are a fairer test of the driver alone.")

st.subheader("The numbers in full")
st.dataframe(
    {"": ["Raced", "Teams", "Nationality", "Best finish", "Titles", "Wins", "Podiums",
          "Poles", "Starts", "Points"],
     a["name"]: [f'{a["first_season"]}–{a["last_season"]}', ", ".join(a["teams"][:4]),
                 a["nationality"], f'P{a["best_finish"]}', a["titles"], a["wins"],
                 a["podiums"], a["poles"], a["starts"], f'{a["points"]:,.0f}'],
     b["name"]: [f'{b["first_season"]}–{b["last_season"]}', ", ".join(b["teams"][:4]),
                 b["nationality"], f'P{b["best_finish"]}', b["titles"], b["wins"],
                 b["podiums"], b["poles"], b["starts"], f'{b["points"]:,.0f}']},
    hide_index=True, width="stretch")
note("Career points are not comparable across eras: a win was worth 8 points in 1950 and "
     "is worth 25 now, and seasons are far longer than they were.")
