"""Strategy Duel: two players run the same driver's strategy in the same real race, at the same time."""
import json

import altair as alt
import pandas as pd
import streamlit as st

import picks
import strategy_duel as D
from app_data import get_game, get_prepared_races
from charts import dress
from predictor import RACES_DIR
from style import stat_strip
from ui_kit import GOLD, GOOD, POOR, banner, board, section

COOKIE = "pp_player"
TYRE_COLOURS = {"SOFT": "#e4544a", "MEDIUM": "#f5c518", "HARD": "#e8e8ec"}


def player():
    if "player" not in st.session_state:
        st.session_state.player = picks.clean_code(st.context.cookies.get(COOKIE)) or picks.new_player_code()
    return st.session_state.player


def info(folder):
    return json.loads((RACES_DIR / folder / "info.json").read_text())


def load(room):
    try:
        return D.moves(room), None
    except Exception as error:
        return [], error


me = player()
room = st.session_state.get("duel_room")

# ---------- lobby ----------
if not room:
    start, join = st.tabs(["Start a duel", "Join with a code"])
    with start:
        races = get_prepared_races()
        if races.empty:
            st.info("No races prepared yet.")
            st.stop()
        c1, c2 = st.columns(2)
        season = c1.selectbox("Season", sorted(races["season"].unique().tolist(), reverse=True), key="sd_season")
        rs = races[races["season"] == season].sort_values("round")
        names = {r.folder: f"Round {r.round} · {r.race_name}" for r in rs.itertuples()}
        folder = c2.selectbox("Race", list(names), index=len(names) - 1, format_func=names.get, key="sd_race")
        pack = get_game(folder)
        if pack is None:
            st.info("This race had rain; the duel only runs dry races. Pick another.")
            st.stop()
        codes = {str(d["number"]): f"{d['code']} · {d['name'].title()}" for d in info(folder)["drivers"]}
        playable = [n for n in pack["drivers"] if n in codes]
        c3, c4 = st.columns(2)
        driver = c3.selectbox("The car you both engineer", playable, format_func=codes.get, key="sd_driver")
        rival = c4.radio("Against", ["A friend", "Our strategist"], horizontal=True, key="sd_rival")
        nick = st.text_input("Your name", max_chars=20, key="sd_nick", placeholder="Anonymous")
        if st.button("Open the room", type="primary", key="sd_open"):
            code = D.new_room()
            try:
                D.add(code, me, "create", {"folder": folder, "driver": driver, "bot": rival == "Our strategist"})
                if nick:
                    D.add(code, me, "name", {"nickname": nick[:20]})
                st.session_state.duel_room = code
                st.rerun()
            except Exception as error:
                st.warning(picks.describe_error(error, D.TABLE))
    with join:
        code = st.text_input("Room code", max_chars=4, key="sd_code").strip().upper()
        nick2 = st.text_input("Your name", max_chars=20, key="sd_nick2", placeholder="Anonymous")
        if st.button("Join", type="primary", key="sd_join") and code:
            mv, err = load(code)
            s = D.state(mv) if not err else None
            if err:
                st.warning(picks.describe_error(err, D.TABLE))
            elif s is None:
                st.warning("There's no room with that code.")
            elif s["guest"] and me not in (s["host"], s["guest"]):
                st.warning("That room already has two players.")
            else:
                if me != s["host"] and not s["guest"]:
                    D.add(code, me, "join", {})
                if nick2:
                    D.add(code, me, "name", {"nickname": nick2[:20]})
                st.session_state.duel_room = code
                st.rerun()
    st.caption("Both of you engineer the same car in the same real race. Every five laps you each lock a call; when "
               "both are in, the race moves on and you see who's ahead. Play on two devices, or against our strategist.")
    st.stop()

# ---------- in a room ----------
mv, err = load(room)
if err:
    st.warning(picks.describe_error(err, D.TABLE))
    st.stop()
s = D.state(mv)
if s is None:
    st.warning("That room has gone.")
    del st.session_state["duel_room"]
    st.stop()
pack = get_game(s["folder"])
race = info(s["folder"])
driver = s["driver"]
car = next(d for d in race["drivers"] if str(d["number"]) == driver)
points = D.steps(pack, driver)
n_laps = pack["drivers"][driver]["laps"]
rival_id = s["guest"] if me == s["host"] else s["host"]
names = {me: s["names"].get(me) or "You", D.BOT: "Our strategist"}
names[rival_id] = s["names"].get(rival_id) or ("Our strategist" if rival_id == D.BOT else "Your rival")

top = st.columns([4, 1])
top[0].markdown(f"**Room {room}** · {race['race_name']} {race['season']} · {car['code']} {car['name'].title()}")
if top[1].button("Leave", key="sd_leave", use_container_width=True):
    del st.session_state["duel_room"]
    st.rerun()


@st.fragment(run_every=3)
def wait_for(count, text):
    """Poll the room until something new happens, then redraw the page."""
    st.info(text)
    new, _ = load(room)
    if len(new) != count:
        st.rerun(scope="app")


if me not in (s["host"], s["guest"]):
    st.warning("You're not a player in this room.")
    st.stop()
if s["guest"] is None:
    wait_for(len(mv), f"Waiting for your rival. Send them the room code: **{room}** (Strategy Duel → Join with a code).")
    st.stop()

mine = s["calls"][me]
theirs = D.bot_calls(pack, driver) if rival_id == D.BOT else s["calls"][rival_id]
done = min(len(mine), len(theirs))                    # steps both have locked
my_plan_known = D.plan_of({k: v for k, v in mine.items() if k < done})
their_plan_known = D.plan_of({k: v for k, v in theirs.items() if k < done})
lap_now = points[done] if done < len(points) else n_laps + 1

# where the race stands (both locked up to here)
upto = min(lap_now - 1, n_laps)
t_me = D.time_to(pack, driver, my_plan_known, upto) if upto > 0 else 0.0
t_them = D.time_to(pack, driver, their_plan_known, upto) if upto > 0 else 0.0
my_tyre, my_age = D.tyre_now(pack, driver, my_plan_known, min(lap_now, n_laps))
their_tyre, their_age = D.tyre_now(pack, driver, their_plan_known, min(lap_now, n_laps))
gap = t_me - t_them
stat_strip([
    ("Lap", f"{min(lap_now, n_laps)} / {n_laps}", "after the last locked stretch", True),
    ("Gap to " + names[rival_id], f"{gap:+.1f} s" if upto > 0 else "—", "ahead" if gap < 0 else ("behind" if gap > 0 else "level"), False),
    ("Your tyres", f"{my_tyre.title()}", f"{my_age:.0f} laps old", False),
    (names[rival_id] + "'s tyres", f"{their_tyre.title()}", f"{their_age:.0f} laps old", False),
])

# ---------- the call ----------
if done < len(points):
    lap = points[done]
    last = min(lap + D.STEP - 1, n_laps - 1)
    neutral = pack["drivers"][driver]["neutral"]
    recent = [k + 1 for k in range(max(0, lap - D.STEP - 1), lap - 1) if neutral[k]]
    if recent:
        banner("🟨", "Safety car in the last stretch", f"Laps {', '.join(map(str, recent))} were neutralised: a stop "
               "there cost about half as much.", GOLD)
    if len(mine) > done:
        wait_for(len(mv), f"Your call for laps {lap}–{last} is locked. Waiting for {names[rival_id]}…")
    else:
        section(f"Your call for laps {lap}–{last}", "Stay out, or box at the end of one of these laps. You can't change it after.")
        c1, c2, c3 = st.columns([1, 1, 1])
        box = c1.radio("Call", ["Stay out", "Box"], horizontal=True, key=f"sd_call_{done}")
        box_lap = c2.slider("Box at the end of lap", lap, last, lap, key=f"sd_lap_{done}", disabled=box == "Stay out")
        tyre = c3.selectbox("New tyres", ["SOFT", "MEDIUM", "HARD"], format_func=str.title, key=f"sd_tyre_{done}",
                            disabled=box == "Stay out")
        if st.button("Lock it in", type="primary", key=f"sd_lock_{done}"):
            D.add(room, me, "call", {"step": done, "box": box_lap if box == "Box" else None,
                                     "tyre": tyre if box == "Box" else None})
            st.rerun()
    st.caption("Tip: tyres wear faster the older they get, and a stop under a safety car costs much less time.")
    st.stop()

# ---------- the result ----------
my_plan, their_plan = D.plan_of(mine), D.plan_of(theirs)
d = pack["drivers"][driver]
results = {me: (D.time_to(pack, driver, my_plan, n_laps), D.legal(pack, driver, my_plan)),
           rival_id: (D.time_to(pack, driver, their_plan, n_laps), D.legal(pack, driver, their_plan))}
real = D.time_to(pack, driver, d["real"], n_laps)
strat = D.time_to(pack, driver, d["strategist"], n_laps)
ok_me, ok_them = results[me][1], results[rival_id][1]
if ok_me and (not ok_them or results[me][0] < results[rival_id][0]):
    banner("🏆", "You win the duel", f"By {abs(results[me][0] - results[rival_id][0]):.1f} s" if ok_them else
           f"{names[rival_id]} never changed compound and is disqualified.", GOOD)
elif ok_them and (not ok_me or results[me][0] > results[rival_id][0]):
    banner("🏁", f"{names[rival_id]} wins", f"By {abs(results[me][0] - results[rival_id][0]):.1f} s" if ok_me else
           "You never changed compound: disqualified (two dry compounds are compulsory).", POOR)
else:
    banner("🤝", "Dead heat", "Same time to the tenth.", GOLD)

section("Final times", "The same car, the same race: only the strategy differs.")
rows = []
for who, (tt, ok), plan in [(me, results[me], my_plan), (rival_id, results[rival_id], their_plan)]:
    rows.append({"colour": "#e10600" if who == me else "#27f4d2",
                 "cells": [(names[who], "you" if who == me else "rival"), f"{tt - real:+.1f} s" if ok else "DSQ",
                           " → ".join([d["startTyre"].title()] + [f"L{p['lap']} {p['tyre'].title()}" for p in plan])]})
rows.append({"colour": GOLD, "cells": [("The real team", car["code"]), "±0.0 s",
                                       " → ".join([d["startTyre"].title()] + [f"L{p['lap']} {p['tyre'].title()}" for p in d["real"]])]})
if rival_id != D.BOT:
    rows.append({"colour": "#8a8a96", "cells": [("Our strategist", "in real time"), f"{strat - real:+.1f} s",
                                                " → ".join([d["startTyre"].title()] + [f"L{p['lap']} {p['tyre'].title()}" for p in d["strategist"]])]})
board([("Engineer", "label"), ("Against the real team", "num"), ("Strategy", "text")], rows)

laps = list(range(1, n_laps + 1))
gaps = pd.DataFrame({"Lap": laps, "Gap": [D.time_to(pack, driver, my_plan, k) - D.time_to(pack, driver, their_plan, k) for k in laps]})
section("The gap, lap by lap", f"Below zero: you were ahead of {names[rival_id]}.")
chart = alt.Chart(gaps).mark_area(line={"color": "#e10600"}, color="#e10600", opacity=.25).encode(
    x=alt.X("Lap:Q", scale=alt.Scale(nice=False)), y=alt.Y("Gap:Q", title="Seconds behind (+) or ahead (−)"))
st.altair_chart(dress(chart).properties(height=240), use_container_width=True)
if st.button("Play again", type="primary", key="sd_again"):
    del st.session_state["duel_room"]
    st.rerun()
