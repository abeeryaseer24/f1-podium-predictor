"""Circuit Explorer: any circuit in 3D, in its real shape and elevation."""
import streamlit as st

from app_data import get_prepared_races, get_race_file, get_race_info
from track3d import circuit_view

st.subheader("Circuit Explorer")
st.write("Every circuit in its real shape, traced from the fastest lap of the race. "
         "Hills are shown 4× higher than real so you can see them.")

races = get_prepared_races()
if races.empty:
    st.info("No circuits prepared yet. The robot adds a few every 3 hours.")
    st.stop()

# ---------- pick a circuit ----------
seasons = sorted(races["season"].unique().tolist(), reverse=True)
left, right = st.columns(2)
season = left.selectbox("Season", seasons)
in_season = races[races["season"] == season].sort_values("round")
names = {r.folder: f"Round {r.round} · {r.race_name}" for r in in_season.itertuples()}
folder = right.selectbox("Circuit", list(names), format_func=names.get)
colour_by = st.radio("Colour the track by", ["Speed", "Gear"], horizontal=True)

# ---------- the 3D view ----------
track = get_race_file(folder, "track")
info = get_race_info(folder)
circuit_view(track, colour_by=colour_by.lower(), dark=st.session_state.dark)

# ---------- fastest-lap facts ----------
laps = get_race_file(folder, "laps")
clean = laps[laps["lap_duration"].notna() & ~laps["is_pit_out_lap"].fillna(False).astype(bool)]
best = clean.nsmallest(1, "lap_duration").iloc[0]
driver = next((d for d in info["drivers"] if d["number"] == int(best["driver_number"])), {})
minutes, seconds = divmod(best["lap_duration"], 60)
length_km = (track[["x", "y"]].diff().pow(2).sum(axis=1) ** 0.5).sum() / 10_000
height_m = (track["z"].max() - track["z"].min()) / 10

c1, c2, c3, c4 = st.columns(4)
c1.metric("Fastest lap", f"{int(minutes)}:{seconds:06.3f}")
c2.metric("Set by", (driver.get("name") or "Unknown").title())
c3.metric("Top speed", f"{track['speed'].max():.0f} km/h")
c4.metric("Height difference", f"{height_m:.0f} m")
st.caption(f"Track length measured from the data: about {length_km:.2f} km. "
           "Shape and speed come from OpenF1's data for the race's fastest lap.")