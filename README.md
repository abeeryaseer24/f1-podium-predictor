# F1 Podium Predictor

Pick a Formula 1 race and this tells you which three drivers it thinks will finish on the podium.

I wanted to see how far you can get predicting F1 results from historical data alone, so I trained a model on every race from 2016 up to the 2026 Mexico City Grand Prix. Short answer: further than I expected, but the starting grid turned out to be a very tough opponent.

## How it works

For every driver in a race, the model estimates their chance of finishing in the top 3. The three highest chances are the predicted podium.

It only uses things you'd know before the lights go out:

- grid and qualifying position
- each driver's and team's long-term record (podium rate, average finish, DNF rate, past results at that circuit)
- how they're doing this season
- how many places they usually gain or lose on race day

Every stat is built only from races *before* the one being predicted, so the model never gets a peek at the result it's guessing.

## Results

To keep things honest I split the data by time: trained on 2016-2022, compared models on 2023-2024, and only touched 2025 once, at the very end.

The score I care about is simple: **in an average race, how many of the 3 predicted drivers actually made the podium?**

| Model | 2023-2024 | 2025 |
|---|---|---|
| Grid baseline (first 3 on the grid) | 1.96 | 2.25 |
| Logistic Regression | 1.80 | 1.83 |
| XGBoost | 1.89 | 2.21 |
| **Random Forest (final model)** | 1.93 | **2.29** |

The baseline is brutal. Just picking the front three on the grid gets about 2 of 3 right before any machine learning happens. My final model scored **2.29 on 2025**, a season it had never seen, against 2.25 for the grid (ROC-AUC 0.949). That's a small edge, and over ~24 races a gap like that could easily be noise, so I'd call it "matches the grid, maybe slightly better" rather than a big win.

The real lesson: qualifying already tells you most of what matters on Sunday.

## What the model pays attention to

![Feature importance](reports/figures/feature_importance.png)

Grid and qualifying position dominate, followed by current-season form. Ten years of history helped less than I thought it would, which makes sense in 2026, when new regulations reshuffled the order.

![Podium rate by grid position](reports/figures/podium_by_grid.png)

## Try it yourself

```bash
git clone https://github.com/abeeryaseer24/f1-podium-predictor.git
cd f1-podium-predictor
python -m venv .venv
source .venv/Scripts/activate      # on Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Rebuild everything from scratch (downloads the data, builds features, trains the model):

```bash
python src/data_loader.py
python src/features.py
python src/train.py
```

The saved model is trained on every race up to 2026 round 19.

**Predict a past race** and compare with what actually happened:

```bash
python src/predict.py --season 2025 --round 1
```

**Predict an upcoming race:**

```bash
python src/predict_next.py --season 2026 --round 20
```

If qualifying has happened, it uses the real grid. If not, it estimates the grid from each driver's average qualifying this season, which is rougher. Run it after Saturday for the version worth trusting.

## Project structure

```
data/processed/    cleaned race data and features
notebooks/         exploration and model comparison
src/
  data_loader.py   downloads results from the Jolpica-F1 API
  features.py      builds the pre-race features
  train.py         trains, tests and saves the final model
  predict.py       predicts a past race
  predict_next.py  predicts an upcoming race
models/            the saved model
reports/figures/   charts
```

## Limitations

- F1 is chaotic. Safety cars, first-lap crashes and strategy calls can't be predicted from history.
- Each driver's podium chance is estimated separately, so the chances don't add up to exactly 3 drivers.
- Qualifying order isn't always the final grid, because penalties get applied afterwards.
- No weather, tyre or lap-time data yet.

## What's next

- A small web app so anyone can pick a race and see the prediction
- Weather and practice-session pace from FastF1
- A model that predicts the full finishing order, not just the podium

## Data

Race and qualifying results come from the [Jolpica-F1 API](https://github.com/jolpica/jolpica-f1), the community successor to the Ergast API.

---

Built by Talha Yaseer Abeer ([@abeeryaseer24](https://github.com/abeeryaseer24))