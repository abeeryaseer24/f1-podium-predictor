"""Career Mode data: real seasons to draw a career from, by series and team tier.

Every season of a career is drawn from what really happened to drivers in the same situation:
  F3, F2   every driver-season in the Ladder archive (GP3 and GP2 included), grouped by how good their team
           was that year: front (the teams' championship top 3), midfield (4th-7th) or back (8th and below)
  F1       every driver-season since 2014 (the hybrid era), grouped the same way by the constructors'
           championship: front (top 3), midfield (4th-6th), back (7th and below)
Each record keeps the driver's championship place as a share of the field (0 = champion, 1 = last),
points as a share of the champion's, wins, podiums, whether they beat their team-mate, and who and when,
so the game can say "a season like Oscar Piastri's in 2021".

F4 has no free results archive, so the game draws F4 seasons from the F3 pools and says so.

Saves data/ladder/career.json.
  python src/career.py
"""
import json

import numpy as np
import pandas as pd

import ladder as L

ROOT = L.ROOT
OUT = L.OUT / "career.json"


def tier_of(pos, front, mid):
    return "front" if pos <= front else "mid" if pos <= mid else "back"


def feeder_pools():
    st, teams, _ = L.load()
    st = st[st["series"].isin(["F2", "F3"])].copy()
    team_pos = teams.set_index(["series", "season", "team"])["pos"]
    champ = st[st["pos"] == 1].set_index(["series", "season"])["points"]
    field = st.groupby(["series", "season"])["pos"].transform("max")
    st["place"] = (st["pos"] - 1) / (field - 1)
    st["share"] = st["points"] / st.set_index(["series", "season"]).index.map(champ).to_numpy()
    mate = st.groupby(["series", "season", "team"])["points"].transform(
        lambda p: [max([x for j, x in enumerate(p) if j != i] or [np.nan]) for i in range(len(p))])
    st["ahead"] = (st["points"] > mate).where(mate.notna() & st["team"].notna())
    pools = {}
    for series in ("F2", "F3"):
        s = st[(st["series"] == series) & st["team"].notna() & (st["races"] >= 6)]   # full-ish seasons only
        tp = [team_pos.get((series, a, b)) for a, b in zip(s["season"], s["team"])]
        s = s.assign(team_pos=tp).dropna(subset=["team_pos"])
        s["tier"] = [tier_of(p, 3, 7) for p in s["team_pos"]]
        pools[series] = {t: [{"place": round(r.place, 3), "pos": int(r.pos), "share": round(r.share, 3),
                              "points": float(r.points), "wins": int(r.wins), "podiums": int(r.podiums),
                              "ahead": None if pd.isna(r.ahead) else bool(r.ahead), "driver": r.driver,
                              "season": int(r.season), "team": r.team, "name": r.name}
                             for r in g.itertuples()] for t, g in s.groupby("tier")}
    return pools


def f1_pool():
    drv = pd.read_csv(ROOT / "data" / "processed" / "history_drivers.csv")
    teams = pd.read_csv(ROOT / "data" / "processed" / "history_teams.csv")
    drv, teams = drv[drv["season"] >= 2014], teams[teams["season"] >= 2014]
    drv = drv[drv["position"] > 0]
    tpos = teams.set_index(["season", "constructor"])["position"]
    drv = drv.assign(team_pos=[tpos.get((a, b)) for a, b in zip(drv["season"], drv["constructor"])]).dropna(subset=["team_pos"])
    field = drv.groupby("season")["position"].transform("max")
    champ = drv[drv["position"] == 1].set_index("season")["points"]
    drv["place"] = (drv["position"] - 1) / (field - 1)
    drv["share"] = drv["points"] / drv["season"].map(champ)
    drv["tier"] = [tier_of(p, 3, 6) for p in drv["team_pos"]]
    return {t: [{"place": round(r.place, 3), "pos": int(r.position), "share": round(r.share, 3), "points": float(r.points),
                 "wins": int(r.wins), "driver": r.driver_name, "season": int(r.season), "team": r.constructor_name}
                for r in g.itertuples()] for t, g in drv.groupby("tier")}


def main():
    pools = feeder_pools()
    pools["F1"] = f1_pool()
    OUT.write_text(json.dumps(pools, ensure_ascii=False), encoding="utf-8")
    for s, p in pools.items():
        print(s, {t: len(v) for t, v in p.items()})


if __name__ == "__main__":
    main()
