"""Scoreboard: every live prediction, locked in before the race and scored after it.
Everything about how the model is built and tested lives on the About page."""
import json

import pandas as pd
import streamlit as st

from app_data import get_full_order, get_scoreboard, get_upcoming
from predictor import clean_name, current_season, season_summary
from style import empty_note, order_table, race_card, show_cards, stat_tiles, why_cards


def card(r):
    """One race card: our podium (✓/✗ once the result is in) and the real podium."""
    done = r["status"] == "done"
    locked = pd.to_datetime(r["predicted_at"]).strftime("%d %b, %H:%M UTC")
    meta = f"Locked in {locked}"
    if done:
        meta += " · Real podium: " + ", ".join(clean_name(d) for d in r["actual"])
    chips = []
    for i in (1, 2, 3):
        driver = r[f"p{i}"]
        chips.append({"name": clean_name(driver), "team": r[f"p{i}_team"],
                      "mark": ("hit" if driver in r["actual"] else "miss") if done else None,
                      "extra": None if done else f'{r[f"p{i}_chance"]:.0f}%'})
    return race_card(f'Round {int(r["round"])} · {r["race_name"]}', meta, chips,
                     int(r["model_hits"]) if done else None, int(r["grid_hits"]) if done else None)


st.write("Predictions are locked in after qualifying, before every race.")

live = get_scoreboard("live")
if live.empty:
    upcoming = get_upcoming(current_season())
    race = upcoming.iloc[0]["race_name"].replace(" Grand Prix", "") if not upcoming.empty else "the next"
    empty_note(f"The first prediction is locked in after {race} qualifying.")
else:
    stat_tiles(season_summary(live))
    for _, r in live.sort_values(["season", "round"], ascending=False).iterrows():
        show_cards([card(r)])
        if isinstance(r.get("why"), str):
            with st.expander("Why this pick?"):
                podium = pd.DataFrame([{"driver": r[f"p{i}"], "name": clean_name(r[f"p{i}"]),
                                        "constructor": r[f"p{i}_team"]} for i in (1, 2, 3)])
                why_cards(podium, json.loads(r["why"]))
        if isinstance(r.get("order"), str):
            with st.expander("Full order"):
                rows, summary = get_full_order(int(r["season"]), int(r["round"]), r["order"])
                order_table(rows, summary)

st.markdown('<p class="pp-link">How the model works and how it is tested fairly:</p>', unsafe_allow_html=True)
st.page_link("app_pages/about.py", label="Read more on the About page →")
