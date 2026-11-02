import sys
from pathlib import Path

import streamlit as st

# Let the app find the files inside src/
sys.path.append(str(Path(__file__).parent / "src"))
from predictor import past_races, upcoming_races, predict_past, predict_upcoming
from style import apply_style, hero, steps

st.set_page_config(page_title="Podium Predictor", page_icon="🏁", layout="wide")


# ---------- cached helpers (so slow work isn't repeated on every click) ----------

@st.cache_data
def get_past_races():
    return past_races()


@st.cache_data(ttl=3600)
def get_upcoming(season):
    return upcoming_races(season)


@st.cache_data
def run_past(season, rnd):
    return predict_past(season, rnd)


@st.cache_data(ttl=3600)
def run_upcoming(season, rnd):
    return predict_upcoming(season, rnd)


# ---------- remember which screen the user is on ----------

if "screen" not in st.session_state:
    st.session_state.screen = "pick"


def go(screen):
    st.session_state.screen = screen


def show_table(result):
    st.dataframe(
        result["table"][["name", "constructor", "grid", "podium_chance"]].head(10),
        hide_index=True,
        column_config={
            "name": "Driver",
            "constructor": "Team",
            "grid": "Grid",
            "podium_chance": st.column_config.NumberColumn(
                "Podium chance", format="%.1f%%"),
        },
    )


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

    steps(2, upcoming=(kind == "upcoming"))
    st.subheader(f"{result['race_name']} {season}")

    if kind == "upcoming":
        if result["real_quali"]:
            st.success("Using real qualifying results")
        else:
            st.warning("Qualifying hasn't happened yet, so the grid is estimated "
                       "from each driver's average qualifying this season")

    # Rough podium for now: P2 | P1 | P3 (the real graphic comes in Step 4)
    p1, p2, p3 = result["predicted"]
    left, middle, right = st.columns(3)
    left.markdown(f"**P2**  \n{p2}")
    middle.markdown(f"**P1**  \n{p1}")
    right.markdown(f"**P3**  \n{p3}")

    st.write("")
    show_table(result)

    back, forward = st.columns(2)
    back.button("← Pick another race", on_click=go, args=("pick",))
    if kind == "past":
        forward.button("Reveal the real result →", type="primary",
                       on_click=go, args=("reveal",))


# ---------- Screen 3: the reveal (past races only) ----------

def screen_reveal():
    kind, season, rnd = st.session_state.choice
    result = run_past(season, rnd)

    steps(3)
    st.subheader(f"{result['race_name']} {season}: how did the model do?")

    st.metric("Podium drivers predicted correctly", f"{result['correct']} of 3")

    actual_col, model_col = st.columns(2)
    with actual_col:
        st.markdown("**Real podium**")
        for i, driver in enumerate(result["actual"], start=1):
            st.write(f"P{i} · {driver}")
    with model_col:
        st.markdown("**Model's picks**")
        for driver in result["predicted"]:
            mark = "✅" if driver in result["actual"] else "❌"
            st.write(f"{mark} {driver}")

    with st.expander("How fair is this?"):
        st.write("The model learned from past races, including this one, so it has "
                 "already seen this result. On the 2025 season, which was kept hidden "
                 "during testing, it got 2.29 of 3 podium drivers right per race.")

    back, again = st.columns(2)
    back.button("← Back to prediction", on_click=go, args=("predict",))
    again.button("Try another race", type="primary", on_click=go, args=("pick",))


# ---------- page layout ----------

with st.sidebar:
    st.header("Settings")
    st.toggle("Dark theme", value=True, key="dark")

apply_style(st.session_state.dark)
hero()

screens = {"pick": screen_pick, "predict": screen_predict, "reveal": screen_reveal}
screens[st.session_state.screen]()