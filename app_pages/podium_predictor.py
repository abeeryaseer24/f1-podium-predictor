"""Podium Predictor page: pick a race -> the model's prediction -> the reveal."""
import streamlit as st

from app_data import get_past_races, get_upcoming, run_past, run_upcoming
from style import driver_rows, picks, podium, score, steps, tag


# ---------- remember which screen the user is on ----------

if "screen" not in st.session_state:
    st.session_state.screen = "pick"


def go(screen):
    st.session_state.screen = screen


# ---------- Screen 1: pick a race ----------

def screen_pick():
    steps(1)

    mode = st.radio("What do you want to predict?",
                    ["Past race", "Upcoming 2026 race"], horizontal=True)

    if mode == "Past race":
        races = get_past_races()
        seasons = sorted(races["season"].unique().tolist(), reverse=True)
        season = st.selectbox("Season", seasons)

        season_races = races[races["season"] == season]
        names = dict(zip(season_races["round"], season_races["race_name"]))
        rnd = st.selectbox("Race", list(names.keys()),
                           format_func=lambda r: f"Round {r} · {names[r]}")
        st.session_state.choice = ("past", int(season), int(rnd))

    else:
        upcoming = get_upcoming(2026)
        if upcoming.empty:
            st.info("No races left in the 2026 season.")
            return
        names = dict(zip(upcoming["round"], upcoming["race_name"]))
        rnd = st.selectbox("Race", list(names.keys()),
                           format_func=lambda r: f"Round {r} · {names[r]}")
        st.session_state.choice = ("upcoming", 2026, int(rnd))

    st.write("")
    st.button("Predict the podium →", type="primary", on_click=go, args=("predict",))


# ---------- Screen 2: the model's prediction ----------

def screen_predict():
    kind, season, rnd = st.session_state.choice
    with st.spinner("Asking the model..."):
        result = run_past(season, rnd) if kind == "past" else run_upcoming(season, rnd)
    table = result["table"]

    steps(2, upcoming=(kind == "upcoming"))
    st.subheader(f"{result['race_name']} {season}")

    if kind == "upcoming":
        if result["real_quali"]:
            st.success("Using real qualifying results")
        else:
            st.warning("Qualifying hasn't happened yet, so the grid is estimated "
                       "from each driver's average qualifying this season")

    podium([
        {"name": r["name"], "team": r["constructor"],
         "note": f'{r["podium_chance"]:.1f}% chance'}
        for _, r in table.head(3).iterrows()
    ])

    st.subheader("Every driver's chance")
    driver_rows(table, 0, 10)
    if len(table) > 10:
        with st.expander("Show the rest of the grid"):
            driver_rows(table, 10, len(table))

    back, forward = st.columns(2)
    back.button("← Pick another race", on_click=go, args=("pick",))
    if kind == "past":
        forward.button("Reveal the real result →", type="primary",
                       on_click=go, args=("reveal",))


# ---------- Screen 3: the reveal (past races only) ----------

def screen_reveal():
    kind, season, rnd = st.session_state.choice
    result = run_past(season, rnd)
    table = result["table"]
    team_of = dict(zip(table["name"], table["constructor"]))

    steps(3)
    st.subheader(f"{result['race_name']} {season}: how did the model do?")
    score(result["correct"])

    st.subheader("The real podium")
    podium([
        {"name": name, "team": team_of[name], "note": tag(name in result["predicted"])}
        for name in result["actual"]
    ])

    st.subheader("The model's picks")
    picks(result["predicted"], result["actual"], team_of)

    with st.expander("How fair is this?"):
        st.write("The model learned from past races, including this one, so it has "
                 "already seen this result. For an honest test, open the Scoreboard: "
                 "it shows predictions locked in before each 2026 race, and a 2025 "
                 "backtest by a model that never saw those races.")

    back, again = st.columns(2)
    back.button("← Back to prediction", on_click=go, args=("predict",))
    again.button("Try another race", type="primary", on_click=go, args=("pick",))


# ---------- show the current screen ----------

SCREENS = {"pick": screen_pick, "predict": screen_predict, "reveal": screen_reveal}
SCREENS[st.session_state.screen]()