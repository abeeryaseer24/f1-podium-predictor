"""AI Strategist: a reinforcement-learning agent that learns pit strategy by racing thousands of times.

THE ENVIRONMENT is one real race, rebuilt from its own data by race_engine.build(): fuel effect, each dry
compound's speed and wear (with the cliff), pit loss, and the circuit's safety-car rate. Safety cars
arrive at random, and a stop under a safety car costs 55 % of a normal one. The car runs alone (no
traffic), so the agent learns pure strategy.

THE AGENT'S POLICY is a small set of numbers:
    how many stops · the target lap for each stop · the tyre for each stint ·
    a safety-car window: if a safety car comes out within this many laps before a planned stop, box now
Its reward is minus the race time (and a big penalty for breaking the two-compound rule).

LEARNING is policy search with the cross-entropy method, a classic reinforcement-learning algorithm:
each generation it tries a population of policies on a batch of simulated races, keeps the best tenth,
and moves its beliefs towards them, until it converges. It is never told the tyre equations, only how
each race turned out. The learning curve shows its average race time improving generation by generation.
(A tabular Q-learning agent was tried first; with this many situations it learned too slowly to be useful.)

IT IS COMPARED, on the same 400 random races, with
  the real winner's stops replayed, and
  the best fixed plan found by searching every one- and two-stop combination (no safety-car reaction).

Writes data/processed/rl/<race>.json.

Usage:
  python src/rl_strategist.py 2025 12            train one race
  python src/rl_strategist.py --missing --limit 2   races not trained yet, newest first
"""
import itertools
import json
import sys
import time

import numpy as np

import race_engine as RE
from strategy import SC_FACTOR

OUT = RE.RACES_DIR.parent / "processed" / "rl"
DRY = ["SOFT", "MEDIUM", "HARD"]
SC_LAPS = 4
GENERATIONS, POPULATION, BATCH, ELITE = 25, 80, 60, 0.1


class Env:
    def __init__(self, race):
        self.race = race
        self.L = race["laps"]
        self.comps = [c for c in DRY if c in race["compounds"]] or ["MEDIUM"]
        self.winner = next((d for d, p in race["real_pos"].items() if p == 1), race["drivers"][0])
        self.hazard = race["sc_rate"] / max(self.L, 1)
        self.loss = race["pit_loss"]
        tyre = np.array([[RE.tyre_cost(race["compounds"], c, a) for a in range(self.L + 2)] for c in self.comps])
        self.cum = np.concatenate([np.zeros((len(self.comps), 1)), np.cumsum(tyre, axis=1)], axis=1)  # cost of an n-lap stint

    def races(self, n, rng):
        """n random races: a boolean safety-car table (races x laps)."""
        sc = np.zeros((n, self.L + 2), dtype=bool)
        for r in range(n):
            lap = 2
            while lap < self.L - 2:
                if rng.random() < self.hazard:
                    sc[r, lap:lap + SC_LAPS] = True
                    lap += SC_LAPS + 3
                lap += 1
        return sc

    def cost(self, stops, comps, window, sc):
        """Race time (tyres + stops) of one policy on every race in sc, vectorised. stops are target laps."""
        n = sc.shape[0]
        actual = []
        prev = np.zeros(n, dtype=int)
        for target in stops:
            lap = np.full(n, int(target))
            if window > 0:                                       # react to a safety car shortly before the planned stop
                for w in range(int(window), 0, -1):
                    early = int(np.clip(int(target) - w, 1, self.L - 1))
                    hit = sc[:, early] & (lap == int(target)) & (early > prev)
                    lap = np.where(hit, early, lap)
            lap = np.maximum(lap, prev + 2)
            actual.append(lap)
            prev = lap
        total = np.zeros(n)
        start = np.zeros(n, dtype=int)
        for k, c in enumerate(comps):
            end = actual[k] if k < len(actual) else np.full(n, self.L)
            total += self.cum[c, np.clip(end - start, 0, self.L)]
            if k < len(actual):
                total += self.loss * np.where(sc[np.arange(n), np.clip(end, 0, self.L)], SC_FACTOR["SC"], 1.0)
            start = end
        if len(set(comps)) < 2:
            total += 60.0
        return total, actual


def learn(env, seed=0):
    """Cross-entropy policy search for every stop count and tyre order. Returns the best policy and its learning curve."""
    rng = np.random.default_rng(seed)
    nc = len(env.comps)
    best, curve = None, []
    for n_stops in (1, 2):
        for comps in itertools.product(range(nc), repeat=n_stops + 1):
            if len(set(comps)) < 2:
                continue
            mu = np.array([env.L * (k + 1) / (n_stops + 1) for k in range(n_stops)] + [3.0])
            sd = np.array([env.L / 4] * n_stops + [3.0])
            history = []
            for g in range(GENERATIONS):
                pop = rng.normal(mu, sd, (POPULATION, n_stops + 1))
                pop[:, :n_stops] = np.sort(np.clip(pop[:, :n_stops], 3, env.L - 3), axis=1)
                pop[:, -1] = np.clip(pop[:, -1], 0, 10)
                sc = env.races(BATCH, rng)
                scores = np.array([env.cost(p[:n_stops].round(), comps, round(p[-1]), sc)[0].mean() for p in pop])
                elite = pop[np.argsort(scores)[: max(2, int(POPULATION * ELITE))]]
                mu, sd = elite.mean(axis=0), elite.std(axis=0) + 0.3
                history.append(float(np.sort(scores)[: len(elite)].mean()))
            policy = {"stops": [int(round(x)) for x in mu[:n_stops]], "comps": list(comps), "window": int(round(mu[-1]))}
            check = env.cost(policy["stops"], policy["comps"], policy["window"], env.races(200, rng))[0].mean()
            if best is None or check < best[1]:
                best, curve = (policy, check), history
    return best[0], curve


def best_fixed(env, sc):
    nc = len(env.comps)
    best, best_t = None, np.inf
    for k in range(4, env.L - 3):
        for c in itertools.product(range(nc), repeat=2):
            t = env.cost([k], c, 0, sc)[0].mean()
            if t < best_t:
                best, best_t = ([k], list(c)), t
    for k1 in range(4, env.L - 8, 2):
        for k2 in range(k1 + 5, env.L - 3, 2):
            for c in itertools.product(range(nc), repeat=3):
                t = env.cost([k1, k2], c, 0, sc)[0].mean()
                if t < best_t:
                    best, best_t = ([k1, k2], list(c)), t
    return best


def run(folder, seed=0):
    race = RE.build(folder)
    env = Env(race)
    t0 = time.time()
    policy, curve = learn(env, seed)
    train_s = time.time() - t0
    rng = np.random.default_rng(seed + 99)
    sc = env.races(400, rng)
    rl_t, rl_stops = env.cost(policy["stops"], policy["comps"], policy["window"], sc)
    real = race["strategies"][env.winner]
    real_comps = [env.comps.index(c) if c in env.comps else 0 for c, _ in real]
    real_t, _ = env.cost([end for _, end in real[:-1]], real_comps, 0, sc)
    fixed = best_fixed(env, env.races(80, np.random.default_rng(seed + 5)))
    fix_t, _ = env.cost(fixed[0], fixed[1], 0, sc)
    reacted = float(np.mean([any(rl_stops[k][r] != policy["stops"][k] for k in range(len(policy["stops"])))
                             for r in range(sc.shape[0])])) if policy["stops"] else 0.0
    out = {
        "race": f"{race['info']['race_name']} {race['info']['season']}", "laps": env.L, "compounds": env.comps,
        "winner": race["who"][env.winner].get("code", ""),
        "policy": {"stops": policy["stops"], "tyres": [env.comps[c] for c in policy["comps"]], "window": policy["window"]},
        "real_plan": [[end, c] for c, end in real], "best_fixed": {"stops": fixed[0], "tyres": [env.comps[c] for c in fixed[1]]},
        "rl_mean": float(rl_t.mean()), "real_mean": float(real_t.mean()), "fixed_mean": float(fix_t.mean()),
        "rl_beats_real": float((rl_t < real_t - 1e-6).mean()), "rl_beats_fixed": float((rl_t < fix_t - 1e-6).mean()),
        "reacted_to_sc": reacted, "curve": curve, "sc_rate": race["sc_rate"], "pit_loss": race["pit_loss"],
        "train_seconds": round(train_s, 1), "races_tried": GENERATIONS * POPULATION * BATCH,
        "gains": {"vs_real": (real_t - rl_t).round(2).tolist(), "vs_fixed": (fix_t - rl_t).round(2).tolist()},
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{folder}.json").write_text(json.dumps(out))
    return out


def trained():
    return sorted(p.stem for p in OUT.glob("*.json")) if OUT.exists() else []


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--missing":
        limit = int(args[args.index("--limit") + 1]) if "--limit" in args else 0
        done = set(trained())
        todo = [p.name for p in sorted(RE.RACES_DIR.glob("*_*"), reverse=True)
                if (p / "laps.parquet").exists() and p.name not in done]
        todo = todo[:limit] if limit else todo
    elif len(args) == 2:
        todo = [f"{int(args[0])}_{int(args[1]):02d}"]
    else:
        print(__doc__)
        todo = []
    for folder in todo:
        try:
            o = run(folder)
        except Exception as error:             # a race the engine can't rebuild: skip it
            print(f"{folder}: skipped ({error})")
            continue
        print(f"{folder} {o['race']}: AI {o['rl_mean'] - o['fixed_mean']:+.1f}s vs best fixed plan, "
              f"{o['rl_mean'] - o['real_mean']:+.1f}s vs the winner's real stops (beats it in {o['rl_beats_real']:.0%}); "
              f"policy {o['policy']}; reacted to a safety car in {o['reacted_to_sc']:.0%}; {o['train_seconds']}s")
