"""Season Rewind: a whole season, race by race, as our model would have called it.
Each season comes from a model trained only on the seasons before it (see About)."""
import html

import altair as alt
import pandas as pd
import streamlit as st

from app_data import get_backtests
from predictor import clean_name
from style import stat_strip

back = get_backtests()
if back.empty:
    st.info("No season tests yet. Run src/train.py to create them.")
    st.stop()

seasons = sorted(back["season"].unique().tolist(), reverse=True)
season = st.segmented_control("Season", seasons, default=seasons[0], format_func=str) or seasons[0]
races = back[back["season"] == season].sort_values("round").reset_index(drop=True)
n = len(races)

# ---------- the season in four numbers ----------
stat_strip([
    ("Our model", f'{races["podium_hits"].mean():.2f}', "podium drivers per race", True),
    ("The grid", f'{races["grid_podium_hits"].mean():.2f}', "podium drivers per race", False),
    ("Winners called", f'{int(races["winner_right"].sum())}/{n}',
     f'the grid: {int(races["grid_winner_right"].sum())}', False),
    ("Places off", f'{races["places_off"].mean():.1f}', f'whole order · the grid: {races["grid_places_off"].mean():.1f}', False),
])
diff = int(races["podium_hits"].sum() - races["grid_podium_hits"].sum())
st.markdown(f'<p class="pp-verdict">{"Our model beat the grid by " + str(diff) + " podium drivers" if diff > 0 else ("The grid beat our model by " + str(-diff) + " podium drivers" if diff < 0 else "Our model and the grid finished level")} over {n} races.</p>',
            unsafe_allow_html=True)

# ---------- race strip: one tile per race, coloured by how many podium drivers were right ----------
tiles = []
for r in races.itertuples():
    picks = ", ".join(clean_name(d) for d in (r.p1, r.p2, r.p3))
    tip = f"Round {r.round} · {r.race_name}: {r.podium_hits}/3 (grid {r.grid_podium_hits}/3). Picked {picks}"
    short = r.race_name.replace(" Grand Prix", "").replace("Grand Prix", "")
    tiles.append(f'<div class="pp-rt h{int(r.podium_hits)}" title="{html.escape(tip)}"><b>{int(r.podium_hits)}</b>'
                 f'<small>R{r.round}</small><span>{html.escape(short)}</span></div>')
st.markdown(f'<div class="pp-strip">{"".join(tiles)}</div>'
            '<p class="pp-legend"><i class="h3"></i>3 of 3 <i class="h2"></i>2 <i class="h1"></i>1 <i class="h0"></i>0 '
            'podium drivers right</p>', unsafe_allow_html=True)

# ---------- the race through the season: running total, model vs grid ----------
dark = st.session_state.get("dark", True)
TEXT, GRID = ("#f5f5f7", "#2c2c3a") if dark else ("#15151e", "#d9d9d4")
lines = pd.concat([
    pd.DataFrame({"Round": races["round"], "Podium drivers right (running total)": races["podium_hits"].cumsum(),
                  "Who": "Our model"}),
    pd.DataFrame({"Round": races["round"], "Podium drivers right (running total)": races["grid_podium_hits"].cumsum(),
                  "Who": "The grid"}),
])
colour = alt.Scale(domain=["Our model", "The grid"], range=["#e10600", "#8a8a96"])
chart = alt.Chart(lines).mark_line(strokeWidth=3, point=True).encode(
    x=alt.X("Round:Q", axis=alt.Axis(tickMinStep=1)),
    y="Podium drivers right (running total):Q",
    color=alt.Color("Who:N", scale=colour, legend=alt.Legend(orient="top", title=None)),
    tooltip=["Who", "Round", "Podium drivers right (running total)"])

chart = (chart.properties(height=320).configure(background="transparent")
         .configure_axis(labelColor=TEXT, titleColor=TEXT, gridColor=GRID, domainColor=GRID)
         .configure_legend(labelColor=TEXT))
st.altair_chart(chart, width="stretch", theme=None)

# ---------- best and toughest calls ----------
best = races.sort_values(["podium_hits", "winner_right", "places_off"], ascending=[False, False, True]).iloc[0]
worst = races.sort_values(["podium_hits", "places_off"], ascending=[True, False]).iloc[0]
left, right = st.columns(2)
left.markdown(f'<div class="pp-call good"><div class="k">Best call</div><b>{html.escape(best["race_name"])}</b>'
              f'<span>{int(best["podium_hits"])} of 3 podium drivers{", winner right" if best["winner_right"] else ""}, '
              f'whole order {best["places_off"]:.1f} places off</span></div>', unsafe_allow_html=True)
right.markdown(f'<div class="pp-call bad"><div class="k">Toughest race</div><b>{html.escape(worst["race_name"])}</b>'
               f'<span>{int(worst["podium_hits"])} of 3 podium drivers, whole order {worst["places_off"]:.1f} places off'
               f'</span></div>', unsafe_allow_html=True)

st.caption(f"Every {season} race was predicted by a model trained only on the seasons before {season}, "
           "so it never saw these results.")
st.page_link("app_pages/about.py", label="How the model is tested fairly →")
