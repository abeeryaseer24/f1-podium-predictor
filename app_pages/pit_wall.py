"""Pit Wall: watch any race back with every car on the real 3D track,
plus the strategist's team radio and its verdict against the real teams."""
import streamlit as st

from app_data import get_prepared_races, get_race_file, get_replay, get_strategy
from pitwall3d import pit_wall_view

races = get_prepared_races()
if races.empty:
    st.info("No races prepared yet. The robot adds a few every 3 hours.")
    st.stop()

left, right = st.columns(2)
season = left.selectbox("Season", sorted(races["season"].unique().tolist(), reverse=True))
in_season = races[races["season"] == season].sort_values("round")
names = {r.folder: f"Round {r.round} · {r.race_name}" for r in in_season.itertuples()}
folder = right.selectbox("Race", list(names), format_func=names.get)

with st.spinner("Building the replay..."):
    try:
        data = get_replay(folder)
        strategy = get_strategy(folder)
    except Exception as error:
        st.error(f"Couldn't build a replay for this race: {error}")
        st.stop()

pit_wall_view(data, get_race_file(folder, "track"), strategy=strategy, dark=st.session_state.dark)

if strategy is None:
    st.caption("The strategist hasn't analysed this race yet. The robot adds it within a few hours.")
st.caption("Tap a driver in the leaderboard to hear their team radio: the strategist's plan, the countdown "
           "and the BOX call. The strategist only knows what has happened up to each lap. "
           "Car positions come from OpenF1, once per second; cars in the pit lane are shown on the track next to it.")