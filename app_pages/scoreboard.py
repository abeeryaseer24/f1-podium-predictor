"""Scoreboard page: locked 2026 predictions and the 2025 backtest."""
import pandas as pd
import streamlit as st

from app_data import get_scoreboard
from predictor import clean_name, season_summary
from style import empty_note, race_card, show_cards, stat_tiles


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