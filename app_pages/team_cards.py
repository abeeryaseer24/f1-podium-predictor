"""Team Cards: every team on the grid as a card. Tap one to open that team's own page,
painted in their colour."""
import streamlit as st

import team_profile
from app_garage import default_season, get_constructor_table, get_entries, get_seasons
from cards import cards_css, note, team_card
from predictor import clean_name
from style import empty_note, team_info
from teaminfo import team_meta

PICKED = "garage_team"
PER_ROW = 3

cards_css()

seasons = get_seasons()
if not seasons:
    empty_note("No results have been downloaded yet.")
    st.stop()

if "garage_season" not in st.session_state:
    st.session_state.garage_season = default_season()

# ---------- a team is open: show its page instead of the cards ----------

if st.session_state.get(PICKED):
    if st.button("← Back to all teams"):
        st.session_state[PICKED] = None
        st.rerun()
    team_profile.show(st.session_state[PICKED], st.session_state.garage_season)
    st.stop()

# ---------- otherwise: the grid of cards ----------

season = st.selectbox("Season", seasons,
                      index=seasons.index(st.session_state.garage_season)
                      if st.session_state.garage_season in seasons else 0)
st.session_state.garage_season = season

table = get_constructor_table(season)
entries = get_entries(season)
if table.empty:
    empty_note(f"No results for {season} yet.")
    st.stop()

note("Tap a team to see who runs it, what it has won, every driver it has had, and where "
     "its cars are built.")

teams = list(table.itertuples())
for start in range(0, len(teams), PER_ROW):
    columns = st.columns(PER_ROW)
    for column, row in zip(columns, teams[start:start + PER_ROW]):
        with column:
            meta = team_meta(row.constructor)
            drivers = entries[entries["constructor"] == row.constructor]["driver"]
            line_up = ", ".join(clean_name(d).split()[-1] for d in drivers)
            st.markdown(team_card(
                row.constructor,
                rank=int(row.position),
                lines=[line_up or "—", meta["engine"] and f'{meta["engine"]} power'],
                numbers=[(f"{row.points:.0f}", "Points"),
                         (int(row.wins), "Wins"),
                         (int(row.podiums), "Podiums")],
            ), unsafe_allow_html=True)
            if st.button(f'Open {team_info(row.constructor)[0]}',
                         key=f"team_{row.constructor}", width="stretch"):
                st.session_state[PICKED] = row.constructor
                st.rerun()
