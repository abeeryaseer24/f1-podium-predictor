"""Entry point: the top menu, the header, the theme switch and the footer.
Every page lives in app_pages/. To add a page, add one st.Page line to PAGES
and one line to TAGLINES."""
import sys
from pathlib import Path

import streamlit as st

# Let every page find the files inside src/
SRC = (Path(__file__).parent / "src").resolve()
sys.path.append(str(SRC))


def forget_changed_modules():
    """Make every run use the files in src/ as they are on disk now.

    Streamlit Cloud keeps one Python process alive across deploys: it pulls the new
    code and reruns the pages, but anything already imported from src/ stays in memory
    as the old version. A page that needs something added to a shared file since then
    (a new table helper in ui_kit, say) fails with an ImportError while older pages
    keep working. Each module is stamped with its file's modified time; if the file
    has changed since, or the module predates the stamp, it is dropped so the next
    import reads it fresh.
    """
    for name, module in list(sys.modules.items()):
        path = getattr(module, "__file__", None)
        if not path or Path(path).resolve().parent != SRC:
            continue
        try:
            mtime = Path(path).stat().st_mtime
        except OSError:
            continue
        if getattr(module, "__src_mtime__", None) != mtime:
            del sys.modules[name]


def stamp_modules():
    """Record the file time of every src/ module imported during this run."""
    for module in list(sys.modules.values()):
        path = getattr(module, "__file__", None)
        if path and Path(path).resolve().parent == SRC and not hasattr(module, "__src_mtime__"):
            try:
                module.__src_mtime__ = Path(path).stat().st_mtime
            except OSError:
                pass


forget_changed_modules()
import ui_kit
from style import apply_style, hero

st.set_page_config(page_title="Podium Predictor", page_icon="🏁", layout="wide")


def has_rows(name):
    """True if one of the hand-kept csv files has anything in it beyond its headings.

    Power Units is built entirely from data/power_units.csv. While that file is empty
    the page can only report that every driver is on their first of every part, which
    is not information — it is the absence of it. Rather than show an empty page, the
    menu leaves it out until the file has something in it, and puts it back by itself
    on the next run once it does.
    """
    path = Path(__file__).parent / "data" / f"{name}.csv"
    try:
        with path.open(encoding="utf-8") as handle:
            next(handle, None)                      # the heading row
            return any(line.strip() for line in handle)
    except OSError:
        return False


# ---------- the top menu: new pages get added here as they're built ----------

PAGES = {
    "": [                                   # no group: shows as a plain "Home" link
        st.Page("app_pages/home.py", title="Home", default=True),
    ],
    "Predictor": [
        st.Page("app_pages/podium_predictor.py", title="Podium Predictor"),
        st.Page("app_pages/scoreboard.py", title="Scoreboard"),
        st.Page("app_pages/season_rewind.py", title="Season Rewind"),
        st.Page("app_pages/championship_odds.py", title="Championship Odds"),
        st.Page("app_pages/model_report_card.py", title="Model Report Card"),
    ],
    "Teams": [
        st.Page("app_pages/constructor_standings.py", title="Constructor Standings"),
        st.Page("app_pages/team_cards.py", title="Team Cards"),
        st.Page("app_pages/team_performance.py", title="Team Performance"),
        st.Page("app_pages/car_dna_view.py", title="Car DNA"),
        st.Page("app_pages/reliability.py", title="Reliability"),
        st.Page("app_pages/pit_strategy.py", title="Pit and Strategy"),
        *([st.Page("app_pages/power_units.py", title="Power Units")]
          if has_rows("power_units") else []),
        st.Page("app_pages/upgrades.py", title="Upgrades"),
        st.Page("app_pages/penalty_planner.py", title="Engine Penalty Planner"),
        st.Page("app_pages/failure_watch_view.py", title="Failure Watch"),
    ],
    "Drivers": [
        st.Page("app_pages/driver_standings.py", title="Driver Standings"),
        st.Page("app_pages/driver_cards.py", title="Driver Cards"),
        st.Page("app_pages/driver_ratings.py", title="Driver Ratings"),
        st.Page("app_pages/teammate_battles.py", title="Teammate Battles"),
        st.Page("app_pages/driver_market.py", title="Driver Market"),
    ],
       "Race": [
        st.Page("app_pages/pit_wall.py", title="Pit Wall"),
        st.Page("app_pages/ghost_lap_duel.py", title="Ghost Lap Duel"),
        st.Page("app_pages/circuit_explorer.py", title="Circuit Explorer"),
        st.Page("app_pages/tyre_lab.py", title="Tyre Lab"),
        st.Page("app_pages/race_insights.py", title="Race Insights"),
        st.Page("app_pages/penalties_log.py", title="Penalties Log"),
        st.Page("app_pages/race_won.py", title="Where the Race Was Won"),
        st.Page("app_pages/win_probability.py", title="Win Probability"),
        st.Page("app_pages/rain_crossover.py", title="Rain Crossover"),
        st.Page("app_pages/race_films.py", title="Race Films"),
        st.Page("app_pages/lap_one.py", title="Lap One"),
        st.Page("app_pages/race_radio.py", title="Team Radio"),
    ],
    "Simulator": [
        st.Page("app_pages/lap_simulator.py", title="Lap Simulator"),
        st.Page("app_pages/setup_garage.py", title="Setup Garage"),
        st.Page("app_pages/series_compare.py", title="Series Compare"),
        st.Page("app_pages/circuit_designer_view.py", title="Circuit Designer"),
        st.Page("app_pages/race_simulator.py", title="Race Simulator"),
        st.Page("app_pages/ai_strategist.py", title="AI Strategist"),
        st.Page("app_pages/tyre_science.py", title="Tyre Physics"),
        st.Page("app_pages/energy_lab.py", title="Energy Lab"),
        st.Page("app_pages/wind_tunnel_view.py", title="Wind Tunnel"),
        st.Page("app_pages/porpoising_lab.py", title="Porpoising Lab"),
        st.Page("app_pages/dirty_air_lab.py", title="Dirty Air Lab"),
        st.Page("app_pages/engine_room.py", title="Engine Room"),
    ],
    "Ladder": [
        st.Page("app_pages/ladder_series.py", title="Feeder Series"),
        st.Page("app_pages/superlicence.py", title="Superlicence Calculator"),
        st.Page("app_pages/scouting_report.py", title="Scouting Report"),
        st.Page("app_pages/career_mode.py", title="Career Mode"),
        st.Page("app_pages/other_series.py", title="Other Series"),
    ],
    "History": [
        st.Page("app_pages/history_champions.py", title="Champions"),
        st.Page("app_pages/history_eras.py", title="Eras"),
        st.Page("app_pages/history_records.py", title="Records"),
        st.Page("app_pages/history_seasons.py", title="Great Seasons"),
        st.Page("app_pages/history_drivers.py", title="Driver Profiles"),
        st.Page("app_pages/history_circuits.py", title="Circuit Profiles"),
        st.Page("app_pages/historic_circuits_view.py", title="Historic Circuits"),
        st.Page("app_pages/on_this_day.py", title="On This Day"),
        st.Page("app_pages/head_to_head.py", title="Head to Head"),
        st.Page("app_pages/rules_sandbox.py", title="Rules Sandbox"),
        st.Page("app_pages/calendar_planner.py", title="Calendar Planner"),
        st.Page("app_pages/all_time_ratings.py", title="All-Time Ratings"),
        st.Page("app_pages/driver_swap.py", title="Driver Swap"),
        st.Page("app_pages/ask_pit_wall.py", title="Ask the Pit Wall"),
    ],
    "Academy": [
        st.Page("app_pages/academy_home.py", title="Engineering Academy"),
        st.Page("app_pages/academy_parts.py", title="3D Part Explorer"),
        st.Page("app_pages/academy_m0.py", title="Start Here"),
        st.Page("app_pages/academy_m1.py", title="The Car as a System"),
        st.Page("app_pages/academy_m2.py", title="Tyres"),
        st.Page("app_pages/academy_m3.py", title="Vehicle Dynamics"),
        st.Page("app_pages/academy_m4.py", title="Aerodynamics"),
        st.Page("app_pages/academy_m5.py", title="Power Unit"),
        st.Page("app_pages/academy_m6.py", title="Transmission"),
        st.Page("app_pages/academy_m7.py", title="Brakes"),
        st.Page("app_pages/academy_m11.py", title="Race Engineering"),
        st.Page("app_pages/academy_m12.py", title="Strategy"),
        st.Page("app_pages/academy_m13.py", title="Circuits"),
    ],
    "Games": [
        st.Page("app_pages/beat_the_ai.py", title="Beat the AI"),
        st.Page("app_pages/beat_the_ai_teams.py", title="Beat the AI: Constructors"),
        st.Page("app_pages/race_engineer.py", title="Be the Race Engineer"),
        st.Page("app_pages/strategy_duel.py", title="Strategy Duel"),
        st.Page("app_pages/team_principal_game.py", title="Team Principal"),
        st.Page("app_pages/classic_races.py", title="Classic Races"),
        st.Page("app_pages/race_director.py", title="Race Director"),
        st.Page("app_pages/pit_crew_game.py", title="Pit Crew"),
        st.Page("app_pages/qualifying_game.py", title="Qualifying Game"),
        st.Page("app_pages/energy_challenge.py", title="Energy Challenge"),
        st.Page("app_pages/fantasy_optimizer.py", title="Fantasy Optimizer"),
        st.Page("app_pages/prediction_market.py", title="Prediction Market"),
        st.Page("app_pages/guess_the_driver.py", title="Guess the Driver"),
        st.Page("app_pages/race_the_ai.py", title="Race the AI Driver"),
        st.Page("app_pages/f1_quiz.py", title="F1 Quiz"),
    ],
    "About": [
        st.Page("app_pages/about.py", title="About"),
    ],
}
page = st.navigation(PAGES, position="top")


# ---------- one line under the title, for each page ----------

TAGLINES = {
    "Home": "Formula 1 predictions, replays and games, live every race weekend.",
    "Podium Predictor": "Pick a Formula 1 race and see who the model puts on the podium.",
    "Scoreboard": "Every prediction, locked in before the race and scored after it.",
    "Season Rewind": "A whole season, race by race, as our model would have called it.",
    "Championship Odds": "The rest of the season replayed thousands of times. Who still wins?",
    "Constructor Standings": "The teams' championship, and the charts behind every point.",
    "Team Cards": "Every team on the grid. Tap one to open its own page.",
    "Team Performance": "How fast each car really was, measured from the lap times.",
    "Reliability": "How often each team's cars reached the finish, and what stopped the rest.",
    "Pit and Strategy": "Who is quickest in the pit box, and which tyres each team chose.",
    "Power Units": "Engine parts used, and how close each driver is to a grid penalty.",
    "Upgrades": "Where the lap times show a car stepped forward, and what each team brought.",
    "Driver Standings": "The drivers' championship, race by race.",
    "Driver Cards": "Every driver on the grid. Tap one to open their own page.",
    "Driver Ratings": "Each driver's form through the season, with and without the car.",
    "Teammate Battles": "Same car, same weekend: who is winning inside each garage.",
    "Champions": "Every drivers' and constructors' title since 1950.",
    "Eras": "Which teams owned which decade, and how the sport itself has changed.",
    "Records": "The all-time leaderboards, for drivers and for constructors.",
    "Great Seasons": "The closest title fights, and the ones that went to the final race.",
    "Driver Profiles": "Any driver who has started a Grand Prix since 1950.",
    "Circuit Profiles": "Every track that has held a Grand Prix, and who has won there.",
    "Historic Circuits": "The Nordschleife and the old Hockenheim rebuilt in 3D, with a 1975, a 2001 and a 2026 car racing round.",
    "Feeder Series": "Formula 2, Formula 3 and F1 Academy since 2005: every championship, and who made it to F1.",
    "Superlicence Calculator": "The points a driver needs for Formula 1, a path of your own, and who on the ladder has them.",
    "Scouting Report": "Which feeder-series records turned into Formula 1 careers, tested honestly, and who looks next.",
    "Career Mode": "From Formula 4 at 15 to Formula 1, one season at a time, every year drawn from a real one.",
    "Other Series": "Formula E and IndyCar: every championship, and which of their drivers raced in F1.",
    "Series Compare": "One circuit lapped by an F1, F2, F3, Formula E and IndyCar-style car, and where the time goes.",
    "Calendar Planner": "How far F1 travels in a season, its estimated freight carbon, and a shorter order for the same races.",
    "Pit Crew": "Run a pit stop yourself: jack, four wheels, a safe release. Then see where it ranks among the real stops.",
    "Driver Market": "Who is likely to keep their seat, change team or leave F1 next season, from the results alone, and why.",
    "Team Principal": "Run a team through a real season: drivers, the cost cap, wind-tunnel time, upgrades and reliability, against every rival's real pace.",
    "Strategy Duel": "You and a friend engineer the same car in the same real race. Lock a call every five laps and see who called it better.",
    "Prediction Market": "Trade who wins the next race with play money. The market opens at our model's odds; see where the crowd disagrees.",
    "Fantasy Optimizer": "The best fantasy team within budget for the next race, picked by an integer program from the model's predictions, and how it would have done all season.",
    "Energy Challenge": "Set where the battery deploys on every straight of a 2026 lap, beat the engineer's plan and post it to the circuit's leaderboard.",
    "Qualifying Game": "Q1, Q2 and Q3 against the real laps of a real session: pick your run, your tow and how hard to push.",
    "On This Day": "The Grands Prix that were run on today's date, in any year.",
    "Head to Head": "Any two drivers from any era, side by side.",
    "F1 Quiz": "Ten questions, straight from the record books. No two quizzes are the same.",
    "Race Insights": "The weather, the flags and the position-swapping behind any race since 2023.",
    "Penalties Log": "Every stewards' decision of a season, as race control broadcast it.",
    "Ghost Lap Duel": "Two drivers' fastest laps, head to head, all the way round.",
    "Circuit Explorer": "Every circuit in its real shape and elevation. "
                        "Hills are shown 4× higher so you can see them.",
    "Tyre Lab": "How fast each tyre wears, measured from every clean racing lap.",
    "Pit Wall": "Watch any race back, lap by lap, with every car on the real track.",
    "Be the Race Engineer": "Make the pit calls for a real driver in a real race. Can you beat their team?",
    "Beat the AI": "Pick the podium before the race. After it, see if you beat our model.",
    "Beat the AI: Constructors": "Which three teams take the most points home? Pick before lights out.",
    "About": "Everything behind the app: the model, how it is tested, and the robot that runs it.",
    "Where the Race Was Won": "The gap between any two drivers, split into the start, pit stops, safety cars and racing laps.",
    "Lap One": "Places gained and lost between the grid and the end of the first lap, in every race since 2023.",
    "Team Radio": "Every published radio message of a race, transcribed and sorted by topic.",
    "Model Report Card": "Are the model's percentages worth trusting? Graded on races it never saw.",
    "Rules Sandbox": "Every championship since 1950, recomputed under the points rules you pick.",
    "Tyre Physics": "How a racing tyre grips, slides, overheats and shares its grip, with the real g-g of any lap.",
    "Tyres": "Module 2: how rubber grips, the magic formula, the friction circle, temperature and wear.",
    "Car DNA": "What each car was good at: corners, top speed, traction, downforce and drag, from its fastest lap.",
    "Vehicle Dynamics": "Module 3: weight transfer, balance, suspension, ride height, the differential and steering.",
    "Energy Lab": "The battery round a lap: harvest, deploy, clip. Pick where to deploy and beat the default.",
    "Porpoising Lab": "Why ground-effect cars bounced in 2022. Tune the floor and springs until it stops.",
    "Dirty Air Lab": "How much downforce a car loses following another, and why the 2022 rules changed it.",
    "Engine Room": "F1 engines from the 1980s turbos to 2026, with their sound synthesised live. Rev them, or drive a real lap.",
    "Aerodynamics": "Module 4: pressure, wings, the floor, the diffuser, vortices, dirty air, porpoising and active aero.",
    "Power Unit": "Module 5: thermodynamics, combustion, turbos, fuel flow, energy recovery, the battery and the 2026 engine.",
    "Transmission": "Module 6: the seamless-shift gearbox, gear ratios, the clutch and the drivetrain.",
    "Brakes": "Module 7: carbon-carbon brakes, brake-by-wire, bias, cooling, and the numbers behind a braking zone.",
    "Wind Tunnel": "A live airflow simulation in your browser: wings, flaps, separation and the wake.",
    "Engine Penalty Planner": "Where to fit new power units for the cheapest grid penalties, circuit by circuit.",
    "Failure Watch": "Did a car's lap times warn of trouble before it retired? An honest early-warning test.",
    "3D Part Explorer": "Rotate the car, the wings, the power unit and a wheel corner. Explode them and tap any part.",
    "Race Simulator": "Replay a real Grand Prix 400 times, then change a strategy, force a safety car, or find pace.",
    "Win Probability": "How every driver's chances moved through a real race, replayed from each lap's real positions.",
    "Rain Crossover": "In wet races, when slicks became faster than intermediates, and who switched at the right moment.",
    "Race Engineering": "Module 11: the weekend, run plans, setup, parc fermé, qualifying and the driver–engineer radio.",
    "Strategy": "Module 12: stops, degradation, the undercut, safety cars, game theory, Monte Carlo, RL and wet races.",
    "Circuits": "Module 13: how circuits differ, a 3D tour of every circuit corner by corner, history and designing your own.",
    "All-Time Ratings": "Every driver since 1950 with the car taken out, against their own era or on one scale.",
    "Driver Swap": "Put any driver from any era in any car, and replay that season 2,000 times.",
    "Ask the Pit Wall": "Ask anything about F1 since 1950 in plain English, answered from our own archive.",
    "Classic Races": "Famous Grands Prix since 1996. Take control of one car's strategy and try to beat history.",
    "Race Director": "Real incidents from race control. Make the stewards' call, then see what they decided.",
    "Guess the Driver": "Two teammates' laps from the same race. Spot whose is whose from the telemetry, then see the AI's call.",
    "Race the AI Driver": "Drive a real circuit yourself, against a driver our AI learned from real laps.",
    "Race Films": "The story of any race since 2023, written from its data and read aloud by your browser.",
    "AI Strategist": "A reinforcement-learning agent learns pit strategy by trial and error, then takes on the real teams.",
    "Lap Simulator": "Our physics model drives a real circuit, next to the real fastest lap.",
    "Circuit Designer": "Draw your own circuit. The lap simulator drives it as you draw.",
    "Setup Garage": "Change the wing, the power, the weight or the tyres, and see what each is worth here.",
    "Engineering Academy": "How a Formula 1 car works, from the tyres up. Three depths, live demos, real data.",
    "Start Here": "Module 0: the physics you need, what makes a car fast, and how to read telemetry.",
    "The Car as a System": "Module 1: the parts, the rules, what each change is worth, and the compromises.",
}


# ---------- header, with the theme switch on the right ----------

if "dark" not in st.session_state:
    st.session_state.dark = True

title_col, switch_col = st.columns([5, 1], vertical_alignment="center")
with title_col:
    hero("Podium Predictor" if page.title == "Home" else page.title, TAGLINES.get(page.title, ""))
with switch_col:
    st.toggle("Dark theme", key="dark")

apply_style(st.session_state.dark)
ui_kit.kit_css()


# ---------- the chosen page ----------

try:
    page.run()
finally:
    stamp_modules()

# Two things Streamlit cannot be told in Python: dropdowns should be tapped rather than
# typed into, and a chart tooltip opened by a finger has no mouse to leave, so it used
# to sit on the screen covering the page. This runs after the page so it also catches
# anything the page just drew.
ui_kit.polish()

