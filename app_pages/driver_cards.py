"""Driver Cards: every driver on the grid as a card, in their team's colour.
Tap one to open their own page."""
import streamlit as st

import driver_profile
from app_garage import default_season, get_driver_table, get_seasons
from cards import cards_css, driver_card, note
from predictor import clean_name
from style import empty_note

PICKED = "garage_driver"
PER_ROW = 3

cards_css()

seasons = get_seasons()
if not seasons:
    empty_note("No results have been downloaded yet.")
    st.stop()

if "garage_season" not in st.session_state:
    st.session_state.garage_season = default_season()

# ---------- a driver is open: show their page instead of the cards ----------

if st.session_state.get(PICKED):
    if st.button("← Back to all drivers"):
        st.session_state[PICKED] = None
        st.rerun()
    driver_profile.show(st.session_state[PICKED], st.session_state.garage_season)
    st.stop()

# ---------- otherwise: the grid of cards ----------

season = st.selectbox("Season", seasons,
                      index=seasons.index(st.session_state.garage_season)
                      if st.session_state.garage_season in seasons else 0)
st.session_state.garage_season = season

table = get_driver_table(season)
if table.empty:
    empty_note(f"No results for {season} yet.")
    st.stop()

note("Tap a driver to see their career, every teammate they have faced and how they "
     "race from where they start.")

drivers = list(table.itertuples())
for start in range(0, len(drivers), PER_ROW):
    columns = st.columns(PER_ROW)
    for column, row in zip(columns, drivers[start:start + PER_ROW]):
        with column:
            name = clean_name(row.driver)
            st.markdown(driver_card(
                name, row.constructor,
                number=None,
                rank=int(row.position),
                lines=[f'{int(row.entries)} races · best P{int(row.best_finish)}'],
                numbers=[(f"{row.points:.0f}", "Points"),
                         (int(row.wins), "Wins"),
                         (int(row.podiums), "Podiums")],
            ), unsafe_allow_html=True)
            if st.button(f"Open {name}", key=f"driver_{row.driver}", width="stretch"):
                st.session_state[PICKED] = row.driver
                st.rerun()
