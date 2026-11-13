"""About: everything behind the app in one place, sorted into tabs.
The project, the prediction model, how it is tested fairly, the strategist and the game,
and the robot that runs it all."""
import altair as alt
import pandas as pd
import streamlit as st

from app_data import (get_model_history, get_model_info, get_model_weights, get_past_races,
                      get_prepared_races, get_scoreboard)
from predictor import clean_name, season_summary
from ranker import LABELS
from style import empty_note, race_card, show_cards, stat_tiles
from ui_kit import kit_css, sheet

GITHUB = "https://github.com/abeeryaseer24/f1-podium-predictor"
LINKEDIN = ""          # paste your LinkedIn profile link here to show it on the page

kit_css()
info = get_model_info() or {}
dark = st.session_state.get("dark", True)
TEXT, GRID = ("#f5f5f7", "#2c2c3a") if dark else ("#15151e", "#d9d9d4")


def table(rows):
    """A small spec table. Keys become the headings, in the order of the first row."""
    if not rows:
        return
    headings = list(rows[0])
    numeric = {h for h in headings
               if all(isinstance(r.get(h), (int, float)) for r in rows)}
    sheet([(h, "num" if h in numeric else "text") for h in headings],
          [[r.get(h, "") for h in headings] for r in rows])


tabs = st.tabs(["The project", "The prediction model", "Accuracy and fairness",
                "Strategist and game", "The live system"])


# ---------- 1. the project ----------
with tabs[0]:
    races = get_past_races()
    prepared = get_prepared_races()
    st.subheader("What it does")
    st.write(f"Podium Predictor is a Formula 1 machine learning project that runs itself. It predicts "
             f"the whole finishing order of every race, locks the prediction in after qualifying, scores "
             f"it after the race and retrains on the new result. Around it sit 3D race replays, a pit "
             f"strategist, four games, a full set of team and driver pages and an archive "
             f"going back to 1950. The model has learned from {len(races)} races since "
             f"{int(races['season'].min())}, and {len(prepared)} races can be replayed in 3D.")

    st.subheader("A tour of the pages")
    table([
        {"Page": "Podium Predictor", "What it shows": "Pick any race: the model's podium, the whole predicted order and the real result."},
        {"Page": "Scoreboard", "What it shows": "Every live prediction, locked in before the race and scored after it."},
        {"Page": "Season Rewind", "What it shows": "A whole season race by race: how our model did against the grid."},
        {"Page": "Championship Odds", "What it shows": "The rest of the season replayed thousands of times, to see who still wins the title."},
        {"Page": "Constructor Standings", "What it shows": "The teams' championship for any season, with the charts behind every point."},
        {"Page": "Team Cards", "What it shows": "Every team as a card. Tap one for its own page in the team's colours: who runs it, what it has won and where it is based."},
        {"Page": "Team Performance", "What it shows": "How fast each car really was, measured from the race lap times rather than the results."},
        {"Page": "Reliability", "What it shows": "How often each team's cars reached the finish, and what stopped the rest."},
        {"Page": "Pit and Strategy", "What it shows": "Pit stop times by team, and the tyre strategy of any race since 2023."},
        {"Page": "Power Units", "What it shows": "Engine parts used and how close each driver is to a grid penalty. Kept by hand."},
        {"Page": "Upgrades", "What it shows": "Where the lap times show a car stepped forward, next to notes on what each team brought."},
        {"Page": "Driver Standings", "What it shows": "The drivers' championship, race by race."},
        {"Page": "Driver Cards", "What it shows": "Every driver as a card. Tap one for their career, teammates and race craft."},
        {"Page": "Driver Ratings", "What it shows": "Each driver's form through the season, on raw pace and against their own teammate."},
        {"Page": "Teammate Battles", "What it shows": "Same car, same weekend: who is winning inside each garage."},
        {"Page": "History: Champions", "What it shows": "Every drivers' and constructors' title since 1950."},
        {"Page": "History: Eras", "What it shows": "Which teams owned which decade, and how the sport itself has changed."},
        {"Page": "History: Records", "What it shows": "All-time leaderboards for wins, poles, podiums, points and starts."},
        {"Page": "History: Great Seasons", "What it shows": "The closest title fights and the championships that went to the final race."},
        {"Page": "History: Driver and Circuit Profiles", "What it shows": "Any driver who has started a Grand Prix, and every track that has held one."},
        {"Page": "History: On This Day and Head to Head", "What it shows": "What happened on today's date, and any two drivers from any era side by side."},
        {"Page": "Pit Wall", "What it shows": "Any race since 2023 replayed on the real 3D track, with our strategist's team radio."},
        {"Page": "Race Insights", "What it shows": "The weather, the flags and the lap-by-lap position swapping behind any race since 2023."},
        {"Page": "Penalties Log", "What it shows": "Every stewards' decision of a season, pulled out of the race control messages."},
        {"Page": "Ghost Lap Duel", "What it shows": "Two drivers' fastest laps raced against each other, corner by corner, with the speed, throttle, brake and gear traces."},
        {"Page": "Circuit Explorer", "What it shows": "Every circuit in its real shape and elevation."},
        {"Page": "Tyre Lab", "What it shows": "How fast each tyre compound wears, measured from real laps."},
        {"Page": "Beat the AI", "What it shows": "Pick the podium before the race, share your card, and see after the race if you beat our model."},
        {"Page": "Be the Race Engineer", "What it shows": "Make the pit calls for a real driver and try to beat their team."},
        {"Page": "Beat the AI: Constructors", "What it shows": "Pick the three teams that will score the most points at the next race, then see your pick against our model's."},
        {"Page": "F1 Quiz", "What it shows": "Ten questions written from the archive itself, with a score and a share card. No two quizzes are the same."},
    ])

    st.subheader("Built with")
    table([
        {"Part": "Language and data", "Tools": "Python, pandas, NumPy"},
        {"Part": "Machine learning", "Tools": "Plackett-Luce ranking model (SciPy optimiser), scikit-learn for the old model and scores"},
        {"Part": "Web app", "Tools": "Streamlit, Altair charts"},
        {"Part": "3D replays and games", "Tools": "Three.js, running inside the page"},
        {"Part": "Beat the AI picks", "Tools": "Supabase database, reached only from the app's server"},
        {"Part": "Automation", "Tools": "GitHub Actions robot every 3 hours, with safety checks"},
    ])

    st.subheader("Where the data comes from")
    table([
        {"Source": "Jolpica-F1 (the Ergast successor)", "Used for": "Results, grids and qualifying since 2016, and the race calendar"},
        {"Source": "OpenF1", "Used for": "Laps, tyres, pit stops, race control and car positions, 2023 onwards"},
        {"Source": "MultiViewer circuit data", "Used for": "Official corner numbers for the tracks"},
    ])

    links = f"[Code on GitHub]({GITHUB})"
    if LINKEDIN:
        links += f" · [Me on LinkedIn]({LINKEDIN})"
    st.markdown(links)


# ---------- 2. the prediction model ----------
with tabs[1]:
    st.subheader("In plain words")
    st.write("Every driver gets a strength score, built from what is known before the race: grid, "
             "qualifying, car pace, form and records. The finishing order is then predicted the way "
             "races work: who comes out on top, then who is best of the rest, and so on down to last "
             "place. This is called a Plackett-Luce ranking model.")
    st.write("To turn strengths into chances, the model replays the race 5,000 times with a measured "
             "amount of luck. That is where the win and podium percentages come from: win chances add "
             "up to 100% and podium chances to exactly 3 drivers.")
    st.write("Every input is compared with the rest of the same race, so the model learns who is better "
             "than whom, not raw numbers. It learns from the first 10 finishers of each race, because the "
             "back of the field is mostly luck.")

    st.subheader("What the model looks at")
    try:
        weights = get_model_weights()
    except Exception:
        weights = pd.DataFrame()
    if weights.empty:
        empty_note("The model file isn't there yet. Run src/train.py to create it.")
    else:
        weights["Input"] = weights["feature"].map(LABELS).fillna(weights["feature"])
        weights["How much it matters"] = weights["weight"].abs().round(3)
        weights = weights.sort_values("How much it matters", ascending=False)
        chart = (alt.Chart(weights).mark_bar(color="#e10600", cornerRadiusEnd=4)
                 .encode(x=alt.X("How much it matters:Q"),
                         y=alt.Y("Input:N", sort=None, title=None, axis=alt.Axis(labelLimit=320)),
                         tooltip=["Input", "How much it matters"])
                 .properties(height=28 * len(weights))
                 .configure(background="transparent")
                 .configure_axis(labelColor=TEXT, titleColor=TEXT, gridColor=GRID, domainColor=GRID))
        st.altair_chart(chart, width="stretch", theme=None)
        st.caption("Size of each input's weight in the live model. All inputs are on the same scale, so "
                   "longer bars move a driver's strength more.")

    st.subheader("Recipes compete to be the live model")
    st.write("A few versions of the model (recipes) take the same fair test, on every season since 2022. "
             "The live one, the champion, is retrained whenever new results come in. A challenger only takes "
             "over if it is clearly better: at least 0.05 more podium drivers per race, and no worse on the "
             "whole order.")
    if info.get("challengers"):
        champion = info.get("recipe")
        table([{"Recipe": r["label"] + ("  ← live" if name == champion else ""),
                "Podium drivers per race": r["podium_hits"], "Places off, whole order": r["places_off"],
                "Winner right": f'{r["winner_right"]:.0%}'}
               for name, r in sorted(info["challengers"].items(), key=lambda kv: -kv[1]["podium_hits"])])
        st.caption(f"Latest decision: {info.get('decision', '')}")
    history = get_model_history()
    if history:
        with st.expander(f"Model history ({len(history)} decision{'s' if len(history) != 1 else ''})"):
            for h in reversed(history[-20:]):
                when = pd.to_datetime(h["date"]).strftime("%d %b %Y")
                mark = "🔄 New champion" if h["changed"] else "✓ Champion kept"
                st.markdown(f"**{when}** · {mark} · {h['races_known']} races known  \n{h['reason']}")


# ---------- 3. accuracy and fairness ----------
with tabs[2]:
    st.subheader("Every season, tested fairly")
    st.write("Each season was predicted by a model trained only on the seasons before it, so it never saw "
             "those results. \"The grid\" means guessing that the race finishes in starting order, a tough "
             "baseline in Formula 1. \"Old model\" is the first version of this project (a Random Forest that "
             "only picked the podium).")
    tests = info.get("backtests")
    if not tests:
        empty_note("No backtests yet. Run src/train.py to create them.")
    else:
        table([{"Season": int(s), "Races": t["races"],
                "Podium drivers · model": t["podium_hits"],
                "Podium drivers · grid": t["grid_podium_hits"],
                "Podium drivers · old model": t.get("old_model_podium_hits", "—"),
                "Winner right · model": f'{t["winner_right"]:.0%}',
                "Winner right · grid": f'{t["grid_winner_right"]:.0%}',
                "Places off · model": t["places_off"],
                "Places off · grid": t["grid_places_off"]}
               for s, t in sorted(tests.items(), reverse=True)])
        st.caption("Podium drivers: how many of the 3 predicted drivers made the podium, per race. Places off: how many places, on average, each driver finished away from where the model "
                   "(or the grid) put them. Lower is better.")
        worse = [s for s, t in sorted(tests.items()) if t["podium_hits"] < t["grid_podium_hits"]]
        if worse:
            st.write(f"Honest note: in {', '.join(worse)} the grid picked more podium drivers than our model. "
                     "Qualifying already tells you most of what matters on Sunday, so beating the grid "
                     "every season is hard.")

    st.subheader("2025, race by race")
    st.write("Every 2025 race, predicted by a model trained only on 2016–2024.")
    back = get_scoreboard("backtest")
    if back.empty:
        empty_note("No 2025 backtest yet. Run src/train.py to create it.")
    else:
        stat_tiles(season_summary(back))
        with st.expander(f"Show all {len(back)} races"):
            cards = []
            for _, r in back.sort_values("round").iterrows():
                done = r["status"] == "done"
                chips = [{"name": clean_name(r[f"p{i}"]), "team": r[f"p{i}_team"],
                          "mark": ("hit" if r[f"p{i}"] in r["actual"] else "miss") if done else None,
                          "extra": None} for i in (1, 2, 3)]
                meta = "Real podium: " + ", ".join(clean_name(d) for d in r["actual"]) if done else ""
                cards.append(race_card(f'Round {int(r["round"])} · {r["race_name"]}', meta, chips,
                                       int(r["model_hits"]) if done else None,
                                       int(r["grid_hits"]) if done else None))
            show_cards(cards)

    st.subheader("Rules that keep it honest")
    st.markdown(
        "- **Locked before the race.** A live prediction is saved on race day, 8 hours before lights out, with "
        "the real qualifying results and the known grid penalties. The whole order 1–22 is saved, not just the podium.\n"
        "- **Never changed.** Every robot run checks that earlier predictions are exactly as they were.\n"
        "- **No peeking.** Every input is built only from races before the one being predicted.\n"
        "- **Fair comparison.** Every recipe, and the grid, is scored on the same races in the same way.\n"
        "- **Past races in the Predictor are not a test.** The live model has already seen those results, "
        "which is why the seasons above are tested with models that never saw them.")


# ---------- 4. strategist and game ----------
with tabs[3]:
    st.subheader("The pit strategist")
    st.write("On the Pit Wall, our strategist watches the race lap by lap and calls pit stops on team "
             "radio, like a race engineer. At the end of every lap it re-plans: when to stop and which tyre "
             "to fit, using a tyre model fitted on the race so far (fuel burning off, each compound's speed "
             "and wear, and the cliff when a tyre is finished). It reacts to safety cars, virtual safety cars "
             "and red flags.")
    st.markdown(
        "- **It only knows the past.** At lap 20 it has seen laps 1–20 and nothing else. The code refuses to "
        "run if it is handed a future lap, and every robot run checks this.\n"
        "- **It learns from earlier races.** A tyre book for each circuit (wear, pit stop time, usual first "
        "stop) and a pit-timing model are built only from races before the one being replayed.\n"
        "- **Its verdict** compares each driver's real stops with what it called: matched, close, too early "
        "or too late.")
    st.write("Honest note: the strategist is more eager to pit than real teams. It doesn't know about "
             "traffic, team orders or tyre sets saved from qualifying.")

    st.subheader("Be the Race Engineer")
    st.write("You make the pit calls for one real driver. Your car does the real driver's lap times with "
             "the tyre effect taken out, plus what your tyres cost and your pit stops. Everyone else races "
             "exactly as they did in reality, so it is a simulation, and the page says so.")
    st.markdown(
        "- **Calibrated.** Copying the real team's stops gives exactly the real finishing time, so you, the "
        "real team and our strategist go through the same maths.\n"
        "- **Dry races only, for now.** Rain changes everything about tyres, so wet races can't be played yet.")


# ---------- 5. the live system ----------
with tabs[4]:
    st.subheader("A robot runs it every 3 hours")
    st.write("Nobody presses a button. Every 3 hours a GitHub Actions robot runs the whole system:")
    st.markdown(
        "1. **After a race:** downloads the new results, checks them, rebuilds the inputs and retrains. "
        "The recipes compete again and the best one stays live.\n"
        "2. **New race files:** prepares replays for races that don't have one yet, and the strategist "
        "analyses them.\n"
        "3. **On race day:** locks in the race's prediction (the whole order), with grid penalties applied.\n"
        "4. **Safety checks**, then it saves everything to GitHub and the live app updates.")

    st.subheader("Safety checks")
    st.write("If any check fails, the run stops, nothing is saved, and I get an email.")
    st.markdown(
        "- No race results lost, missing or duplicated, and every race has exactly one P1, P2 and P3\n"
        "- The model's test score is healthy and the live model is the champion recipe\n"
        "- Locked predictions are exactly as they were\n"
        "- Every replay has all its files and enough car positions\n"
        "- The strategist refuses future laps, and a re-run from the past only gives the same plans")

    if info:
        last = info["last_race"]
        trained = pd.to_datetime(info["trained_at"]).strftime("%d %b %Y, %H:%M UTC")
        st.caption(f"Model last trained on {trained}, using every race up to the {last['race_name']} "
                   f"{last['season']} (round {last['round']}).")
    st.markdown(f"[See the robot's runs on GitHub]({GITHUB}/actions)")

    st.subheader("Maintaining the data")
    st.write("Two parts of the app are not automated. Power unit allocations and aerodynamic "
             "upgrade packages are published only in team press material and scrutineering "
             "documents, and no free data source carries either, so both are recorded by hand. "
             "The reference below is the specification for those files.")

    st.markdown("**`data/power_units.csv` — power unit components**")
    st.markdown(
        "Columns: `season, round, driver, constructor, component, note`.\n"
        "- One row per component fitted. The component each car begins the season with is "
        "counted automatically, so only subsequent changes are recorded.\n"
        "- `driver` takes the identifier used throughout the application, for example "
        "`max_verstappen`.\n"
        "- `component` must match the part name exactly as it appears in the allowance table "
        "on the Power Units page.\n"
        "- The page is withdrawn from the menu while this file is empty, and is restored "
        "automatically once it contains at least one row.")

    st.markdown("**`data/upgrades.csv` — upgrade packages**")
    st.markdown(
        "Columns: `season, round, constructor, area, description, source`.\n"
        "- One row per package introduced by a team.\n"
        "- `area` identifies the part of the car, for example floor, front wing or sidepods.\n"
        "- `source` records the technical report the entry was taken from.\n"
        "- The Upgrade notes section is omitted for any season with no rows. The measured "
        "pace steps shown above it are derived from lap data and are unaffected.")

    st.markdown("**Lap-derived pages**")
    st.write("Pit and Strategy, Tyre Lab, Pit Wall, Race Insights and the Penalties Log are all "
             "built from the prepared race folders in `data/races/`, which the robot assembles "
             "from OpenF1. Coverage begins in 2023 and a season appears only once its races have "
             "been prepared, so these pages open on the most recent season that has data rather "
             "than on the current one.")
