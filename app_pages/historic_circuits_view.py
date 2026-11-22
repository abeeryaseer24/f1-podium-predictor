"""Historic Circuits: old layouts rebuilt in 3D, with a 1975, a 2001 and a 2026 car racing round them."""
import json

import numpy as np
import streamlit as st

import app_sim as A
import historic_circuits as H
import lapsim
from sim3d import lap_view
from style import stat_strip
from ui_kit import chips, section


@st.cache_data(ttl=86400)
def summary():
    path = H.HIST / "summary.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


@st.cache_resource(ttl=86400)
def track(key):
    return H.track_of(key)


@st.cache_data(ttl=86400)
def laps(key):
    """Every era's lap round this circuit, from the cars saved in summary.json."""
    s, tr = summary(), track(key)
    out = {}
    for era, e in s["eras"].items():
        car = lapsim.Car(**{**e["car"], "wing": s["circuits"][key]["laps"][era]["wing"]})
        out[era] = lapsim.simulate(car, tr)
    return out


s = summary()
if not s or not s["circuits"]:
    st.info("The historic circuits haven't been built yet.")
    st.stop()

names = {k: v["name"] for k, v in s["circuits"].items()}
key = st.selectbox("Circuit", list(names), format_func=names.get, key="hist_circuit")
c = s["circuits"][key]
chips([(c["years"], "#e10600"), (f"{c['length_km']:.1f} km", "#8a8a96"), (f"{c['climb_m']} m of climb", "#8a8a96")])
st.markdown(c["note"] + (" " + c["record"] if c["record"] else ""))

eras = s["eras"]
stat_strip([(eras[e]["label"], A.lap_str(v["lap"]), f"{v['avg_kmh']:.0f} km/h average · top {v['top_kmh']}", i == 0)
            for i, (e, v) in enumerate(c["laps"].items())])

tr = track(key)
sims = laps(key)
newest = list(sims)[-1]
section("Three eras, one lap", "The 1975, 2001 and 2026 cars start together. The track is coloured by what limits "
        "the 2026 car. Try Onboard, and press Play.")
lap_view(A.three_track(tr, [A.MODE_COLOURS[m] for m in sims[newest]["mode"]], A.MODE_LEGEND),
         [A.sim_car(sim, era, eras[era]["colour"]) for era, sim in sims.items()],
         dark=st.session_state.dark, height=520, note="Hills shown 4× higher")

section("Speed all the way round", "Where the newer cars gain: the corners, more than the straights.")
st.altair_chart(A.speed_chart([(eras[e]["label"], eras[e]["colour"], sim["s"], sim["speed_kmh"])
                               for e, sim in sims.items()]), use_container_width=True)

fits = "; ".join(f"the {eras[e]['label']} matches {eras[e]['benchmark']}" for e in eras if eras[e].get("fitted"))
untuned = [eras[e]["label"] for e in eras if eras[e]["fit"] and not eras[e].get("fitted")]
if untuned:
    fits += f" (the {', '.join(untuned)} uses a typical grip until its benchmark circuit is added)"
st.caption(f"How it's built: the track shape comes from OpenStreetMap (© OpenStreetMap contributors, ODbL) and the "
           f"heights from the EU-DEM elevation model through OpenTopoData. The lap simulator drives a line that may "
           f"stray 2 m from the road's centre, roughly a racing line. Each older car has one tuned number, its tyre "
           f"grip: {fits}. The 2026 car is the middle of every 2026 car calibrated to a real circuit, so its laps here "
           f"are a what-if, never raced. The Engineering Academy's Module 13 tells these circuits' stories.")
