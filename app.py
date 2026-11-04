"""Entry point: the top menu, the header, the theme switch and the footer.
Every page lives in app_pages/. To add a page, add one st.Page line to PAGES
and one line to TAGLINES."""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Let every page find the files inside src/
sys.path.append(str(Path(__file__).parent / "src"))
from app_data import get_model_info
from style import apply_style, hero

st.set_page_config(page_title="Podium Predictor", page_icon="🏁", layout="wide")


# ---------- the top menu: new pages get added here as they're built ----------

PAGES = {
    "Predictor": [
        st.Page("app_pages/podium_predictor.py", title="Podium Predictor", default=True),
        st.Page("app_pages/scoreboard.py", title="Scoreboard"),
    ],
       "Race": [
        st.Page("app_pages/pit_wall.py", title="Pit Wall"),
        st.Page("app_pages/ghost_lap_duel.py", title="Ghost Lap Duel"),
        st.Page("app_pages/circuit_explorer.py", title="Circuit Explorer"),
        st.Page("app_pages/tyre_lab.py", title="Tyre Lab"),
    ],
    
}
page = st.navigation(PAGES, position="top")


# ---------- one line under the title, for each page ----------

TAGLINES = {
    "Podium Predictor": "Pick a Formula 1 race and see who the model puts on the podium.",
    "Scoreboard": "Every prediction, locked in before the race and scored after it.",
    "Ghost Lap Duel": "Two drivers' fastest laps, head to head, all the way round.",
    "Circuit Explorer": "Every circuit in its real shape and elevation. "
                        "Hills are shown 4× higher so you can see them.",
    "Tyre Lab": "How fast each tyre wears, measured from every clean racing lap.",
        "Pit Wall": "Watch any race back, lap by lap, with every car on the real track.",
}


# ---------- header, with the theme switch on the right ----------

if "dark" not in st.session_state:
    st.session_state.dark = True

title_col, switch_col = st.columns([5, 1], vertical_alignment="center")
with title_col:
    hero(page.title, TAGLINES.get(page.title, ""))
with switch_col:
    st.toggle("Dark theme", key="dark")

apply_style(st.session_state.dark)


# ---------- the chosen page ----------

page.run()


# ---------- footer: which model is running ----------

info = get_model_info()
if info:
    last = info["last_race"]
    trained = pd.to_datetime(info["trained_at"]).strftime("%d %b %Y")
    st.write("")
    st.caption(f"Model trained on {trained}, using every race up to the "
               f"{last['race_name']} {last['season']} (round {last['round']}).")