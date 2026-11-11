"""Teammate Battles: who is winning inside each garage, across qualifying, the race,
the points and reliability."""
import streamlit as st

from app_garage import default_season, get_seasons, get_teammate_battles
from cards import accent, cards_css, head_to_head, note
from predictor import clean_name
from style import empty_note, stat_strip, team_info

cards_css()

seasons = get_seasons()
season = st.selectbox("Season", seasons, index=seasons.index(default_season()))
battles = get_teammate_battles(season)

if battles.empty:
    empty_note(f"No teammate pairs found for {season}.")
    st.stop()

dark = st.session_state.get("dark", True)
closest = battles.assign(
    margin=(battles["quali_a"] - battles["quali_b"]).abs()).sort_values("margin").iloc[0]
biggest = battles.assign(
    margin=(battles["points_a"] - battles["points_b"]).abs()).sort_values(
    "margin", ascending=False).iloc[0]

stat_strip([
    ("Pairs racing", str(len(battles)), f"in {season}", True),
    ("Closest in qualifying", team_info(closest["constructor"])[0],
     f'{int(closest["quali_a"])} – {int(closest["quali_b"])}', False),
    ("Biggest points gap", team_info(biggest["constructor"])[0],
     f'{abs(biggest["points_a"] - biggest["points_b"]):.0f} points apart', False),
])

note("Only rounds where both drivers took part are counted. The race row counts only the "
     "races where both cars were classified at the end, so one car breaking down does not "
     "hand the other a free win.")

for row in battles.itertuples():
    team_name, colour = team_info(row.constructor)
    a_name, b_name = clean_name(row.driver_a), clean_name(row.driver_b)
    left, right = accent(colour, dark), "#8a8a96"
    st.subheader(team_name)
    blocks = [
        head_to_head("Qualifying", f"{row.races_together} races together",
                     a_name, b_name, row.quali_a, row.quali_b, left, right),
        head_to_head("Finished ahead", "both cars classified",
                     a_name, b_name, row.race_a, row.race_b, left, right),
        head_to_head("Points", "this season", a_name, b_name,
                     int(row.points_a), int(row.points_b), left, right),
        head_to_head("Races not finished", "lower is better", a_name, b_name,
                     int(row.dnf_a), int(row.dnf_b), left, right),
    ]
    st.markdown(f'<div class="pp-h2h">{"".join(blocks)}</div>', unsafe_allow_html=True)
