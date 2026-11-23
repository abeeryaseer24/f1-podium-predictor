"""Scouting (M14): which feeder-series records turned into Formula 1 careers, and who looks next.

THE RECORD. For every driver in the Ladder archive (F2/GP2 since 2005, F3/GP3 since 2010; F1 Academy is
left out because no driver from it has reached F1 yet, so there is nothing to learn from):
  f3_best, f2_best         best championship place in each (40 = never raced there)
  f2_rookie                championship place in the first F2/GP2 season
  f3_share, f2_share       best season's points as a share of that season's champion
  f2_wins, f2_podiums      across every F2/GP2 season
  beat_teammate            share of seasons (F2 and F3) with more points than their team-mate(s)
  sl_peak                  the best three-season Super Licence total, with today's table
Left out on purpose: how many seasons a driver spent in each series. Drivers often leave F2 because they
got an F1 seat, so the count partly gives the answer away, and a current driver's count is still growing.

THE OUTCOMES, from our F1 archive (names matched by ladder.name_key):
  reached       started a Grand Prix within four seasons after their last feeder season
  established   started 50 or more Grands Prix

THE MODEL. Logistic regression on the standardised record (scikit-learn), one for each outcome. Only
careers that have had time to play out are used to train it (last feeder season at least four years ago
for "reached", eight for "established"). It is tested by leaving out whole groups of first seasons at a
time, so it never sees a driver's own era-mates while being scored on them. Scores: the area under the ROC
curve (how well it ranks: 0.5 is guessing, 1 is perfect) and the Brier score.

Saves data/ladder/scouting.json (with the fitted model, so Career Mode can score a made-up record).
  python src/scouting.py
"""
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

import ladder as L

OUT = L.OUT / "scouting.json"
FEATURES = {
    "f3_best": "Best F3/GP3 championship place",
    "f2_best": "Best F2/GP2 championship place",
    "f2_rookie": "F2/GP2 place as a rookie",
    "f3_share": "Best F3 season, share of the champion's points",
    "f2_share": "Best F2 season, share of the champion's points",
    "f2_wins": "F2/GP2 race wins",
    "f2_podiums": "F2/GP2 podiums",
    "beat_teammate": "Share of seasons ahead of their team-mate",
    "sl_peak": "Best three-season Super Licence total",
}
NONE = 40           # the place given to a series a driver never raced in
REACH_WINDOW = 4
ESTABLISHED = 50


def records():
    st, _, sl = L.load()
    st = st[st["series"].isin(["F2", "F3"])].copy()
    champ = st[st["pos"] == 1].set_index(["series", "season"])["points"]
    st["share"] = st["points"] / st.set_index(["series", "season"]).index.map(champ).to_numpy()
    st["sl"] = [L.sl_points(sl, s, p) for s, p in zip(st["series"], st["pos"])]
    # team-mates: same series, season and team
    st["mate_best"] = st.groupby(["series", "season", "team"])["points"].transform(
        lambda p: [max([x for j, x in enumerate(p) if j != i] or [np.nan]) for i in range(len(p))])
    st.loc[st["team"].isna() | (st["team"] == ""), "mate_best"] = np.nan
    st["ahead"] = (st["points"] > st["mate_best"]).where(st["mate_best"].notna())
    rows = []
    for key, g in st.groupby("key"):
        f2, f3 = g[g["series"] == "F2"].sort_values("season"), g[g["series"] == "F3"].sort_values("season")
        by_season = g.groupby("season")["sl"].max()
        seasons = range(int(g["season"].min()), int(g["season"].max()) + 1)
        sl_peak = max(sum(by_season.get(y, 0) for y in (s - 2, s - 1, s)) for s in seasons)
        first = int(g["season"].min())
        rows.append({
            "key": key, "driver": g.sort_values("season")["driver"].iloc[-1],
            "first": first, "last": int(g["season"].max()),
            "f3_best": int(f3["pos"].min()) if len(f3) else NONE, "f2_best": int(f2["pos"].min()) if len(f2) else NONE,
            "f2_rookie": int(f2["pos"].iloc[0]) if len(f2) else NONE,
            "f3_share": float(f3["share"].max()) if len(f3) else 0.0, "f2_share": float(f2["share"].max()) if len(f2) else 0.0,
            "f2_wins": int(f2["wins"].sum()), "f2_podiums": int(f2["podiums"].sum()),
            "f2_seasons": len(f2), "f3_seasons": len(f3),
            "beat_teammate": float(g["ahead"].dropna().mean()) if g["ahead"].notna().any() else 0.5,
            "sl_peak": float(sl_peak),
            "young": int(len(f2) > 0 and int(f2["season"].min()) - first <= 1),
            "path": " · ".join(f"{r.season} {r['name']} P{r.pos}" for _, r in g.sort_values(["season", "series"]).iterrows()),
        })
    df = pd.DataFrame(rows).set_index("key")
    f1 = L.f1_careers()
    df = df.join(f1)
    # drivers who were already in F1 before their feeder career began don't belong in this question
    df = df[~(df["first_f1"] < df["first"])]
    df["reached"] = (df["first_f1"].notna() & (df["first_f1"] <= df["last"] + REACH_WINDOW)).astype(int)
    df["established"] = (df["starts"].fillna(0) >= ESTABLISHED).astype(int)
    return df


def fit(X, y):
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    return make_pipeline(StandardScaler(), LogisticRegression(C=0.5, max_iter=2000)).fit(X, y)


def cross_validate(df, outcome, groups=5):
    """Leave out groups of first seasons; returns out-of-fold probabilities, AUC and Brier score."""
    from sklearn.metrics import brier_score_loss, roc_auc_score
    years = np.array(sorted(df["first"].unique()))
    folds = np.array_split(years, groups)
    p = pd.Series(np.nan, index=df.index)
    X, y = df[list(FEATURES)], df[outcome]
    for test in folds:
        tr = ~df["first"].isin(test)
        if y[tr].nunique() < 2:
            continue
        p[~tr] = fit(X[tr], y[tr]).predict_proba(X[~tr])[:, 1]
    ok = p.notna()
    return p, float(roc_auc_score(y[ok], p[ok])), float(brier_score_loss(y[ok], p[ok])), float(y[ok].mean())


def chance(model, record):
    """P(reaching F1) for one record (a dict of FEATURES), from the saved model."""
    z = sum(model["coef"][f] * (record[f] - model["mean"][f]) / model["scale"][f] for f in model["coef"])
    return 1 / (1 + np.exp(-(z + model["intercept"])))


def main():
    df = records()
    last = int(df["last"].max())
    reach_train = df[df["last"] <= last - REACH_WINDOW]
    est_train = df[(df["last"] <= last - 8) & (df["reached"] == 1)]
    p_reach, auc_r, brier_r, base_r = cross_validate(reach_train, "reached")
    p_est, auc_e, brier_e, base_e = cross_validate(est_train, "established")
    m_reach = fit(reach_train[list(FEATURES)], reach_train["reached"])
    m_est = fit(est_train[list(FEATURES)], est_train["established"])

    df["p_reach"] = m_reach.predict_proba(df[list(FEATURES)])[:, 1]
    df["p_est"] = m_est.predict_proba(df[list(FEATURES)])[:, 1]
    df.loc[reach_train.index, "p_reach_cv"] = p_reach
    coef = dict(zip(FEATURES, m_reach[-1].coef_[0]))

    # who looks next: raced in the last two seasons, no Grand Prix start yet
    candidates = df[(df["last"] >= last - 1) & df["starts"].isna()].sort_values("p_reach", ascending=False)

    # nearest past drivers (standardised record) for every candidate
    from sklearn.preprocessing import StandardScaler
    past = reach_train
    sc = StandardScaler().fit(past[list(FEATURES)])
    P = sc.transform(past[list(FEATURES)])

    def similar(row, k=3):
        d = np.linalg.norm(P - sc.transform(row[list(FEATURES)].to_frame().T), axis=1)
        out = []
        for i in np.argsort(d)[:k]:
            r = past.iloc[i]
            out.append({"driver": r["driver"], "path": r["path"], "reached": int(r["reached"]),
                        "starts": int(r["starts"]) if pd.notna(r["starts"]) else 0})
        return out

    def row_out(key, r, extra=None):
        d = {"key": key, "driver": r["driver"], "path": r["path"], "first": int(r["first"]), "last": int(r["last"]),
             "p_reach": round(float(r["p_reach"]), 3), "p_est": round(float(r["p_est"]), 3),
             **{f: (round(float(r[f]), 3) if isinstance(r[f], float) else int(r[f])) for f in FEATURES}}
        return {**d, **(extra or {})}

    history = []
    for key, r in df.loc[reach_train.index].iterrows():
        history.append(row_out(key, r, {"reached": int(r["reached"]), "starts": int(r["starts"]) if pd.notna(r["starts"]) else 0,
                                         "wins": int(r["f1_wins"]) if pd.notna(r["f1_wins"]) else 0,
                                         "p_cv": round(float(r["p_reach_cv"]), 3) if pd.notna(r["p_reach_cv"]) else None}))
    payload = {
        "features": FEATURES, "built": time.strftime("%Y-%m-%d"), "last": last,
        "reach": {"auc": round(auc_r, 3), "brier": round(brier_r, 3), "base": round(base_r, 3), "drivers": int(len(reach_train)),
                  "window": REACH_WINDOW},
        "established": {"auc": round(auc_e, 3), "brier": round(brier_e, 3), "base": round(base_e, 3),
                        "drivers": int(len(est_train)), "starts": ESTABLISHED},
        "weights": {f: round(float(v), 3) for f, v in sorted(coef.items(), key=lambda kv: -abs(kv[1]))},
        # the fitted model itself, so other pages (Career Mode) can score a record of their own
        "model": {"mean": dict(zip(FEATURES, m_reach[0].mean_.round(5).tolist())),
                  "scale": dict(zip(FEATURES, m_reach[0].scale_.round(5).tolist())),
                  "coef": dict(zip(FEATURES, m_reach[-1].coef_[0].round(5).tolist())),
                  "intercept": round(float(m_reach[-1].intercept_[0]), 5)},
        "candidates": [row_out(k, r, {"similar": similar(r)}) for k, r in candidates.head(40).iterrows()],
        "history": history,
    }
    OUT.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Reach F1: AUC {auc_r:.2f}, Brier {brier_r:.3f} (base rate {base_r:.0%}) on {len(reach_train)} drivers")
    print(f"Established (50+ starts) among those who reached F1: AUC {auc_e:.2f} on {len(est_train)} drivers")
    print("Top candidates:", ", ".join(f"{c['driver']} {c['p_reach']:.0%}" for c in payload["candidates"][:8]))


if __name__ == "__main__":
    main()
