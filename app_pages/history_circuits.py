"""Circuit Profiles: every track that has held a Grand Prix, as a card you can open.

Tapping a card opens that circuit's own page: who has won there, every race it has
held, and the lap itself in 3D where we have the data for it.
"""
import streamlit as st

import circuit_profile
from app_archive import get_circuit_index, get_circuit_winners, require_history
from cards import cards_css, rgba
from style import empty_note
from ui_kit import esc, kit_css, section, tap_card

PICKED = "circuit_open"
PER_ROW = 3

cards_css()
kit_css()
require_history()

CARD_CSS = """<style>
.cc{position:relative;overflow:hidden;border-radius:16px;padding:15px 16px 13px;
  min-height:168px;display:flex;flex-direction:column;justify-content:space-between;
  border:1px solid var(--pp-border);background:var(--pp-panel)}
.cc .wash{position:absolute;inset:0;z-index:0}
.cc .ghost{position:absolute;right:-6px;bottom:-14px;z-index:0;font-size:3.4rem;opacity:.10;
  line-height:1}
.cc .body{position:relative;z-index:1}
.cc .where{font-size:.72rem;font-weight:700;letter-spacing:1.4px;text-transform:uppercase;
  color:var(--pp-red)}
.cc h4{font-family:'Saira Condensed',sans-serif;font-weight:800;font-size:1.3rem;
  line-height:1.08;margin:.18rem 0 .3rem;text-transform:uppercase;color:var(--pp-text)}
.cc .sub{color:var(--pp-muted);font-size:.82rem;line-height:1.4}
.cc .nums{position:relative;z-index:1;display:flex;gap:14px;margin-top:11px}
.cc .nums div{display:flex;flex-direction:column}
.cc .nums b{font-family:'Saira Condensed',sans-serif;font-weight:800;font-size:1.25rem;
  line-height:1;color:var(--pp-text)}
.cc .nums small{color:var(--pp-muted);font-size:.64rem;text-transform:uppercase;
  letter-spacing:.5px}
.cc .bar{position:absolute;left:0;top:0;bottom:0;width:5px;z-index:1}
@media (max-width:640px){
  .cc{min-height:146px;padding:12px 12px 10px}
  .cc h4{font-size:1.08rem}.cc .nums b{font-size:1.05rem}
  .cc .nums{gap:10px}.cc .nums small{font-size:.56rem}
}
</style>"""
st.markdown(CARD_CSS, unsafe_allow_html=True)

index = get_circuit_index()
if index.empty:
    empty_note("No circuits found in the history files.")
    st.stop()

# ---------- a circuit is open: show its page instead of the grid ----------

if st.session_state.get(PICKED):
    if st.button("← Back to all circuits"):
        st.session_state[PICKED] = None
        st.rerun()
    circuit_profile.show(st.session_state[PICKED])
    st.stop()

# ---------- otherwise: the grid of cards ----------

newest = int(index["last_season"].max())
countries = ["Every country"] + sorted(c for c in index["country"].dropna().unique())
left, right = st.columns([2, 2])
with left:
    country = st.selectbox("Country", countries)
with right:
    which = st.selectbox("Show", ["On the calendar now", "Every circuit ever",
                                  "Gone from the calendar"])

shown = index if country == "Every country" else index[index["country"] == country]
if which == "On the calendar now":
    shown = shown[shown["last_season"] >= newest - 1]
elif which == "Gone from the calendar":
    shown = shown[shown["last_season"] < newest - 1]

section(f"{len(shown)} circuit{'s' if len(shown) != 1 else ''}",
        "Tap a card to open that circuit: every race it has held, who has won there "
        "most often, and the lap in 3D for the ones we have position data for.")

if shown.empty:
    empty_note("No circuits match that choice.")
    st.stop()

rows = list(shown.itertuples())
for start in range(0, len(rows), PER_ROW):
    columns = st.columns(PER_ROW)
    for column, row in zip(columns, rows[start:start + PER_ROW]):
        with column:
            by_driver, _ = get_circuit_winners(row.circuit)
            king = (f'{by_driver.iloc[0]["driver_name"]} · '
                    f'{int(by_driver.iloc[0]["wins"])} wins'
                    if not by_driver.empty else "No winner recorded")
            current = row.last_season >= newest - 1
            colour = "#e10600" if current else "#6b6b7a"
            span = (f'{int(row.first_season)}' if row.first_season == row.last_season
                    else f'{int(row.first_season)}–{int(row.last_season)}')
            wash = (f'background:linear-gradient(135deg,{rgba(colour, .20)},'
                    f'{rgba(colour, .02)} 64%)')
            card = (
                f'<div class="pp-card cc" style="border-color:{rgba(colour, .45)}">'
                f'<div class="wash" style="{wash}"></div>'
                f'<div class="ghost">🏁</div>'
                f'<div class="bar" style="background:{colour}"></div>'
                f'<div class="body">'
                f'<div class="where">{esc(row.country or "")}</div>'
                f'<h4>{esc(row.circuit_name)}</h4>'
                f'<div class="sub">{esc(row.locality or "")}<br>{esc(king)}</div></div>'
                f'<div class="nums">'
                f'<div><b>{int(row.races)}</b><small>Races</small></div>'
                f'<div><b>{span}</b><small>Seasons</small></div></div></div>')
            if tap_card(card, key=f"circuit-{row.circuit}",
                        label=f"Open {row.circuit_name}"):
                st.session_state[PICKED] = row.circuit
                st.rerun()
