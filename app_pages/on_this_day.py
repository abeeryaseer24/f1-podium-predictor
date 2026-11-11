"""On This Day: the Grands Prix that were run on today's date, in any year."""
from datetime import date

import streamlit as st

from app_archive import get_on_this_day, require_history
from cards import cards_css, note
from style import empty_note, stat_strip

cards_css()
require_history()

today = date.today()
picked = st.date_input("Date", value=today, format="DD/MM/YYYY")
if isinstance(picked, (list, tuple)):
    picked = picked[0] if picked else today

races = get_on_this_day(picked.month, picked.day)
pretty = picked.strftime("%d %B")

if races.empty:
    empty_note(f"No Grand Prix has ever been run on {pretty}.")
    note("There are only about twenty race days in a year, so most dates come up empty. "
         "Try a Sunday in the middle of the season.")
    st.stop()

newest = races.iloc[0]
stat_strip([
    ("Races on this date", str(len(races)), pretty, True),
    ("Most recent", str(int(newest["season"])), newest["race_name"], False),
    ("Oldest", str(int(races["season"].min())),
     races.iloc[-1]["race_name"], False),
])

st.subheader(f"On {pretty}")
for row in races.itertuples():
    st.markdown(
        f'**{int(row.season)} · {row.race_name}** — won by **{row.driver_name}** '
        f'for {row.constructor_name}.')

st.subheader("The same thing as a table")
st.dataframe(
    races[["season", "race_name", "driver_name", "constructor_name", "date"]]
    .rename(columns={"season": "Season", "race_name": "Race", "driver_name": "Winner",
                     "constructor_name": "Team", "date": "Date"}),
    hide_index=True, width="stretch")

note("Only the race winner is listed. Pick any other date above to see what happened then.")
