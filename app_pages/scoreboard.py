"""Scoreboard page: locked 2026 predictions and the 2025 backtest."""
import pandas as pd
import streamlit as st

from app_data import get_model_history, get_model_info, get_scoreboard
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

st.subheader("Every season, tested fairly")
st.write("Each season below was predicted by a model trained only on the seasons before it. "
         "\"The grid\" means simply guessing that the race finishes in starting order, a tough "
         "baseline in Formula 1.")
info = get_model_info()
tests = (info or {}).get("backtests")
if not tests:
    empty_note("No backtests yet. Run src/train.py to create them.")
else:
    rows = [{"Season": int(s), "Races": t["races"],
             "Podium drivers per race (model)": t["podium_hits"],
             "Podium drivers per race (grid)": t["grid_podium_hits"],
             "Winner right (model)": f'{t["winner_right"]:.0%}',
             "Winner right (grid)": f'{t["grid_winner_right"]:.0%}',
             "Places off, whole order (model)": t["places_off"],
             "Places off, whole order (grid)": t["grid_places_off"]}
            for s, t in sorted(tests.items(), reverse=True)]
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.caption("Places off: how many places, on average, each driver finished away from where the "
               "model (or the grid) put them. Lower is better.")

st.subheader("How the live model is chosen")
st.write("A few different recipes for the model take the same fair test above. The live recipe "
         "(the champion) is retrained every time new results come in. A challenger only takes over "
         "if it is clearly better: at least 0.05 more podium drivers per race, and no worse on the "
         "whole order.")
if info and info.get("challengers"):
    champion = info.get("recipe")
    rows = [{"Recipe": r["label"] + ("  ← live" if name == champion else ""),
             "Podium drivers per race": r["podium_hits"], "Places off, whole order": r["places_off"],
             "Winner right": f'{r["winner_right"]:.0%}'}
            for name, r in sorted(info["challengers"].items(), key=lambda kv: -kv[1]["podium_hits"])]
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.caption(f"Latest decision: {info.get('decision', '')}")
history = get_model_history()
if history:
    with st.expander(f"Model history ({len(history)} decision{'s' if len(history) != 1 else ''})"):
        for h in reversed(history[-20:]):
            when = pd.to_datetime(h["date"]).strftime("%d %b %Y")
            mark = "🔄 New champion" if h["changed"] else "✓ Champion kept"
            st.markdown(f"**{when}** · {mark} · {h['races_known']} races known  \n{h['reason']}")
