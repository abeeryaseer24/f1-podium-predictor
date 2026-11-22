# Roadmap: everything next

Both rounds of ideas merged into one list, de-duplicated and put in build order. Every page
lives in the existing Streamlit app and looks like it was always there.

Status: ✅ marks what is live. Phase 1 (lap simulator, 3D kit, Lap Simulator, Setup Garage, Academy shell and Modules 0–1) Phase 2 (Where the Race Was Won, Lap One, Team Radio, Model Report Card, Rules Sandbox) Phase 3 (tyre physics, Tyre Physics, Car DNA, Academy Modules 2–3) and Phase 4 (energy model, Energy Lab, Wind Tunnel, Porpoising and Dirty Air Labs, Engine Room, Engine Penalty Planner, Academy Modules 4–7) Phase 5 (race engine, Race Simulator, Win Probability, Rain Crossover, Academy Modules 11–12) and Phase 6 (All-Time Ratings, Driver Swap, Classic Races, Race Director, Race Films) and Phase 7 (AI Strategist, Failure Watch, Ask the Pit Wall, Guess the Driver, Race the AI Driver) are done, plus the 3D Part Explorer.

---

## 0. Ground rules (apply to every item)

### Design: match what is already live
- **Colours and fonts come from `src/style.py` only**: `--pp-red #e10600`, `--pp-bg`, `--pp-panel`,
  `--pp-panel2`, `--pp-text`, `--pp-muted`, `--pp-border`, Saira Condensed 800 for headings,
  Inter for text. Both themes (dark and light) on every page, with no hard-coded colours.
- **Page furniture comes from `src/ui_kit.py` and `src/style.py`**: `hero()`, `section()`,
  `banner()`, `chips()`, `league()`, `heat()`, `diverge()`, `feed()`, `versus()`, `sheet()`,
  `stat_strip()`, `empty_note()`. Add a new widget to the kit if it's needed, never inline on one page.
- **Charts go through `src/charts.py`** (`theme()`, `dress()`, `team_scale()`), so team colours
  and axes match the rest of the app.
- **3D and live simulations** use the same Three.js setup as `src/track3d.py` / `src/pitwall3d.py`
  (three@0.160.0 from jsdelivr, embedded with `components.html`), reading the theme tokens
  passed in from Python. New shared file: `src/sim3d.py` (camera rig, track mesh, car marker,
  labels, theme), so every 3D page feels the same.
- **Plain words.** Same voice as the existing pages: short sentences, a one-line subtitle under
  each title, an honest "what this can't tell you" note on every model page.
- **Phones.** Every page works at phone width, as now.

### Engineering
- Python modules in `src/` with a docstring header and a `python src/x.py <year> <round>` test
  entry, like the existing ones.
- **Heavy work runs offline**: in the GitHub Actions pipeline or on a laptop, never in the
  Streamlit app. This covers RL training, Whisper transcription, Bayesian fitting and car DNA fits.
  The app only reads the results files. (Streamlit Community Cloud has about 1 GB of RAM.)
- **Real-time interaction runs in the browser** (JavaScript inside the component). Python
  precomputes, and the JS steps the simulation, so sliders feel instant.
- Every model gets a check in `src/checks.py` and a row in About.
- The no-future rule extends to every new predictive model.

### Zero paid services
Nothing in this roadmap may need a paid API, a paid plan or a credit card. What we use, and the
free limit to stay inside:

| Need | Free option | Limit to respect |
|---|---|---|
| Hosting the app | Streamlit Community Cloud (as now) | ~1 GB RAM: heavy work stays offline |
| Heavy compute (Whisper, RL training, Bayesian fits, car DNA, small local language model) | GitHub Actions: standard runners are free for public repositories | 6 h per job, ~7 GB RAM, CPU only; split long jobs, cache results, or run them on a laptop and commit the output |
| Database (Beat the AI, Strategy Duel, Prediction Market, leaderboards) | Supabase free tier (as now) | 500 MB; free projects pause after a week with no traffic, so the pipeline pings it |
| Data | Jolpica, OpenF1 history, MultiViewer, OpenStreetMap, Copernicus/SRTM elevation | OpenF1 *live* is paid, so live features run on replays; cache everything |
| Speech to text | `faster-whisper` (open source) in Actions | Only new races, once each |
| Text to speech | Browser Web Speech API (free, on the visitor's device), or Piper TTS (open source) in Actions for audio files | Voices vary by browser with Web Speech |
| Writing text (reports, narration) | Template-based text generation, optionally polished by a small open model run in Actions (see A13) | Once per race, never per visitor |
| Big files | GitHub Releases for large assets instead of the repo | Keep the repo light |

If a feature can only be done with a paid service, it's dropped or redesigned, not paid for.

### New menu groups (in `app.py`)

```
Home · Predictor · Teams · Drivers · Race · Simulator · Ladder · History · Academy · Games · About
```
`Simulator`, `Ladder` and `Academy` are new. Everything else slots into the existing groups.

---

## 1. Engines (the foundation everything else runs on)

| # | Module | What it is | Feeds |
|---|---|---|---|
| E1 ✅ | `src/lapsim.py` | **Lap-time simulator.** A quasi-steady-state point-mass car on the real 3D track (`track.parquet` x/y/z): curvature → corner speed limit from grip + downforce, forward pass (power, drag, gears), backward pass (braking), elevation and banking. Calibrated per circuit against the real fastest lap and its speed trace. | Nearly everything |
| E2 ✅ | `src/race_engine.py` | **Race engine.** Lap by lap for the whole field: base pace (from E1/E3), tyres (`tyres.py`), fuel burn, pit loss, dirty air, overtaking (M2), safety car hazards (M1), reliability, weather, and rivals that react to each other. Replaces the "nobody else reacts" assumption in `strategy.py`. | Race sim, classic races, RL, games |
| E3 ✅ | `src/car_dna.py` | **Car DNA.** Inverse E1: fit each car's downforce, drag and power to real OpenF1 speed traces, per team per race since 2023. | Car DNA page, E2 pace, counterfactuals |
| E4 ✅ | `src/energy.py` | **Power unit and energy model.** 2026 rules: 50/50 ICE and electric, MGU-K harvest and deploy limits, battery state of charge, active aero modes, overtake mode. Older eras (V10, V8, 2014 hybrid with MGU-H) as presets. | Energy Lab, PU pages, Academy |
| E5 ✅ | `src/tyre_physics.py` | **Tyre model.** Pacejka magic formula, load sensitivity, a one-node temperature model, wear. Grip for E1 and the Academy. | E1, Tyre Physics, Academy |
| E6 ✅ | `src/sim3d.py` | **Shared 3D kit** (see design rules). | Every 3D page |

---

## 2. Simulator (new menu group)

| # | Page | What the visitor does |
|---|---|---|
| S1 ✅ | **Lap Simulator** | Pick a circuit, watch the simulated car lap it in 3D next to the real pole lap, and see the speed trace overlay and where they disagree. |
| S2 ✅ | **Setup Garage** | Wing level, ride height, mass, power, brake bias, tyre compound → lap time and per-corner gains and losses. "A Monza wing at Monaco costs 1.8 s." Shows sensitivities: what 10 kg, 10 points of downforce and 10 kW are each worth at this track. |
| S3 ✅ | **Energy Lab 2026** | Battery state of charge round a lap, clipping on straights, harvest zones. Game: place your own deploy and harvest zones and try to beat the default lap. |
| S4 ✅ | **Race Simulator** | Run any race on E2 with your own changes (safety car on lap 20, rain from lap 35, a car's pace +0.3 s) and get the result distribution over 1,000 runs. |
| S5 | **Circuit Designer** | Draw a track (spline editor). E1 laps it, E2 races it, and you get a rating: lap time, top speed, overtaking chance, tyre wear, "processional / strategy race / chaos". Share a link to your track. |
| S5 ✅ | **Circuit Designer** | Drag points to draw your own circuit; the lap simulator (ported to the browser) drives it live with a typical calibrated car: lap time, corners, overtaking spots and where it brakes. |
| S6 ✅ | **Wind Tunnel** | A browser CFD toy (WebGL lattice-Boltzmann) round a wing profile and a car silhouette. Change the angle of attack, see the pressure and the wake, and read lift and drag. |
| S7 ✅ | **Dirty Air Lab** | Downforce lost behind another car at 0.5 / 1 / 2 s, for the 2017–21 cars vs 2022+ vs 2026, and what that does to overtaking. |
| S8 ✅ | **Porpoising Lab** | A spring-mass car with ground-effect downforce. Lower the ride height and watch it start bouncing (2022). Adjust stiffness and floor design to stop it. |
| S9 ✅ | **Tyre Physics** | Pacejka curves, the friction circle, g-g diagrams from real telemetry, and a temperature window toy (graining vs blistering). |
| S10 ✅ | **Power Units Through the Eras** (Engine Room) | 3.0 V10, 2.4 V8, 2014 V6 hybrid, 2026. Each has a thermodynamic model, an energy-flow Sankey and **synthesized engine sound** (Web Audio, made from rpm and firing order), plus an rpm slider. |
| S11 ✅ | **Rain Crossover** | When to switch inters to slicks (and back) as the track dries, tested against real wet races (`weather.parquet` + laps). |
| S12 ✅ | **Engine Penalty Planner** | When to take new power unit components across a season for the cheapest grid penalties (builds on `power_units.csv`). |
| S13 | **Series Compare** | The same circuit lapped by F1, F2, F3, Formula E and an IndyCar-style car on E1, showing where the time goes. |

---

## 3. Analysis (slots into Race, Teams, Drivers, Predictor)

| # | Page / feature | Group | What it is |
|---|---|---|---|
| A1 ✅ | **Car DNA** | Teams | E3 as a radar per team per race (slow / medium / fast corners, top speed, traction), plus how each upgrade in `upgrades.csv` moved it. |
| A2 ✅ | **Where the Race Was Won** | Race | Each winning margin (and any driver's result) split into qualifying, start, pure pace, strategy, pit stops and luck (safety car timing), as a waterfall per race. |
| A3 ✅ | **Rules Sandbox** | History | Recompute every championship 1950–2026 under any points system, dropped results, no fastest-lap point, sprints everywhere, reversed grids. "Which titles change hands?" |
| A4 ✅ | **Team Radio** | Race | Radio clips (OpenF1's team_radio list; our own `radio.parquet` is the strategist's calls) transcribed offline with open-source `faster-whisper` in GitHub Actions (free, new races only), sorted by topic (tyres, strategy, damage, complaints) on the race timeline. Test: does radio predict pit stops? Links to OpenF1 audio, never rehosted. |
| A5 ✅ | **Lap One** | Race | Places gained and lost at the start by grid slot, clean vs dirty side, distance to Turn 1 and circuit (M3). |
| A6 ✅ | **Win Probability** | Race | A live-style win-chance chart through each race, updated lap by lap (M12). |
| A7 ✅ | **Driver Swap** | Drivers | Counterfactuals: any driver in any car, any era (M4 + E2). "Alonso in the 2023 Red Bull." |
| A8 ✅ | **All-Time Ratings** | History | Era-adjusted driver ratings 1950–2026 with uncertainty bands (M4 + M5). The honest GOAT list. |
| A9 ✅ | **Model Report Card** | Predictor | Brier score, log loss, reliability diagrams and conformal ranges for the predictor (M11), added to Scoreboard and About. |
| A10 ✅ | **Failure Watch** | Teams | Cars whose lap times or telemetry looked wrong before they retired, and how early the model flagged them (M9). |
| A11 | **Driver Market** | Drivers | Who is likely to move seats next season and why (M10). |
| A12 | **Calendar Planner** | History | Travel distance and freight carbon of the real calendar vs an optimised one (a travelling-salesman problem with fixed-date constraints). |
| A13 ✅ | **Ask the Pit Wall** (free version) | Home / About | Three free pieces, no paid API: **(1) Question Builder**: about 60 question patterns with slots ("who gained the most places at {circuit} in {season}?"). The visitor types freely and fuzzy matching (`rapidfuzz`) plus a driver/team/circuit/season name list picks the pattern and fills the slots, or they build the question from dropdowns. Every answer is a real pandas query with a table and chart, so it's never made up. **(2) Race reports**: after each race the pipeline finds the "story beats" (decisive pit stop, biggest climber, safety car winner and loser, teammate battle, fastest lap, a record broken), scores how interesting each is, and writes them up from varied sentence templates. **(3) Optional polish**: a small open-source model (e.g. a 1–3B instruct model through `llama.cpp`, CPU-only) runs once per race in GitHub Actions to smooth the template text. The facts come only from the template, and the check refuses any number that isn't in the data. |

---

## 4. Models (ML / statistics, built offline)

| # | Model | Method | Used by |
|---|---|---|---|
| M1 | Safety car hazard | Survival model per lap, circuit and conditions | E2, strategist, S4 |
| M2 | Overtaking | Logistic / gradient boosting on pace gap, DRS or overtake mode, tyre offset, circuit | E2 |
| M3 | Lap one | Ordinal model on grid slot, side, distance to Turn 1 | A5, predictor feature |
| M4 ✅ | Driver vs car | Bayesian hierarchical or TrueSkill-through-time, 1950–2026 | A7, A8 |
| M5 | Pre-1996 pace | Bayesian pace from finishing gaps and laps down | A8, classic races |
| M6 ✅ | RL strategist | PPO or MCTS trained inside E2. Compared with the Monte Carlo strategist and the real teams. A policy map (box or stay by tyre age and gap). | Pit Wall, Race Engineer, C1 |
| M7 ✅ | AI driver | Imitation learning on telemetry, driving E1 | G9 |
| M8 ✅ | Who's driving? | Classifier on one lap's throttle, brake and steering traces | G4, Drivers |
| M9 ✅ | Failure early warning | Anomaly detection on laps and telemetry | A10 |
| M10 | Driver market | Classification on contract, form and teammate gap | A11 |
| M11 | Calibration | Reliability curves, conformal prediction | A9 |
| M12 | In-race win probability | E2 restarted from each lap's state | A6 |
| M13 | Radio NLP | Whisper + a topic classifier | A4 |
| M14 | Scouting | Feeder-series results → F1 career outcome | L3 |

---

## 5. Ladder (new menu group: F2, F3, F1 Academy and beyond)

| # | Page | What it is |
|---|---|---|
| L1 | **F2 / F3 / F1 Academy** | Standings, results, driver cards and team cards in the same card style as F1. **Data caveat:** there is no public API like Jolpica, so results come from FIA timing PDFs or the series sites. Check their terms first, and cache everything. |
| L2 | **Superlicence Calculator** | Points by series and position, as in the FIA rules. Who on the ladder qualifies. |
| L3 | **Scouting Report** | M14: which feeder records turned into good F1 careers, and who looks next. |
| L4 | **Career Mode** | Start in karting, then F4, F3, F2 and F1. Make decisions (team, budget, risk), with results drawn from real distributions for each series. |
| L5 | **Other Series** | Formula E (reuses E4 energy), WEC/Le Mans (multi-class traffic, driver stints) and IndyCar (ovals, fuel saving), each as a ruleset on E1/E2 plus results data where a free source exists. |

---

## 6. Classic races and race control (Race / Games)

| # | Page | What it is |
|---|---|---|
| C1 ✅ | **Classic Races** | Famous races since 1996 (Jolpica lap times; pit stops from about 2011), each with a case file, a 3D replay and **take control**: run one car's strategy on E2 and try to beat history. Starter set: Abu Dhabi 2021, Hungary 2021, Brazil 2008, Japan 2005, Germany 2019, Silverstone 2022, Monaco 2024. |
| C2 ✅ | **Race Director** | Replay real incidents. You call the safety car, VSC, red flag and penalties, and get compared with the real decisions (race control feed + Penalties Log). |
| C3 ✅ | **Race Films** | A script built from the same story beats as the A13 race reports, a timeline, the 3D replay and a voice-over from the browser's free Web Speech API (or Piper TTS audio made in Actions). |
| C4 | **Replay Commentary** | Event-driven commentary over the Pit Wall replay, with no AI service: each event in the replay (overtake, pit stop, safety car, fastest lap, retirement, gap closing under 1 s) triggers a line from a phrase bank, with variety and a cooldown so it doesn't repeat itself. Spoken with Web Speech. |

---

## 7. Games (Games group)

| # | Game | What it is |
|---|---|---|
| G1 | **Team Principal** | A full season: budget cap, wind-tunnel hours by championship position, upgrade timing, driver market, race weekends on E2. |
| G2 | **Strategy Duel** | Two visitors run strategy on the same real race at the same time (Supabase, which is already set up). |
| G3 | **Prediction Market** | Trade race outcomes with play money. Crowd prices vs the model. |
| G4 ✅ | **Guess the Driver** | See one lap of telemetry and name the driver. Then see what M8 guessed. |
| G5 | **Pit Crew** | A reaction-timed pit stop against each team's real stop-time distribution. |
| G6 | **Qualifying Game** | Q1 to Q3: pick your run timing, tow and track evolution. |
| G7 | **Fantasy Optimizer** | An integer program that picks a budget-capped fantasy team from the model's predicted points. |
| G8 | **Energy Challenge** | The game half of S3, with a leaderboard per circuit. |
| G9 ✅ | **Race the AI Driver** | Drive the lap yourself in the browser on E1's physics, against M7 and the real fastest lap. |

---

## 8. Presentation upgrades (across the app)

- P1 ✅ **Onboard camera** in every 3D page: a camera that follows the racing line and the real elevation, at real speed.
- P2 ✅ **Night races, rain and time of day** in `sim3d.py` and the Pit Wall (night races start at night, and the replay rains when the real race did).
- P3 ✅ **Illustrative 3D car** (the 3D Part Explorer) (our own design, no team livery or branding). It's used across the Academy with an exploded view, x-ray, airflow particles and component highlighting.
- P4 **Historic circuits in 3D** (old Hockenheim, the Nordschleife, Kyalami, the old Spa) from OpenStreetMap raceway geometry plus open elevation data.
- P5 **Technical report** (`docs/report.md` + PDF): every model, assumption, limitation and validation.

---

## 9. The Engineering Academy (new menu group)

> Name: the real **F1 Academy** is a racing series (and it's in the Ladder section), so the course
> is called **Engineering Academy** to avoid confusion.

**Goal:** someone with school physics finishes it understanding how a modern F1 car works,
why it's designed that way, and how a race is engineered, to the depth of a good motorsport
engineering degree module.

### How every chapter works
- **Three depths on one page:** *Basics* (no maths), *Engineer* (equations with `st.latex`),
  *Deep dive* (derivations, real numbers, papers to read). A toggle at the top, remembered in
  `st.session_state`.
- **One live widget per chapter**, running on the real engines (E1–E5). You change a value and
  see the physics.
- **"In the data"**: each idea shown in real race data from the app (Tyre Lab, Ghost Lap Duel,
  Pit Wall…), with a link.
- **3D**: the illustrative car (P3) highlighting the part being discussed.
- **Check yourself**: 5 questions at the end (reuses the `quiz.py` machinery). Progress is kept
  per visitor, and finishing a module gives a share card (reuses `share_card.py`).
- **Glossary** with hover definitions, and a search across all chapters.
- Every number is sourced: FIA technical regulations, published papers, team or supplier
  talks. Estimates are marked as estimates.

### Curriculum

**Module 0: Start here**
0.1 How to use the Academy · 0.2 Units and the physics you need (force, energy, power, pressure, vectors) · 0.3 What makes a car fast: the lap-time equation · 0.4 Reading telemetry: speed, throttle, brake, gear, delta

**Module 1: The car as a system**
1.1 Anatomy of an F1 car (3D exploded tour) · 1.2 The regulations as a design box · 1.3 Lap-time sensitivities: mass, drag, downforce, power, grip *(widget: S2 sensitivities)* · 1.4 Design compromise: the same car at Monaco and Monza

**Module 2: Tyres, the only contact with the road**
2.1 How rubber grips: adhesion, hysteresis, the contact patch · 2.2 Slip angle and slip ratio · 2.3 The magic formula *(widget: Pacejka curves)* · 2.4 The friction circle and g-g diagrams *(real telemetry)* · 2.5 Load sensitivity: why downforce gives diminishing returns · 2.6 Temperature and pressure windows · 2.7 Wear, graining, blistering, the cliff · 2.8 Compounds C1–C6, construction, wets and inters · 2.9 Degradation in the data *(Tyre Lab)*

**Module 3: Vehicle dynamics**
3.1 Weight transfer: longitudinal and lateral · 3.2 Balance: understeer, oversteer, the yaw moment · 3.3 Suspension layouts: push rod, pull rod, double wishbone · 3.4 Kinematics: camber, toe, caster, anti-dive, anti-squat · 3.5 Springs, dampers, heave elements, roll stiffness distribution · 3.6 Ride height and rake *(widget)* · 3.7 Differentials and traction · 3.8 Steering · 3.9 The quasi-steady-state lap simulator, built step by step *(widget: E1 internals)*

**Module 4: Aerodynamics**
4.1 Pressure, Bernoulli and why air pushes · 4.2 Boundary layers, separation, the Reynolds number · 4.3 Lift, drag and efficiency (L/D) · 4.4 Front wing: load, outwash, the Y250 vortex · 4.5 Rear wing, beam wing, DRS · 4.6 The floor: Venturi tunnels and ground effect *(widget: S6)* · 4.7 Diffuser and floor edges · 4.8 Vortices as tools · 4.9 Sidepods, bodywork and cooling inlets · 4.10 Dirty air and following *(widget: S7)* · 4.11 Porpoising and bouncing *(widget: S8)* · 4.12 Aero maps: ride height, yaw and steer sensitivity · 4.13 CFD and the wind tunnel: the ATR rules and correlation · 4.14 2026 active aero

**Module 5: Power unit**
5.1 Engine thermodynamics: the Otto cycle and real efficiency · 5.2 Combustion: lean burn, turbulent jet ignition, knock · 5.3 Turbocharging · 5.4 The fuel-flow limit and why it drives efficiency · 5.5 Energy recovery: MGU-K (and the old MGU-H) · 5.6 The battery: cells, cooling, state of charge · 5.7 Energy management over a lap *(widget: S3)* · 5.8 Sustainable fuels · 5.9 The 2026 power unit · 5.10 Reliability, component allocation and penalties *(widget: S12)* · 5.11 Engines through history: V12, V10, V8, hybrid *(widget: S10 with sound)*

**Module 6: Transmission and drivetrain**
6.1 The seamless-shift gearbox · 6.2 Choosing gear ratios *(widget)* · 6.3 Clutch, launch and the race start · 6.4 Driveshafts, uprights and hubs

**Module 7: Brakes**
7.1 Carbon-carbon brakes and their temperature window · 7.2 Brake-by-wire and rear energy recovery · 7.3 Brake bias and migration · 7.4 Brake cooling and ducts · 7.5 Braking in the data: deceleration of 5–6 g

**Module 8: Chassis, materials and safety**
8.1 The carbon-fibre monocoque: layup, autoclave, stiffness · 8.2 Weight, ballast and the minimum mass · 8.3 Crash structures and FIA tests · 8.4 The halo, HANS and the survival cell · 8.5 Fire, medical car and circuit safety · 8.6 Great crashes and what engineering learned (Grosjean 2020)

**Module 9: Cooling and thermal management**
9.1 The heat budget: where the energy goes · 9.2 Radiators, louvres and sidepod design · 9.3 Hot races and cooling compromises · 9.4 Driver cooling

**Module 10: Electronics, data and simulation**
10.1 The standard ECU and around 300 sensors · 10.2 Telemetry and the garage · 10.3 The steering wheel · 10.4 Data analysis like an engineer: overlays, deltas, mini-sectors *(Ghost Lap Duel)* · 10.5 Driver-in-the-loop simulators · 10.6 Correlation: simulation vs track

**Module 11: Race engineering**
11.1 The race weekend from an engineer's chair · 11.2 Practice run plans · 11.3 Setup work and the setup sheet *(widget: S2)* · 11.4 Parc fermé · 11.5 Qualifying preparation · 11.6 Driver and engineer communication *(Team Radio)*

**Module 12: Strategy**
12.1 The race as an optimisation problem · 12.2 Tyre deg + fuel effect + pit loss · 12.3 Undercut and overcut · 12.4 Safety cars and VSCs · 12.5 Game theory: reacting to rivals · 12.6 Monte Carlo strategy *(Pit Wall)* · 12.7 Reinforcement learning for strategy *(M6)* · 12.8 Wet races and crossovers *(S11)*

**Module 13: Circuits (with 3D tours)**
13.1 How circuits differ: power, downforce, braking, tyre energy · 13.2 **A tour of every circuit with data**: a 3D flyover (camera along the racing line with real elevation), then a corner-by-corner guide with speed, gear, braking point, g-load and overtaking spots, then setup demands and tyre wear, then what the lap simulator says matters most here · 13.3 Historic circuits in 3D (P4) · 13.4 Designing a circuit *(widget: S5)*

**Module 14: Rules, money and the business**
14.1 Technical vs sporting regulations · 14.2 The cost cap and what it limits · 14.3 How teams are organised: aero, vehicle performance, race team · 14.4 Testing limits and the ATR · 14.5 Protests, appeals and grey areas

**Module 15: History of F1 engineering**
15.1 Front-engine to mid-engine · 15.2 Wings arrive (1968) · 15.3 Ground effect (1978) and why it was banned · 15.4 The turbo era · 15.5 Active suspension and driver aids (1992–93) · 15.6 The V10 years · 15.7 Blown diffusers, the double diffuser, the F-duct · 15.8 DAS and clever loopholes · 15.9 The hybrid era · 15.10 2022 ground effect returns · 15.11 2026 and after

**Module 16: Capstone, design your car**
Choose a circuit, set the car's aero, mass, power and setup within the regulations, then E1 laps it, E2 races it against the real grid, and you get a debrief explaining your result with everything from the course.

---

## 10. Build order

Each phase ships something visible and finishes in a working app.

| Phase | Builds | Why first |
|---|---|---|
| **1. Foundations** ✅ | E6 `sim3d.py`, design checks for new pages, E1 lap simulator, S1, S2 · Academy shell (menu, chapter template, depth toggle, glossary) + Modules 0–1 | E1 is the base of everything, and the Academy template is needed by every later module |
| **2. Quick wins on existing data** ✅ | A2 Where the Race Was Won, A3 Rules Sandbox, A5 Lap One, A9 Report Card, A4 Team Radio | High impact with the data already on disk |
| **3. Car physics** ✅ | E5 tyres, E3 Car DNA, A1, S9 · Academy Modules 2–3 | Fills E1 with real grip and real cars |
| **4. Aero and power** ✅ | E4 energy, S3, S6, S7, S8, S10, S12 · Academy Modules 4–7 | The flagship engineering content |
| **5. Race engine** ✅ (safety cars and overtaking use data-derived rates; fuller ML versions of M1/M2 are still open) | M1, M2, E2, S4, S11, A6 · Academy Modules 11–12 | Unlocks every race-level feature |
| **6. History playable** ✅ (M5 pre-1996 pace not built: the archive has finishing orders but no time gaps before 1996, so the era ratings cover those years from finishing order instead) | M4, M5, A7, A8, C1, C2, C3 | Built on E2 and M4 |
| **7. AI showcase** ✅ | M6 RL strategist, M7, M8, M9, G4, G9, A10, A13 | Needs E1, E2 and the data pipeline |
| **8. Circuits and 3D** (in progress: P1, P2, S5 and Academy Module 13 done; P4 historic circuits left) | P1, P2, P3, P4, S5 · Academy Module 13 (tours) | Uses everything in `sim3d.py` |
| **9. Ladder** | L1–L5, M14, S13 | Biggest data-sourcing risk, so it waits until the core is solid |
| **10. Games and polish** | G1–G3, G5–G8, A11, A12, C4 · Academy Modules 8–10, 14–16 · P5 technical report | Full set, then the write-up |

## 11. Risks to watch

- **Streamlit limits**: heavy pages must keep the work in the browser or precomputed. If a page
  can't, it's a sign to move that page to a separate front end later.
- **Data sources**: F2/F3 results and historic circuit geometry need checking for terms of use.
  OpenF1's real-time feed may need their paid tier, so live features may have to run as replays.
- **Copyright and branding**: our own car model and art only. No team liveries, logos, onboard
  footage or rehosted radio audio.
- **Staying free**: no paid APIs anywhere (see the zero-paid-services table). Watch the GitHub
  Actions time per run, the Supabase 500 MB limit and its pause after a quiet week. The repository
  must stay public for free Actions minutes; if it ever goes private, the free minutes are capped.
- **Optional browser AI (experiment only)**: a small language model can run inside the visitor's
  own browser (WebLLM or transformers.js, on their GPU, free to us) for free-text questions. It's
  a large download and needs WebGPU, so it's an opt-in "try it" toggle only, never required.
- **Honesty**: every simulation page says it is a teaching model, what it ignores, and how
  it was checked against reality, the same standard the predictor already holds.
