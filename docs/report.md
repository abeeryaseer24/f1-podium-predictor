# F1 Podium Predictor: Technical Report

*Every model, assumption, limitation and validation in the app. Figures are as of 23 November 2026 (after
round 21 of the 2026 season). Run the commands in section 10 to reproduce them.*

---

## 1. What the project is

A Formula 1 app that runs itself. Its core is a ranking model that predicts the whole finishing order of
every Grand Prix, locks the prediction on race day, scores it after the race and retrains on the new result
with no human in the loop. Around it sit three physics engines (a lap simulator, a race simulator and a
power-unit energy model), a set of machine-learning models, analysis pages, games and a 17-module
engineering course.

**Constraints that shaped every decision**

- **Free services only.** No paid APIs or language models. Data comes from free public sources, compute from
  GitHub Actions and Streamlit Community Cloud, storage from a free Supabase project. Where a feature
  could only be built with a paid service, it was redesigned or dropped.
- **No leakage.** Anything presented as a prediction uses only information available before the event, and
  every reported accuracy figure comes from out-of-sample tests.
- **Honesty about limits.** Each page states what is real data and what is illustrative.

**Stack.** Python, pandas, NumPy, SciPy, scikit-learn, Streamlit and Altair; Three.js for 3D; Web Audio and
the Web Speech API in the browser; GitHub Actions for the pipeline; Supabase for visitors' game data.

---

## 2. Data

| Source | What | Years | Licence / terms |
|---|---|---|---|
| Jolpica-F1 (Ergast successor) | Results, grids, qualifying, calendar, driver dates of birth | 1950–2026 | Free API, cached locally |
| OpenF1 | Laps, car data (speed, rpm, gear, throttle, brake), positions, tyres, pit stops, race control, team radio list, starting grid | 2023–2026 | Free API, cached; audio linked, never rehosted |
| MultiViewer | Corner positions and numbers | current circuits | Free API |
| OpenStreetMap (Overpass API) | Historic circuit shapes | — | © OpenStreetMap contributors, ODbL |
| OpenTopoData (EU-DEM 25 m) | Elevation for historic circuits | — | Free public API |
| Wikipedia season articles | F2/GP2, F3/GP3, F1 Academy, Formula E, IndyCar results | 2005– | CC BY-SA 4.0 |

Each prepared race (`data/races/<season>_<round>/`) holds laps, the 3D track (`track.parquet`, x/y/z in
decimetres), pit stops, race control, weather and positions. There are 90 prepared races (2023–2026).

### The pipeline

`src/pipeline.py`, run by GitHub Actions every three hours:

1. Download new results; safety checks (no lost, missing or duplicated results; exactly one P1, P2 and P3 per race).
2. Rebuild features; retrain; champion-vs-challenger decision (section 3.4).
3. Build race history, the tyre book, 3D race files and the strategist's calls.
4. Lock the prediction 8 hours before lights out with real qualifying and the official grid.
5. Incremental jobs: team-radio transcription (faster-whisper), driving styles, the AI driver, circuit tours,
   qualifying sessions, the energy engineer's plans, the driver market.
6. Final checks; push; ping Supabase so the free project isn't paused.

If any check fails, nothing is pushed.

---

## 3. The predictor

### 3.1 Model

A **Plackett–Luce ranking model**. Each driver $i$ in a race gets a strength $s_i = \beta^\top x_i$, a linear
function of standardised features. The probability of a finishing order is

$$P(\pi) = \prod_{k=1}^{K} \frac{e^{s_{\pi_k}}}{\sum_{j \ge k} e^{s_{\pi_j}}},$$

fitted by maximum likelihood (SciPy) on the first $K$ finishers of every race since 2016 (the live recipe uses
$K = 10$), with L2 regularisation. Win, podium and expected-position figures come from replaying each race
5,000 times: strength divided by a fitted "luck" scale (0.6) plus Gumbel noise, then sorted. That Gumbel
sampling is exactly Plackett–Luce.

### 3.2 Features

All computed from races before the one being predicted, and compared within each race (so the model learns
"faster than the rest of this field", not absolute values): grid and qualifying position (and logs of
them), gap to pole, the team's best qualifying, teammate qualifying gap, recent and season form for driver
and team (finish, qualifying, DNF), career and circuit podium rates, average places gained, how much the
grid matters at the circuit, and interactions such as grid × circuit.

### 3.3 Starting grid

For upcoming races: (1) OpenF1's official starting grid, which includes penalties; (2) a hand-kept penalties
file as backup; (3) plain qualifying. Before qualifying, an estimated grid from recent form.

### 3.4 Champion vs challengers

Several recipes (first 10 / first 5 / first 15 finishers with stronger smoothing; a short-term feature set)
take the same season-by-season backtest whenever new results arrive. A challenger replaces the live model
only if it is clearly better: at least +0.05 podium drivers per race and no worse on the whole order. Every
decision is logged (`models/history.json`).

### 3.5 Validation

Each season predicted by a model trained only on earlier seasons (`data/predictions/backtests.csv`):

| Season | Races | Podium drivers right / race: model | grid | Winner right: model | grid | Places off: model | grid |
|---|---|---|---|---|---|---|---|
| 2022 | 22 | **2.18** | 1.91 | 41% | 45% | **3.65** | 3.94 |
| 2023 | 22 | 1.73 | **1.91** | 64% | 64% | **3.46** | 3.75 |
| 2024 | 24 | **2.08** | 2.00 | 50% | 46% | **2.78** | 2.90 |
| 2025 | 24 | **2.42** | 2.25 | 58% | 67% | **3.24** | 3.34 |
| 2026 (to round 21) | 21 | **1.86** | 1.81 | 76% | 71% | **3.46** | 3.64 |
| **All** | 113 | **2.06** | 1.98 | 58% | 58% | **3.31** | 3.50 |

"The grid" predicts the race finishes in starting order, a strong baseline in F1. **Calibration:** Brier
score for podium probabilities 0.0690, against 0.0698 for a grid-based baseline (podium rate by grid slot).
The Model Report Card page shows reliability diagrams and conformal finish ranges.

**Reading:** the model beats the grid on podium picks in four of five seasons and on the whole order in every
season, but the edge is small. Qualifying already carries most of the information.

### 3.6 Explanations

Because strengths are linear, each prediction decomposes exactly into feature contributions; "Why this
pick?" shows the largest, in plain words.

---

## 4. Physics engines

### 4.1 E1 Lap simulator (`src/lapsim.py`)

A **quasi-steady-state point-mass** model on the real 3D track:

- Track: x/y/z resampled every 4 m, smoothed by a spline; curvature from the spline, plus slope and banking.
- Corner speed limit: lateral grip $\mu N$ with downforce $N = mg + \tfrac12\rho C_zA v^2$ and load sensitivity
  $\mu$ falling as $N^{-\lambda}$ ($\lambda = 0.12$).
- Forward pass: power-limited and traction-limited acceleration minus drag, rolling resistance and gravity on
  slopes, using the friction circle for combined grip. Backward pass: braking limited the same way.
- Air density from altitude.
- **Calibration** per race: wing level, grip and power fitted so the simulated lap matches the real fastest
  lap and its speed trace. 89 of 90 prepared races calibrate; median gap to the real lap time 0.03%, median
  speed-trace error 14.8 km/h (the point-mass model has no gearbox, tyre temperature or driver variation, and
  public speed data is sampled at a few hertz).

**Limits:** no transient dynamics (weight transfer, yaw), no gear ratios, no tyre thermal model in the lap,
fixed aero map. Good for "what matters at this circuit" and relative changes; not for absolute setup work.

### 4.2 E2 Race engine (`src/race_engine.py`)

Lap by lap for the whole field: base pace from each car's real clean laps, tyre degradation (compound offset
and linear wear plus a cliff after a share of compound life, fitted from real stints in the tyre book), fuel
burn, pit loss measured per circuit, dirty air, overtaking chance from the pace gap, safety cars and
retirements at data-derived rates, and weather. Monte Carlo over 400–1,000 runs gives result distributions.

**Limits:** overtaking and safety-car models are rates from data, not the full ML models planned as M1/M2.

### 4.3 E3 Car DNA (`src/car_dna.py`)

The inverse of E1: fit each team's downforce, drag and power to their fastest race lap's speed trace,
per race since 2023, plus corner-speed bands, top speed and traction from telemetry.

### 4.4 E4 Energy model (`src/energy.py`)

E1 with a battery. Power = combustion engine + MGU-K while the battery has charge. Harvest under braking up to
the motor's power and a per-lap limit; deploy on chosen straights (or, since November 2026, a window on each
straight). Two lap types: **race** (energy-neutral: deployment scaled back to what the lap harvests) and
**qualifying** (full battery). Era presets: 2026 (≈400 kW ICE, 350 kW MGU-K, 8.5 MJ harvest, active aero:
drag × 0.67 on straights) and 2022–25 (≈560 kW ICE, 120 kW MGU-K, 4 MJ deploy limit, MGU-H as steady 80 kW).
Era power is scaled from each circuit's calibrated effective power. Rounded public figures; a teaching model
(no thermal limits, no "super clipping").

### 4.5 E5 Tyre model (`src/tyre_physics.py`)

Pacejka magic formula, load sensitivity, a one-node temperature model (graining below the window, blistering
above) and wear. Used in the Tyre Physics page and the Academy; real g-g diagrams from telemetry for
comparison.

---

## 5. Machine-learning and statistical models

| # | Model | Method | Validation (out of sample) |
|---|---|---|---|
| M3 | Lap one | Places gained by grid slot, side and distance to Turn 1 | Descriptive, all races since 2023 |
| M4 | Driver vs car | Driver and team-season effects fitted on finishing positions since 1950 | Uncertainty bands on every rating; finishing order only before 1996 |
| M6 | AI strategist | Cross-entropy policy search inside E2, per race | Beats the real team's stops in 93% of 88 races in simulation, beats the best fixed plan in 37%, reacts to safety cars in all |
| M7 | AI driver | Behaviour cloning of speed against track features | Tested on circuits it never saw: closer to the real speed trace than the plain simulator in 99% of 88 races (RMSE 11.9 vs 14.8 km/h); 0.83 s slower than the real lap on average |
| M8 | Who's driving? | Logistic regression on 16 driving habits relative to the team average | Held-out races: 78% of single laps, 87% of races (by majority vote) |
| M9 | Failure watch | Lap residuals against fuel- and tyre-corrected pace | 210 retirements: at the default threshold catches 51% with 6% precision (about 26 alerts a race): a weak signal, shown honestly |
| M10 | Driver market | Multinomial logistic regression (stay / move / out) on age, experience, form, teammate battle, team results; renamed teams count as the same team | Season by season since 2010 (343 seats): log loss 0.82 vs 0.94 for base rates (13% better); accuracy level with "always stays" |
| M11 | Calibration | Reliability curves, Brier score, conformal ranges | Section 3.5 |
| M12 | In-race win probability | E2 restarted from each lap's real state | Replays of every race since 2023 |
| M13 | Radio | faster-whisper transcription + keyword topic classification | Spot-checked; a test of whether radio predicts pit stops |
| M14 | Scouting | Logistic regression on feeder-series records → reaching F1 | Tested on eras it never saw: AUC ≈ 0.92, calibrated |

M1 (safety-car hazard), M2 (overtaking) and M5 (pre-1996 pace) remain simpler than planned: rates from data
in E2, and finishing-order-only ratings before 1996 (no time gaps exist in the archive before then).

---

## 6. Games and the models inside them

| Game | Model | Real vs illustrative |
|---|---|---|
| Beat the AI | Visitors' podium picks scored against the locked prediction | Real |
| Be the Race Engineer | Each car's real lap times with its tyre effect removed, plus the player's tyres and stops; calibrated so the real stops reproduce the real race time | Real data, simulated counterfactual |
| Strategy Duel | Same maths as Race Engineer, two players locking calls every five laps; two-compound rule | As above |
| Qualifying Game | Real laps of 68 sessions split into Q1–Q3 at the knockout pauses; track evolution measured per session (median of drivers' push-lap slopes, ≈ −0.02 s/min) | Laps, cut lines and evolution real; tow, traffic and mistake odds illustrative |
| Pit Crew | Player's stationary time ranked against 1,212 real stops | Real distribution |
| Energy Challenge | E4 with deploy windows; the engineer's plan from a greedy coordinate search over windows (5% steps), precomputed for 89 circuits | Teaching model |
| Fantasy Optimizer | Expected fantasy points from 20,000 Plackett–Luce race replays with each driver's retirement rate; MILP (scipy `milp`) for 5 drivers, 2 constructors and a captain within budget; prices from recent race points | Own rules and prices. Backtest 2023–26: 2.0–2.9× an average affordable random team, 60–70% of the hindsight optimum; expected points match realised (≈104 per race in 2025) |
| Prediction Market | Logarithmic market scoring rule (liquidity b = 40 shares), prior = model win chances | Play money |
| Team Principal | Rivals follow their real smoothed pace race by race; your car develops via spend × wind-tunnel allowance (70–115% by championship place) with diminishing returns; correlation risk on rushed upgrades; races drawn Plackett–Luce with retirements | Rival pace real; costs, gains and risks illustrative. With average decisions the simulated standings track the real ones |
| Career Mode | Each season a real driver-season from a comparable seat; FIA Super Licence table; M14 judges you | Real distributions |
| Race the AI Driver | E1 physics in the browser against M7 | Real lap for comparison |

Visitors' data (picks, scores, trades, duel moves) is stored in Supabase with row-level security, reached only
from the app's server with a secret key. Players are random codes in a cookie: no login, email or IP address.

---

## 7. The Engineering Academy

17 modules, 100+ chapters, each in three depths (Basics, Engineer with equations, Deep dive), with a quiz,
glossary terms, sources and links to the app's real-data pages. Live demos run on the same engines (E1, E2,
E4, E5) or on real data; anything illustrative says so on screen.

---

## 8. Historic circuits

Old layouts rebuilt from OpenStreetMap: the Nordschleife (route relation stitched into one 20.8 km loop) and
the old Hockenheim (the abandoned forest section joined to today's track by shortest paths, 6.95 km against
the real 6.825 km), with EU-DEM heights. Three era cars on E1: a 1975 car tuned to Lauda's 1975 pole average
speed, a 2001 car tuned to Montoya's 2001 Hockenheim pole, and the median calibrated 2026 car. Only grip is
fitted for the older cars; mass, power and aero are era-typical guesses.

---

## 9. Limitations (all in one place)

- **Predictor:** the edge over the grid is small; driver-market-type events (upgrades, team orders,
  incidents) are invisible to it. Wet races are hard.
- **Lap simulator:** point-mass and quasi-steady; no gearbox, transients or tyre temperature in the lap.
- **Race engine:** overtaking and safety cars are rates, not full models; the strategist pits more eagerly
  than real teams.
- **Energy model:** rounded public figures; every straight is all-or-window, no lift-and-coast harvesting.
- **Failure watch:** weak signal, many false alarms.
- **Driver market:** knows nothing about contracts, ownership or sponsorship.
- **Games:** risk and cost numbers are illustrative and say so.
- **Data:** OpenF1 starts in 2023; public telemetry is a few hertz; some sessions have gaps (one 2024 driver
  is missing from the pace data, one 2026 qualifying session couldn't be segmented).

---

## 10. Reproducing

```bash
pip install -r requirements.txt
python src/data_loader.py && python src/features.py && python src/train.py   # data, features, model
python src/pipeline.py                     # the whole robot run
python src/lapsim.py --all                 # calibrate the lap simulator on every prepared race
python src/quali_game.py                   # qualifying sessions for the Qualifying Game
python src/energy_game.py                  # the engineer's energy plans
python src/fantasy.py 2025                 # fantasy backtest for a season
python src/driver_market.py                # driver market model and its season-by-season test
python src/checks.py                       # every safety check
streamlit run app.py
```

Licences: OpenStreetMap data ODbL; Wikipedia-derived data CC BY-SA 4.0. F1 and team names are
used descriptively; the app is unofficial and not associated with Formula 1 companies.
