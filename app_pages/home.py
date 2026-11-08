"""Home: this race weekend at a glance. The next race with a live countdown and the five start lights,
our model's podium, a way into Beat the AI, and the rest of the app."""
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

import picks
from datetime import timedelta
from zoneinfo import ZoneInfo

from app_data import get_calendar, get_scoreboard, run_upcoming
from predictor import RESULTS_CSV, clean_name, current_season
from race_card import race_hero
from log_prediction import LOCK_HOURS
from style import podium, teaser_podium


def local_time(when):
    try:
        zone = ZoneInfo(st.context.timezone or "UTC")
    except Exception:
        zone = timezone.utc
    return when.astimezone(zone).strftime("%a %d %b, %H:%M")

season = current_season()
now = datetime.now(timezone.utc)
results = pd.read_csv(RESULTS_CSV, usecols=["season", "round"])
finished = set(zip(results["season"], results["round"]))
try:
    calendar = get_calendar(season)
except Exception:
    calendar = []
race = next((r for r in calendar if (season, r["round"]) not in finished), None)

live = get_scoreboard("live")
locked = None
if race is not None and not live.empty:
    rows = live[(live["season"] == season) & (live["round"] == race["round"])]
    locked = rows.iloc[0] if not rows.empty else None


# ---------- 1 + 2. the next race: countdown, five lights, weekend schedule ----------
if race is None:
    st.markdown(f'<div class="pp-band"><b>That\'s the {season} season done.</b>'
                '<span>See you next season. Meanwhile, rewind the season race by race.</span></div>',
                unsafe_allow_html=True)
    st.page_link("app_pages/season_rewind.py", label="Season Rewind →")
else:
    race_hero(race, locked is not None, dark=st.session_state.get("dark", True))
    after_quali = race["quali_start"] is not None and now >= race["quali_start"]

    # ---------- 3. our model's podium ----------
    st.subheader("Our model's podium")
    if locked is not None:
        when = pd.to_datetime(locked["predicted_at"]).strftime("%a %d %b, %H:%M UTC")
        podium([{"name": clean_name(locked[f"p{i}"]), "team": locked[f"p{i}_team"],
                 "note": f'{locked[f"p{i}_chance"]:.0f}% podium'} for i in (1, 2, 3)])
        st.caption(f"Locked in on race day, {when}, with the real qualifying results and grid penalties. "
                   "It won't change.")
    else:
        lock_at = race["race_start"] - timedelta(hours=LOCK_HOURS)
        provisional = None
        if after_quali:
            try:
                provisional = run_upcoming(season, race["round"])
            except Exception:
                provisional = None
        if provisional is not None and provisional["real_quali"]:
            podium([{"name": r["name"], "team": r["constructor"], "note": f'{r["podium_chance"]:.0f}% podium'}
                    for _, r in provisional["table"].head(3).iterrows()])
            pens = " and grid penalties" if provisional.get("grid_source") in ("official", "penalties file") else ""
            if now >= lock_at:
                st.caption(f"Locking in now: lock time was {local_time(lock_at)} your time. Our robot checks "
                           "every 10 minutes on race weekends, so the locked pick appears here shortly.")
            else:
                st.caption(f"Provisional: from the real qualifying{pens}. It locks in on race day, "
                           f"{local_time(lock_at)} your time, and won't change after that.")
        else:
            teaser_podium(f"Our model's pick comes after qualifying, and locks in on race day "
                          f"({local_time(lock_at)} your time).")

    def open_prediction():
        st.session_state.screen = "predict"
        st.session_state.choice = ("upcoming", season, race["round"])

    label = "View full predictions →" if locked is not None or after_quali else "See the model's early guess →"
    if st.button(label, on_click=open_prediction):
        st.switch_page("app_pages/podium_predictor.py")

    # ---------- 4. Beat the AI ----------
    head = "It's Hammertime." if after_quali else "You're early, but you can still predict."
    mine = None
    code = picks.clean_code(st.session_state.get("player") or st.context.cookies.get("pp_player"))
    if code:
        try:
            mine = next((p for p in picks.get_picks(code)
                         if p["season"] == season and p["round"] == race["round"]), None)
        except Exception:
            mine = None
    line = ("Your pick: " + " · ".join(clean_name(d) for d in mine["podium"]) + " ✓") if mine \
        else "Can you beat our model? Pick the podium before lights out."
    st.markdown(f'<div class="pp-band{" hot" if after_quali else ""}"><b>{head}</b><span>{line}</span></div>',
                unsafe_allow_html=True)
    st.page_link("app_pages/beat_the_ai.py", label="Change my pick →" if mine else "Make your pick →")


# ---------- 5. explore ----------
st.subheader("Explore")
TILES = [
    ("app_pages/pit_wall.py", ":material/sports_motorsports:", "Pit Wall", "Any race replayed in 3D, with our strategist's radio."),
    ("app_pages/race_engineer.py", ":material/headset_mic:", "Be the Race Engineer", "Make the pit calls. Beat the real team."),
    ("app_pages/season_rewind.py", ":material/history:", "Season Rewind", "A whole season, race by race."),
    ("app_pages/tyre_lab.py", ":material/tire_repair:", "Tyre Lab", "How fast each tyre wears, from real laps."),
]
for pair in (TILES[:2], TILES[2:]):
    for col, (path, icon, title, text) in zip(st.columns(2), pair):
        with col.container(border=True):
            st.page_link(path, label=f"**{title}**", icon=icon)
            st.caption(text)

st.page_link("app_pages/about.py", label="How it works → About")
