"""Energy Challenge: the game half of the Energy Lab, with a leaderboard for every circuit.

The car is a 2026 car (active aero on) on a circuit's calibrated chassis. For each straight the player
sets a deploy window: from where to where on the straight the electric motor helps. Everything outside
the windows is engine only. The lap is run on energy.py, so emptying the battery early (clipping) or,
in a race lap, spending more than the lap harvests, costs time.

Two laps:
  qualifying  start with a full battery and use it all
  race        the lap pays for itself: you can only spend what the braking zones put back

Targets: "deploy everywhere" (the simple plan) and the engineer's plan, found by a search over the
windows (par()): start from the best of a few even plans, then move each window's ends one at a time,
keeping every change that makes the lap faster. Medals: bronze for beating deploy everywhere, silver
within 0.10 s of the engineer, gold for matching or beating the engineer.

Leaderboard: each player's best lap per circuit and lap type, in the Supabase table `energy_scores`
(same server-side key as Beat the AI). Laps are always recomputed on the server from the plan, never
taken from the browser. Without a database they are kept in data/energy_scores_local.json.

    create table energy_scores (player text not null, folder text not null, mode text not null,
      lap_time double precision not null, plan jsonb not null, nickname text, updated_at timestamptz,
      primary key (player, folder, mode));
    alter table energy_scores enable row level security;

Precompute the engineer's plans for every calibrated circuit (skips ones already done):
    python src/energy_game.py
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import energy as E
import lapsim
import picks

ROOT = Path(__file__).resolve().parent.parent
PAR_FILE = ROOT / "data" / "processed" / "energy_par.json"
LOCAL_FILE = ROOT / "data" / "energy_scores_local.json"
TABLE = "energy_scores"
ERA = "2026 rules"
MODES = ("qualifying", "race")
STEP = 0.05                      # windows move in 5% steps of the straight
SILVER = 0.10                    # s off the engineer for silver


def setup(folder, track=None):
    car, pu = E.car_for(folder, ERA)
    if track is None:
        import pandas as pd
        track = lapsim.build_track(pd.read_parquet(lapsim.RACES_DIR / folder / "track.parquet"))
    return car, track, pu


def lap(car, track, pu, plan, mode):
    """plan = one (from, to) window per straight, as fractions; None = deploy everywhere."""
    return E.simulate(car, track, pu, deploy_on=None if plan is None else [tuple(w) for w in plan], mode=mode)


def snap(x):
    return round(min(1.0, max(0.0, round(x / STEP) * STEP)), 2)


def par(car, track, pu, mode, passes=3):
    """The engineer's plan: (lap time, windows). A greedy search, so good but not provably the best."""
    n = len(E.straights(car, track))
    t = lambda p: lap(car, track, pu, p, mode)["lap_time"]
    starts = [[(0.0, b)] * n for b in (1.0, 0.75, 0.5, 0.3)]
    best_plan = min(starts, key=t)
    best = t(best_plan)
    for _ in range(passes):
        improved = False
        for k in range(n):
            for end in (0, 1):
                for move in (-0.2, 0.2, -0.1, 0.1, -0.05, 0.05):
                    w = list(best_plan[k])
                    w[end] = snap(w[end] + move)
                    if w[0] >= w[1] and not (w[0] == w[1] == 0.0):
                        continue
                    trial = best_plan[:k] + [tuple(w)] + best_plan[k + 1:]
                    tt = t(trial)
                    if tt < best - 1e-4:
                        best_plan, best, improved = trial, tt, True
        if not improved:
            break
    return round(best, 3), [list(w) for w in best_plan]


def load_par():
    return json.loads(PAR_FILE.read_text(encoding="utf-8")) if PAR_FILE.exists() else {}


def medal(time, everywhere, engineer):
    if engineer is not None and time <= engineer + 5e-4:
        return "gold"
    if engineer is not None and time <= engineer + SILVER:
        return "silver"
    if time < everywhere - 5e-4:
        return "bronze"
    return None


# ---------- the leaderboard ----------

def _read_local():
    return json.loads(LOCAL_FILE.read_text()) if LOCAL_FILE.exists() else []


def scores(folder, mode):
    """Every player's best lap on this circuit, quickest first."""
    conf = picks._supabase()
    if conf:
        import requests
        url, key = conf
        r = requests.get(f"{url}/rest/v1/{TABLE}", params={"folder": f"eq.{folder}", "mode": f"eq.{mode}",
                                                           "select": "*", "order": "lap_time.asc", "limit": 50},
                         headers=picks._headers(key), timeout=15)
        r.raise_for_status()
        return r.json()
    rows = [r for r in _read_local() if r["folder"] == folder and r["mode"] == mode]
    return sorted(rows, key=lambda r: r["lap_time"])


def save_score(player, folder, mode, lap_time, plan, nickname=""):
    """Keep the player's lap if it beats their best here. Returns True if it was saved."""
    mine = [r for r in scores(folder, mode) if r["player"] == player]
    if mine and mine[0]["lap_time"] <= lap_time + 1e-6:
        return False
    row = {"player": player, "folder": folder, "mode": mode, "lap_time": round(float(lap_time), 3),
           "plan": [list(map(float, w)) for w in plan], "nickname": (nickname or "").strip()[:20] or None,
           "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    conf = picks._supabase()
    if conf:
        import requests
        url, key = conf
        r = requests.post(f"{url}/rest/v1/{TABLE}?on_conflict=player,folder,mode", json=row,
                          headers={**picks._headers(key), "Prefer": "resolution=merge-duplicates,return=minimal"},
                          timeout=15)
        r.raise_for_status()
        return True
    rows = [r for r in _read_local() if not (r["player"] == player and r["folder"] == folder and r["mode"] == mode)]
    LOCAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOCAL_FILE.write_text(json.dumps(rows + [row], indent=1))
    return True


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    done = load_par()
    cal = lapsim.load_calibration()
    folders = sorted(f for f, c in cal.items() if c.get("usable"))
    for f in folders:
        if f in done:
            continue
        try:
            car, track, pu = setup(f)
            entry = {"everywhere": {}, "engineer": {}}
            for mode in MODES:
                entry["everywhere"][mode] = round(lap(car, track, pu, None, mode)["lap_time"], 3)
                t, plan = par(car, track, pu, mode)
                entry["engineer"][mode] = {"time": t, "plan": plan}
            done[f] = entry
            print(f"{f}: quali {entry['everywhere']['qualifying']:.3f} -> {entry['engineer']['qualifying']['time']:.3f}, "
                  f"race {entry['everywhere']['race']:.3f} -> {entry['engineer']['race']['time']:.3f}", flush=True)
        except Exception as error:
            print(f"{f}: failed ({error})", flush=True)
        PAR_FILE.write_text(json.dumps(dict(sorted(done.items()))), encoding="utf-8")


if __name__ == "__main__":
    main()
