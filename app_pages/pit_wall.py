"""Pit Wall: watch any race back, with every car on the real 3D track."""
import streamlit as st

from app_data import get_prepared_races, get_race_file, get_replay
from track3d import replay_view

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
    except Exception as error:
        st.error(f"Couldn't build a replay for this race: {error}")
        st.stop()

replay_view(data, get_race_file(folder, "track"), dark=st.session_state.dark)
st.caption("Car positions come from OpenF1, once per second. Cars in the pit lane are shown "
           "on the track next to it. Click a driver in the leaderboard to highlight and follow them.")