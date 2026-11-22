"""Lap Simulator: our physics model drives a real circuit, next to the real fastest lap."""
import streamlit as st

import app_sim as A
from app_data import get_race_file, get_race_info
from scene_env import env_for
from sim3d import lap_view
from style import stat_strip
from ui_kit import section
import lapsim

folder = A.pick_race("lapsim")
info = get_race_info(folder)
cal = A.get_calibration()[folder]
track = A.get_track(folder)
car = A.calibrated(folder)
sim = A.run_car(folder, A.car_key(car))
track_df = get_race_file(folder, "track")
real = lapsim.real_trace(track_df, track)
real_t, real_s = lapsim.real_progress(track_df, track)

gap = sim["lap_time"] - real["lap_time"]
stat_strip([
    ("Simulated lap", A.lap_str(sim["lap_time"]), "our physics model", True),
    ("Real fastest lap", A.lap_str(real["lap_time"]), f"{info['race_name']} {info['season']}", False),
    ("Lap time gap", f"{gap:+.3f}s", "after calibration", False),
    ("Speed gap", f"{cal['speed_rmse_kmh']:.0f} km/h", "average, all the way round", False),
])

# ---------- the 3D lap ----------
section("Watch both laps", "Red is the simulated car, the other is the real fastest lap of the race. "
        "The track is coloured by what limits the simulated car at each point.")
real_colour = "#f5f5f7" if st.session_state.dark else "#15151e"
lap_view(
    A.three_track(track, [A.MODE_COLOURS[m] for m in sim["mode"]], A.MODE_LEGEND),
    [A.sim_car(sim, "SIM", A.SIM_COLOUR),
     {"name": "REAL", "colour": real_colour, "t": real_t, "s": real_s}],
    labels=A.corner_labels(folder, track), dark=st.session_state.dark, env=env_for(folder),
    note="Hills shown 4× higher",
)

# ---------- speed trace ----------
section("Speed all the way round", "Where the lines split, the simulator and the real car "
        "disagree. Dotted lines mark the corners.")
st.altair_chart(A.speed_chart([("Simulated", A.SIM_COLOUR, sim["s"], sim["speed_kmh"]),
                               ("Real", "#8a8a96", sim["s"], real["speed_kmh"])],
                              marks=A.corner_marks(folder, track)), use_container_width=True)

share = {m: float((sim["mode"] == m).mean()) for m in A.MODE_COLOURS}
time_share = {m: float(((sim["mode"] == m) * (sim["s"][1] - sim["s"][0]) / sim["speed"]).sum()
                       / sim["lap_time"]) for m in A.MODE_COLOURS}
stat_strip([
    ("Full throttle", f"{time_share['throttle']:.0%}", f"of the lap time ({share['throttle']:.0%} of the distance)", False),
    ("Cornering on the limit", f"{time_share['corner']:.0%}", f"of the lap time ({share['corner']:.0%} of the distance)", False),
    ("Braking", f"{time_share['brake']:.0%}", f"of the lap time ({share['brake']:.0%} of the distance)", False),
])

# ---------- the calibrated car ----------
facts = A.car_facts(car, track.rho)
section("The car the simulator found", "The settings that make the simulated lap match the real one "
        "best. Change any of them in the Setup Garage.")
stat_strip([
    ("Power", f"{car.power_kw:.0f} kW", f"about {facts['hp']:.0f} hp at the wheels", False),
    ("Downforce at 250 km/h", f"{facts['downforce_kn']:.1f} kN",
     f"{facts['downforce_x_weight']:.1f}× the car's weight", False),
    ("Drag at 300 km/h", f"{facts['drag_kn']:.1f} kN", f"wing level {car.wing:.2f} (0 low, 1 high)", False),
    ("Tyre grip", f"{car.grip:.2f}", "friction coefficient at the car's weight", False),
])
st.caption(f"Air density here: {track.rho:.3f} kg/m³ "
           f"({'thin air at altitude, so less downforce and drag' if track.rho < 1.1 else 'close to sea level'}). "
           f"Track length measured from the data: {track.length / 1000:.3f} km.")

with st.expander("How the simulator works"):
    st.markdown("""
At every point of the lap the car is treated as a single point with a mass, tyre grip,
downforce, drag and an engine. Three passes find its speed:

1. **Corner limit.** In a corner the tyres must push the car sideways with a force of
   *mass × speed² × curvature*. They can give *grip × load*, and the load is the car's
   weight **plus its downforce**, which grows with speed². So faster corners get more grip.
2. **Forward pass.** Out of every corner the car accelerates as hard as the engine and the
   rear tyres allow, minus drag, rolling resistance and any slope.
3. **Backward pass.** Into every corner it brakes as late as the tyres allow.

The speed at each point is the lowest of the three. The tyres share their grip between
turning and braking or accelerating (the *friction circle*), and grip grows a little more
slowly than the load on the tyre (*load sensitivity*).

**Calibration.** For each race, the wing level, the grip and the power are tuned until the
simulated speed matches the real fastest lap as closely as possible. That's why the lap
times agree so well: the honest test is the *shape* of the speed trace, shown above.
""")
with st.expander("What the simulator can't tell you"):
    st.markdown("""
- It is a point mass: no suspension, weight transfer, yaw, kerbs or driver.
- Banking isn't modelled, so the simulated car is too slow through banked corners such as
  Zandvoort's Turns 3 and 14.
- No DRS, no energy limits per lap, no gears in the physics, constant power at every speed.
- The wing level moves downforce and drag together on one fixed curve; real wings each have their own.
- Wing level, grip and power trade off against each other in the fit. A high grip with a low
  wing can look much like the reverse, so read them as *one consistent car*, not as what the
  team really ran.
- The real lap is the race's fastest lap: race fuel, worn tyres and maybe DRS.
""")
