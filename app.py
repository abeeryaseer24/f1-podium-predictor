"""Entry point: the top menu, the header, the theme switch and the footer.
Every page lives in app_pages/. To add a page, add one st.Page line to PAGES
and one line to TAGLINES."""
import sys
from pathlib import Path

import streamlit as st

# Let every page find the files inside src/
sys.path.append(str(Path(__file__).parent / "src"))
from style import apply_style, hero

st.set_page_config(page_title="Podium Predictor", page_icon="🏁", layout="wide")


# ---------- the top menu: new pages get added here as they're built ----------

PAGES = {
    "": [                                   # no group: shows as a plain "Home" link
        st.Page("app_pages/home.py", title="Home", default=True),
    ],
    "Predictor": [
        st.Page("app_pages/podium_predictor.py", title="Podium Predictor"),
        st.Page("app_pages/scoreboard.py", title="Scoreboard"),
        st.Page("app_pages/season_rewind.py", title="Season Rewind"),
    ],
    "Teams": [
        st.Page("app_pages/constructor_standings.py", title="Constructor Standings"),
        st.Page("app_pages/team_cards.py", title="Team Cards"),
        st.Page("app_pages/team_performance.py", title="Team Performance"),
        st.Page("app_pages/reliability.py", title="Reliability"),
        st.Page("app_pages/pit_strategy.py", title="Pit and Strategy"),
        st.Page("app_pages/power_units.py", title="Power Units"),
        st.Page("app_pages/upgrades.py", title="Upgrades"),
    ],
    "Drivers": [
        st.Page("app_pages/driver_standings.py", title="Driver Standings"),
        st.Page("app_pages/driver_cards.py", title="Driver Cards"),
        st.Page("app_pages/driver_ratings.py", title="Driver Ratings"),
        st.Page("app_pages/teammate_battles.py", title="Teammate Battles"),
    ],
       "Race": [
        st.Page("app_pages/pit_wall.py", title="Pit Wall"),
        st.Page("app_pages/ghost_lap_duel.py", title="Ghost Lap Duel"),
        st.Page("app_pages/circuit_explorer.py", title="Circuit Explorer"),
        st.Page("app_pages/tyre_lab.py", title="Tyre Lab"),
    ],
    "Games": [
        st.Page("app_pages/beat_the_ai.py", title="Beat the AI"),
        st.Page("app_pages/race_engineer.py", title="Be the Race Engineer"),
    ],
    "About": [
        st.Page("app_pages/about.py", title="About"),
    ],
}
page = st.navigation(PAGES, position="top")


# ---------- one line under the title, for each page ----------

TAGLINES = {
    "Home": "Formula 1 predictions, replays and games, live every race weekend.",
    "Podium Predictor": "Pick a Formula 1 race and see who the model puts on the podium.",
    "Scoreboard": "Every prediction, locked in before the race and scored after it.",
    "Season Rewind": "A whole season, race by race, as our model would have called it.",
    "Constructor Standings": "The teams' championship, and the charts behind every point.",
    "Team Cards": "Every team on the grid. Tap one to open its own page.",
    "Team Performance": "How fast each car really was, measured from the lap times.",
    "Reliability": "How often each team's cars reached the finish, and what stopped the rest.",
    "Pit and Strategy": "Who is quickest in the pit box, and which tyres each team chose.",
    "Power Units": "Engine parts used, and how close each driver is to a grid penalty.",
    "Upgrades": "Where the lap times show a car stepped forward, and what each team brought.",
    "Driver Standings": "The drivers' championship, race by race.",
    "Driver Cards": "Every driver on the grid. Tap one to open their own page.",
    "Driver Ratings": "Each driver's form through the season, with and without the car.",
    "Teammate Battles": "Same car, same weekend: who is winning inside each garage.",
    "Ghost Lap Duel": "Two drivers' fastest laps, head to head, all the way round.",
    "Circuit Explorer": "Every circuit in its real shape and elevation. "
                        "Hills are shown 4× higher so you can see them.",
    "Tyre Lab": "How fast each tyre wears, measured from every clean racing lap.",
    "Pit Wall": "Watch any race back, lap by lap, with every car on the real track.",
    "Be the Race Engineer": "Make the pit calls for a real driver in a real race. Can you beat their team?",
    "Beat the AI": "Pick the podium before the race. After it, see if you beat our model.",
    "About": "Everything behind the app: the model, how it is tested, and the robot that runs it.",
}


# ---------- header, with the theme switch on the right ----------

if "dark" not in st.session_state:
    st.session_state.dark = True

title_col, switch_col = st.columns([5, 1], vertical_alignment="center")
with title_col:
    hero("Podium Predictor" if page.title == "Home" else page.title, TAGLINES.get(page.title, ""))
with switch_col:
    st.toggle("Dark theme", key="dark")

apply_style(st.session_state.dark)


# ---------- the chosen page ----------

page.run()

