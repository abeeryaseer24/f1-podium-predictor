"""Be the Race Engineer: you make the pit calls for one driver in a real race,
and see whether you beat the real team and our strategist."""
import streamlit as st

from app_data import get_game, get_prepared_races, get_race_file, get_replay
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

with st.spinner("Getting the race ready..."):
    try:
        data = get_replay(folder)
        pack = get_game(folder)
    except Exception as error:
        st.error(f"Couldn't get this race ready: {error}")
        st.stop()

if pack is None:
    st.info("This race had rain, and the game only works for dry races so far. Pick another race.")
    st.stop()

# drivers you can engineer, in the order they really finished
order = sorted(pack["finish"], key=lambda f: (-f["laps"], f["end"]))
real_pos = {f["number"]: i + 1 for i, f in enumerate(order)}
cars = {c["number"]: c for c in data["cars"]}
playable = sorted((int(n) for n in pack["drivers"] if int(n) in cars), key=lambda n: real_pos.get(n, 99))

left, right = st.columns([2, 1])
driver = left.selectbox("Your driver", playable,
                        format_func=lambda n: f"{cars[n]['code']} · {cars[n]['name']} (really finished P{real_pos.get(n, '?')})")
mode = right.radio("Difficulty", ["Normal", "Hard"], horizontal=True,
                   help="Normal: our strategist gives hints and you can see the real car. Hard: no hints, no real car.")

game = dict(pack, driver=str(driver), mode=mode.lower(), folder=folder, raceName=names[folder].split(" · ", 1)[1])
pit_wall_view(data, get_race_file(folder, "track"), strategy=None, dark=st.session_state.dark, game=game)

st.caption("Pick the tyres, then press BOX to call your driver in. Everyone else races exactly as they did "
           "in reality, so your result is simulated: your car does the real driver's lap times with the tyre "
           "effect taken out, plus what your tyres cost and your pit stops.")
