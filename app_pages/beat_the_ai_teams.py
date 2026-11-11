"""Beat the AI: Constructors. Pick the three teams you think will score the most points
at the next race, before lights out. After the race, see your pick against our model's
and the real answer.

The driver game is on the Beat the AI page; this is the team version and keeps its own
picks, so you can play both.
"""
import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

import picks
from app_data import get_calendar, get_scoreboard, run_upcoming
from cards import cards_css, note
from predictor import RESULTS_CSV, TEAM_MAP, current_season
from style import empty_note, team_info, vs_boxes
from team_card import team_card
from team_game import PLACES, score, teams_from_order, teams_from_results, top_teams, verdict

COOKIE = "pp_player"
MESSAGES = {"win": "Congratulations, you beat our model!",
            "lose": "Our model is just better this time.",
            "tie": "Dead level with our model."}

cards_css()


# ---------- who is this visitor? (the same code as the driver game) ----------

def player():
    if "player" not in st.session_state:
        st.session_state.player = (picks.clean_code(st.context.cookies.get(COOKIE))
                                   or picks.new_player_code())
    return st.session_state.player


def remember(code):
    if picks.clean_code(st.context.cookies.get(COOKIE)) != code:
        components.html(
            f"<script>document.cookie = '{COOKIE}={code}; path=/; max-age=63072000; "
            "SameSite=Lax';</script>", height=0)


def local_time(when):
    try:
        zone = ZoneInfo(st.context.timezone or "UTC")
    except Exception:
        zone = timezone.utc
    return when.astimezone(zone).strftime("%a %d %b, %H:%M")


def team_label(team_id):
    return team_info(team_id)[0]


# ---------- the data we need ----------

season = current_season()
now = datetime.now(timezone.utc)
results = pd.read_csv(RESULTS_CSV)
results["constructor"] = results["constructor"].replace(TEAM_MAP)
finished = set(zip(results["season"], results["round"]))

try:
    calendar = get_calendar(season)
except Exception:
    st.error("Couldn't load the race calendar right now. Please try again in a minute.")
    st.stop()

waiting = [r for r in calendar if (season, r["round"]) not in finished and r["race_start"] <= now]
open_race = next((r for r in calendar
                  if (season, r["round"]) not in finished and r["race_start"] > now), None)
me = player()
try:
    my_picks = {(p["season"], p["round"]): p for p in picks.get_team_picks(me)}
except Exception:
    my_picks = {}
    st.warning("Couldn't reach the picks database right now, so your saved picks aren't "
               "shown. If this is the first time you have opened this page, the "
               "team_picks table may still need creating.")

st.markdown("**The game.** Which three teams will take the most points home from the "
            "next race? A team's haul is simply what both its cars score, so a quiet "
            "double-points finish can beat one car on the podium and one in the gravel.")

# ---------- 1. the next race: make your pick ----------

for r in waiting:
    st.info(f"Picks for the {r['race_name']} are closed. The result comes in a few hours "
            "after the race.")

if open_race is None:
    st.info(f"No races left to pick in {season}. See you next season!")
else:
    rnd = open_race["round"]
    st.subheader(f"Round {rnd} · {open_race['race_name']}")
    with st.spinner("Getting the teams..."):
        try:
            race = run_upcoming(season, rnd)
        except Exception as error:
            st.error(f"Couldn't get this race ready: {error}")
            st.stop()

    table = race["table"]
    teams = sorted(table["constructor"].unique(), key=team_label)
    close = f"Picks close at lights out: {local_time(open_race['race_start'])} your time."
    if race["real_quali"]:
        st.markdown(f'<div class="pp-banner hammer"><b>It\'s Hammertime.</b><span>'
                    f'Qualifying is done, so you can see the grid. {close}</span></div>',
                    unsafe_allow_html=True)
    else:
        quali = (f" Qualifying is {local_time(open_race['quali_start'])} your time."
                 if open_race["quali_start"] else "")
        st.markdown(f'<div class="pp-banner"><b>You\'re early, but you can still predict.'
                    f'</b><span>{quali.strip()} {close}</span></div>',
                    unsafe_allow_html=True)

    saved = my_picks.get((season, rnd))
    old = (saved or {}).get("teams") or [None] * PLACES

    columns = st.columns(PLACES)
    pick = [column.selectbox(
        f"{i + 1}{'st' if i == 0 else ('nd' if i == 1 else 'rd')} most points",
        teams, format_func=team_label, placeholder="Choose a team",
        index=teams.index(old[i]) if i < len(old) and old[i] in teams else None,
        key=f"bta_team_{i}") for i, column in enumerate(columns)]

    nickname = st.text_input("Nickname for your card (optional)",
                             value=(saved or {}).get("nickname") or "", max_chars=20)

    if st.button("Lock in my pick", type="primary"):
        if None in pick or len(set(pick)) < PLACES:
            st.error(f"Pick {PLACES} different teams.")
        elif datetime.now(timezone.utc) >= open_race["race_start"]:
            st.error("Too late: the race has started, so picks are closed.")
        else:
            try:
                picks.save_team_pick(me, season, rnd, pick, nickname)
                saved = {"teams": pick, "nickname": nickname}
                st.success("Locked in! You can change it until lights out.")
            except Exception:
                st.error("Couldn't save your pick right now. Please try again in a minute.")

    if saved and saved.get("teams"):
        st.write("**Your pick card.** Download it and share it anywhere.")
        team_card("pick", f"{open_race['race_name']} {season}",
                  saved.get("nickname") or "", you=saved["teams"])

    with st.expander("What our model expects (no peeking before you pick)"):
        order = table.sort_values("predicted_position")["driver"].tolist()
        team_of = dict(zip(table["driver"], table["constructor"]))
        expected = teams_from_order(order, team_of)
        st.dataframe(
            pd.DataFrame([{"Team": team_label(t), "Points if the model is right": p,
                           "Best car": f"P{b}"} for t, p, b in expected]),
            hide_index=True, width="stretch")
        note("This is only what the model's predicted finishing order adds up to. It is "
             "not locked in and it is not a result.")

# ---------- 2. your results ----------

live = get_scoreboard("live")
done = sorted((k for k in my_picks if k in finished), reverse=True)

if done:
    st.subheader("Your results")
    outcomes = []
    for key in done:
        saved = my_picks[key]
        mine = saved.get("teams") or []
        race = results[(results["season"] == key[0]) & (results["round"] == key[1])]
        if race.empty or not mine:
            continue

        real_rows = teams_from_results(race)
        actual = top_teams(real_rows)

        locked = (live[(live["season"] == key[0]) & (live["round"] == key[1])]
                  if not live.empty else live)
        model_teams = None
        if not locked.empty:
            row = locked.iloc[0]
            order = json.loads(row["order"]) if isinstance(row.get("order"), str) else None
            if order:
                team_of = dict(zip(race["driver"], race["constructor"]))
                model_teams = top_teams(teams_from_order(order, team_of))

        st.markdown(f"**{race.iloc[0]['race_name']} {key[0]}**")
        as_rows = lambda ids, mark: [(team_label(t), t, (t in actual) if mark else None)
                                     for t in ids]
        boxes = [("You", as_rows(mine, True))]
        if model_teams:
            boxes.append(("Our model", as_rows(model_teams, True)))
        boxes.append(("Actual result", as_rows(actual, False)))
        vs_boxes(boxes)

        points = {t: p for t, p, _ in real_rows}
        st.caption(" · ".join(f"{team_label(t)} {points.get(t, 0):g}" for t in actual)
                   + "  points scored")

        if model_teams:
            result = verdict(mine, model_teams, actual)
            outcomes.append(result)
            st.markdown(f'<div class="pp-msg {result}">{MESSAGES[result]}</div>',
                        unsafe_allow_html=True)
            with st.expander("Share this result"):
                team_card("result", f"{race.iloc[0]['race_name']} {key[0]}",
                          saved.get("nickname") or "", you=mine, model=model_teams,
                          actual=actual, result=result)
        else:
            st.caption("Our model didn't lock in a pick for this race, so there's no "
                       "winner here.")

    if outcomes:
        wins = outcomes.count("win")
        st.write(f"You've beaten our model in **{wins} of {len(outcomes)}** "
                 f"race{'s' if len(outcomes) != 1 else ''}.")
elif open_race is not None:
    note("Once the race has run, this is where your pick, our model's pick and the real "
         "answer line up side by side.")

# ---------- 3. how it is scored, and your player code ----------

with st.expander("How it is scored"):
    st.write("A team in the exact spot is worth 3 points, and a team in your three but "
             "in the wrong spot is worth 1. Our model's three come from its locked "
             "prediction for the race: its predicted finishing order turned into points, "
             "added up per team. The real answer uses the points actually awarded, so a "
             "disqualification counts the way it really did.")
    st.write("Your score is never shown, only whether you beat the model.")

with st.expander("Your player code"):
    st.write(f"Your picks are saved with the code **{me}**, the same code as the driver "
             "game, kept in this browser. No login and no email. On another phone, or "
             "after clearing your browser, enter the code here to get your picks back.")
    typed = st.text_input("Enter a code", placeholder="ABCD-EF23", key="bta_team_code")
    if st.button("Use this code"):
        code = picks.clean_code(typed)
        if code:
            st.session_state.player = code
            st.rerun()
        else:
            st.error("That isn't a valid code. It looks like ABCD-EF23.")

remember(me)
if not picks.online():
    st.caption("Test mode: picks are saved on this computer only "
               "(data/team_picks_local.json).")
