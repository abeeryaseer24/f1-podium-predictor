"""Beat the AI: visitors pick the podium (and, if they like, the whole order) before the race.
After the race they see their pick, our model's locked pick and the real result, and who won.
Scores are worked out behind the scenes; visitors only see who won."""
import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

import picks
from app_data import get_calendar, get_scoreboard, run_upcoming
from predictor import RESULTS_CSV, TEAM_MAP, clean_name, current_season
from share_card import card_data, share_card
from style import team_info, vs_boxes

COOKIE = "pp_player"
MESSAGES = {"win": "Congratulations, you beat our model!",
            "lose": "Our model is just better this time.",
            "tie": "Dead level with our model."}


# ---------- who is this visitor? (a random code kept in their browser) ----------

def player():
    if "player" not in st.session_state:
        st.session_state.player = picks.clean_code(st.context.cookies.get(COOKIE)) or picks.new_player_code()
    return st.session_state.player


def remember(code):
    """Keep the code in this browser for 2 years (a cookie only this app can read)."""
    if picks.clean_code(st.context.cookies.get(COOKIE)) != code:
        components.html(f"<script>document.cookie = '{COOKIE}={code}; path=/; max-age=63072000; SameSite=Lax';</script>",
                        height=0)


def local_time(when):
    try:
        zone = ZoneInfo(st.context.timezone or "UTC")
    except Exception:
        zone = timezone.utc
    return when.astimezone(zone).strftime("%a %d %b, %H:%M")


# ---------- the data we need ----------

season = current_season()
now = datetime.now(timezone.utc)
results = pd.read_csv(RESULTS_CSV)
results["constructor"] = results["constructor"].replace(TEAM_MAP)
finished = set(zip(results["season"], results["round"]))
last_team = results.sort_values(["season", "round"]).groupby("driver")["constructor"].last()
try:
    calendar = get_calendar(season)
except Exception:
    st.error("Couldn't load the race calendar right now. Please try again in a minute.")
    st.stop()

waiting = [r for r in calendar if (season, r["round"]) not in finished and r["race_start"] <= now]
open_race = next((r for r in calendar if (season, r["round"]) not in finished and r["race_start"] > now), None)
me = player()
try:
    my_picks = {(p["season"], p["round"]): p for p in picks.get_picks(me)}
except Exception:
    my_picks = {}
    st.warning("Couldn't reach the picks database right now, so your saved picks aren't shown.")


# ---------- 1. the next race: make your pick ----------

for r in waiting:
    st.info(f"Picks for the {r['race_name']} are closed. The result comes in a few hours after the race.")

if open_race is None:
    st.info(f"No races left to pick in {season}. See you next season!")
else:
    rnd = open_race["round"]
    st.subheader(f"Round {rnd} · {open_race['race_name']}")
    with st.spinner("Getting the drivers..."):
        try:
            race = run_upcoming(season, rnd)
        except Exception as error:
            st.error(f"Couldn't get this race ready: {error}")
            st.stop()

    close = f"Picks close at lights out: {local_time(open_race['race_start'])} your time."
    if race["real_quali"]:
        st.markdown(f'<div class="pp-banner hammer"><b>It\'s Hammertime.</b><span>Qualifying is done. '
                    f'Can you beat our model? {close}</span></div>', unsafe_allow_html=True)
    else:
        quali = f" Qualifying is {local_time(open_race['quali_start'])} your time." if open_race["quali_start"] else ""
        st.markdown(f'<div class="pp-banner"><b>You\'re early, but you can still predict.</b>'
                    f'<span>{quali.strip()} {close}</span></div>', unsafe_allow_html=True)

    drivers = race["table"].sort_values(["constructor", "name"])
    names = dict(zip(drivers["driver"], drivers["name"]))
    teams = dict(zip(drivers["driver"], drivers["constructor"]))
    label = lambda d: f"{names[d]} · {team_info(teams[d])[0]}"
    saved = my_picks.get((season, rnd))
    old = saved["podium"] if saved else [None, None, None]

    cols = st.columns(3)
    podium = [col.selectbox(f"P{i + 1}", list(names), format_func=label, placeholder="Choose a driver",
                            index=list(names).index(old[i]) if old[i] in names else None, key=f"bta_p{i}")
              for i, col in enumerate(cols)]
    with st.expander("Add the rest of the order (optional)"):
        st.caption("Pick drivers in the order you think they'll finish, from P4 down. It only counts if you "
                   "and our model get the same podium score.")
        rest_old = [d for d in (saved or {}).get("full_order") or [] if d in names and d not in podium][:19]
        rest = st.multiselect("P4 onwards", [d for d in names if d not in podium], default=rest_old,
                              format_func=label, key="bta_rest")
    nickname = st.text_input("Nickname for your card (optional)", value=(saved or {}).get("nickname") or "",
                             max_chars=20)

    if st.button("Lock in my pick", type="primary"):
        if None in podium or len(set(podium)) < 3:
            st.error("Pick three different drivers for P1, P2 and P3.")
        elif datetime.now(timezone.utc) >= open_race["race_start"]:
            st.error("Too late: the race has started, so picks are closed.")
        else:
            try:
                picks.save_pick(me, season, rnd, podium, podium + rest if rest else None, nickname)
                saved = {"podium": podium, "nickname": nickname}
                st.success("Locked in! You can change it until lights out. Come back after the race to see if "
                           "you beat our model.")
            except Exception:
                st.error("Couldn't save your pick right now. Please try again in a minute.")

    if saved:
        st.write("**Your pick card.** Download it and share it anywhere.")
        share_card(card_data("pick", f"{open_race['race_name']} {season}", saved.get("nickname") or "",
                             you=[(names.get(d, clean_name(d)), teams.get(d, "")) for d in saved["podium"]]))


# ---------- 2. your results: you vs our model vs the real podium ----------

live = get_scoreboard("live")
done = sorted((k for k in my_picks if k in finished), reverse=True)
if done:
    st.subheader("Your results")
    outcomes = []
    for key in done:
        p = my_picks[key]
        race = results[(results["season"] == key[0]) & (results["round"] == key[1])].sort_values("finish_position")
        team = dict(zip(race["driver"], race["constructor"]))
        real = dict(zip(race["driver"], race["finish_position"].astype(int)))
        actual = race.head(3)["driver"].tolist()
        locked = live[(live["season"] == key[0]) & (live["round"] == key[1])] if not live.empty else live
        model = locked.iloc[0] if not locked.empty else None
        model_podium = [model[f"p{i}"] for i in (1, 2, 3)] if model is not None else None
        model_order = json.loads(model["order"]) if model is not None and isinstance(model.get("order"), str) else None

        st.markdown(f"**{race.iloc[0]['race_name']} {key[0]}**")
        row = lambda ds, mark: [(clean_name(d), team.get(d, last_team.get(d, "")), (d in actual) if mark else None)
                                for d in ds]
        boxes = [("You", row(p["podium"], True))]
        if model_podium:
            boxes.append(("Our model", row(model_podium, True)))
        boxes.append(("Actual result", row(actual, False)))
        vs_boxes(boxes)

        if model_podium:
            result = picks.verdict(p["podium"], p.get("full_order"), model_podium, model_order, actual, real)
            outcomes.append(result)
            st.markdown(f'<div class="pp-msg {result}">{MESSAGES[result]}</div>', unsafe_allow_html=True)
            with st.expander("Share this result"):
                share_card(card_data("result", f"{race.iloc[0]['race_name']} {key[0]}", p.get("nickname") or "",
                                     you=[(n, t) for n, t, _ in row(p["podium"], False)],
                                     model=[(n, t) for n, t, _ in row(model_podium, False)],
                                     actual=[(n, t) for n, t, _ in row(actual, False)], result=result))
        else:
            st.caption("Our model didn't lock in a pick for this race, so there's no winner here.")
    if outcomes:
        wins = outcomes.count("win")
        st.write(f"You've beaten our model in **{wins} of {len(outcomes)}** race{'s' if len(outcomes) != 1 else ''}.")


# ---------- 3. your player code (to get your picks back on another device) ----------

with st.expander("Your player code"):
    st.write(f"Your picks are saved with the code **{me}**, kept in this browser. No login, no email: only your "
             "picks and an optional nickname are saved. On another phone, or after clearing your browser, "
             "enter the code here to get your picks back.")
    typed = st.text_input("Enter a code", placeholder="ABCD-EF23", key="bta_code")
    if st.button("Use this code"):
        code = picks.clean_code(typed)
        if code:
            st.session_state.player = code
            st.rerun()
        else:
            st.error("That isn't a valid code. It looks like ABCD-EF23.")

remember(me)
if not picks.online():
    st.caption("Test mode: picks are saved on this computer only (data/picks_local.json).")
