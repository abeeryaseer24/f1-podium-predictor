import sys
from pathlib import Path

import streamlit as st

# Let the app find the files inside src/
sys.path.append(str(Path(__file__).parent / "src"))
from predictor import past_races, upcoming_races, predict_past, predict_upcoming

st.set_page_config(page_title="Podium Predictor", page_icon="🏁", layout="wide")


# ---------- cached helpers (so the app doesn't redo slow work on every click) ----------

@st.cache_data
def get_past_races():
    return past_races()


@st.cache_data(ttl=3600)          # re-check the calendar once an hour
def get_upcoming(season):
    return upcoming_races(season)


@st.cache_data(ttl=3600)
def run_upcoming(season, rnd):
    return predict_upcoming(season, rnd)


# ---------- sidebar ----------

with st.sidebar:
    st.header("Settings")
    dark = st.toggle("Dark theme", value=True)
    mode = st.radio("What do you want to see?", ["Past race", "Upcoming 2026 race"])


# ---------- main page ----------

st.title("Podium Predictor")

if mode == "Past race":
    races = get_past_races()

    seasons = sorted(races["season"].unique().tolist(), reverse=True)
    season = st.selectbox("Season", seasons)

    season_races = races[races["season"] == season]
    names = dict(zip(season_races["round"], season_races["race_name"]))
    rnd = st.selectbox("Race", list(names.keys()),
                       format_func=lambda r: f"Round {r} · {names[r]}")

    result = predict_past(int(season), int(rnd))

    st.subheader(f"{result['race_name']} {season}")
    st.write("**Predicted podium:**", ", ".join(result["predicted"]))
    st.write("**Actual podium:**", ", ".join(result["actual"]))
    st.write(f"**Correct:** {result['correct']} of 3")
    st.caption("The model learned from races up to 2026 round 19, including this one, "
               "so past races look a little easier than a true blind test. "
               "On 2025, which it had never seen, it got 2.29 of 3 per race.")

else:
    upcoming = get_upcoming(2026)

    if upcoming.empty:
        st.info("No races left in the 2026 season.")
        st.stop()

    names = dict(zip(upcoming["round"], upcoming["race_name"]))
    rnd = st.selectbox("Race", list(names.keys()),
                       format_func=lambda r: f"Round {r} · {names[r]}")

    with st.spinner("Asking the model..."):
        result = run_upcoming(2026, int(rnd))

    st.subheader(f"{result['race_name']} 2026")
    if result["real_quali"]:
        st.success("Using real qualifying results")
    else:
        st.warning("Qualifying hasn't happened yet, so the grid is estimated "
                   "from each driver's average qualifying this season")
    st.write("**Predicted podium:**", ", ".join(result["predicted"]))

st.dataframe(
    result["table"][["name", "constructor", "grid", "podium_chance"]].head(10),
    hide_index=True,
)