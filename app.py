import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Let the app find the files inside src/
sys.path.append(str(Path(__file__).parent / "src"))
from predictor import (past_races, upcoming_races, predict_past, predict_upcoming,
                       scoreboard, season_summary, clean_name, model_info)
from style import (apply_style, hero, steps, podium, driver_rows, score, picks, tag,
                   stat_tiles, race_card, show_cards, empty_note)

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


@st.cache_data(ttl=600)
def get_scoreboard(kind):
    return scoreboard(kind)


@st.cache_data(ttl=600)
def get_model_info():
    return model_info()


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


# ---------- Scoreboard page ----------

def race_cards(board, live):
    """Turn scoreboard rows into race cards (newest first for live, in order for backtest)."""
    cards = []
    for _, r in board.sort_values("round", ascending=not live).iterrows():
        done = r["status"] == "done"
        title = f'Round {int(r["round"])} · {r["race_name"]}'

        parts = []
        if live:
            locked = pd.to_datetime(r["predicted_at"]).strftime("%d %b, %H:%M UTC")
            parts.append(f"Locked in {locked}")
        if done:
            parts.append("Podium: " + ", ".join(clean_name(d) for d in r["actual"]))
        meta = " · ".join(parts)

        chips = []
        for i in (1, 2, 3):
            driver = r[f"p{i}"]
            if done:
                mark, extra = ("hit" if driver in r["actual"] else "miss"), None
            else:
                mark, extra = None, f'{r[f"p{i}_chance"]:.0f}%'
            chips.append({"name": clean_name(driver), "team": r[f"p{i}_team"],
                          "mark": mark, "extra": extra})

        cards.append(race_card(
            title, meta, chips,
            int(r["model_hits"]) if done else None,
            int(r["grid_hits"]) if done else None,
        ))
    return cards


def page_scoreboard():
    st.subheader("2026 live")
    st.write("Predictions are locked in after qualifying, before each race starts, "
             "and never changed afterwards.")
    live = get_scoreboard("live")
    if live.empty:
        empty_note("No locked predictions yet. The first one is saved right after "
                   "the next qualifying session.")
    else:
        stat_tiles(season_summary(live))
        show_cards(race_cards(live, live=True))

    st.subheader("2025 backtest")
    st.write("Every 2025 race, predicted by a model trained only on 2016–2024, "
             "so it never saw these results.")
    back = get_scoreboard("backtest")
    if back.empty:
        empty_note("No backtest yet. Run src/train.py to create it.")
    else:
        stat_tiles(season_summary(back))
        with st.expander(f"Show all {len(back)} races"):
            show_cards(race_cards(back, live=False))


# ---------- page layout ----------

with st.sidebar:
    st.header("Settings")
    st.toggle("Dark theme", value=True, key="dark")

apply_style(st.session_state.dark)
hero()

page = st.segmented_control("Page", ["Predict", "Scoreboard"], default="Predict",
                            key="page", label_visibility="collapsed")
st.write("")

if page == "Scoreboard":
    page_scoreboard()
else:
    screens = {"pick": screen_pick, "predict": screen_predict, "reveal": screen_reveal}
    screens[st.session_state.screen]()


# ---------- footer: which model is running ----------
info = get_model_info()
if info:
    last = info["last_race"]
    trained = pd.to_datetime(info["trained_at"]).strftime("%d %b %Y")
    st.write("")
    st.caption(f"Model trained on {trained}, using every race up to the "
               f"{last['race_name']} {last['season']} (round {last['round']}).")