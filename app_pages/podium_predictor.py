"""Podium Predictor page: pick a race -> the model's predicted order -> the reveal."""
import streamlit as st

from app_data import get_past_races, get_reasons, get_upcoming, run_past, run_upcoming
from predictor import current_season
from style import driver_rows, picks, podium, score, steps, tag, why_cards


# ---------- remember which screen the user is on ----------

if "screen" not in st.session_state:
    st.session_state.screen = "pick"


def go(screen):
    st.session_state.screen = screen


# ---------- Screen 1: pick a race ----------

def screen_pick():
    steps(1)
    season_now = current_season()

    mode = st.radio("What do you want to predict?",
                    ["Past race", f"Upcoming {season_now} race"], horizontal=True)

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
        upcoming = get_upcoming(season_now)
        if upcoming.empty:
            st.info(f"No races left in the {season_now} season.")
            return
        names = dict(zip(upcoming["round"], upcoming["race_name"]))
        rnd = st.selectbox("Race", list(names.keys()),
                           format_func=lambda r: f"Round {r} · {names[r]}")
        st.session_state.choice = ("upcoming", season_now, int(rnd))

    st.write("")
    st.button("Predict the podium →", type="primary", on_click=go, args=("predict",))

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
         "note": f'{r["podium_chance"]:.0f}% podium · {r["win_chance"]:.0f}% win'}
        for _, r in table.head(3).iterrows()
    ])

    with st.expander("Why this pick?"):
        st.caption("The biggest reasons the model rates each driver this highly, compared with the rest of "
                   "the field. Longer bar = bigger reason.")
        why_cards(table, get_reasons(kind, season, rnd))

    st.subheader("The predicted finishing order")
    st.caption("Big number: chance of a podium. Small number: chance of winning. The model replays "
               "the race 5,000 times with the right amount of luck, so podium chances add up to "
               "exactly 3 drivers and win chances to 100%.")
    driver_rows(table, 0, 10)
    if len(table) > 10:
        with st.expander(f"Show positions 11–{len(table)}"):
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

    st.subheader("The whole order: predicted vs real")
    finished = table.dropna(subset=["finish_position"])
    model_off = (finished["finish_position"] - finished["predicted_position"]).abs().mean()
    grid_rank = finished["grid"].rank(method="first")
    grid_off = (finished["finish_position"] - grid_rank).abs().mean()
    st.caption(f"On average the model's order was {model_off:.1f} places off. "
               f"Simply copying the starting grid would have been {grid_off:.1f} places off.")
    driver_rows(table, 0, 10, real=True)
    if len(table) > 10:
        with st.expander(f"Show positions 11–{len(table)}"):
            driver_rows(table, 10, len(table), real=True)

    st.caption("The model has already seen this race's result, so this is not a fair test. "
               "The fair tests are on the About page.")
    st.page_link("app_pages/about.py", label="How the model is tested fairly →")

    back, again = st.columns(2)
    back.button("← Back to prediction", on_click=go, args=("predict",))
    again.button("Try another race", type="primary", on_click=go, args=("pick",))


# ---------- show the current screen ----------

SCREENS = {"pick": screen_pick, "predict": screen_predict, "reveal": screen_reveal}
SCREENS[st.session_state.screen]()
