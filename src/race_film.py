"""Race Films: the story of a race, written automatically from its data, scene by scene.

Every scene comes from facts in the race files (OpenF1 laps, pit stops and race control) and the
Where-the-Race-Was-Won breakdown, never from guesswork:
  the start       pole sitter, leader after lap 1, the biggest lap-one gains and losses
  lead changes    every lap the leader changed, and whether it happened in the pits
  safety cars     each safety-car or VSC period, and who pitted under it
  the stops       when the eventual podium finishers made their stops
  the climber     the biggest gain from grid to flag
  the finish      winner, margin, and which part of the race decided it
Sentences come from small sets of templates, so two races don't read the same. The browser reads the
film aloud with its own free speech engine.
"""
import random

import pandas as pd

import race_story as R

BUCKET_WORDS = {"Start (lap 1)": "the start", "Pit stops": "the pit stops", "Safety car laps": "the safety-car laps",
                "Racing laps": "pure pace"}


def ordinal(n):
    n = int(n)
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def _name(who, n):
    d = who.get(int(n), {})
    return str(d.get("name", d.get("code", n))).title()


def _code(who, n):
    return who.get(int(n), {}).get("code", str(n))


def standings(laps, lap, who, top=5):
    d = laps[laps["lap_number"] == lap].dropna(subset=["position"]).sort_values("position").head(top)
    return [{"code": _code(who, r.driver_number), "colour": who.get(int(r.driver_number), {}).get("colour") or "#8a8a96",
             "pos": int(r.position)} for r in d.itertuples()]


def film(folder, seed=0):
    rng = random.Random(seed or hash(folder) % 10_000)
    pick = rng.choice
    laps, pits, control, info = R.load(folder)
    who = R.drivers(info)
    results = pd.read_csv(R.RESULTS_CSV)
    grid = R.grid_for(info, results)
    order = R.finishing_order(laps)
    n_laps = int(laps["lap_number"].max())
    scenes = []

    def add(lap, title, text, kind):
        scenes.append({"lap": int(lap), "title": title, "text": text, "kind": kind, "top": standings(laps, max(lap, 1), who)})

    # --- the start ---
    pole = min(grid, key=grid.get) if grid else order[0]
    l1 = laps[laps["lap_number"] == 1].dropna(subset=["position"]).sort_values("position")
    leader1 = int(l1.iloc[0]["driver_number"]) if len(l1) else pole
    one = R.lap_one(folder, results)
    text = (pick([f"{_name(who, pole)} started from pole at the {info['race_name']}.",
                  f"The {info['race_name']} began with {_name(who, pole)} on pole."]) + " " +
            (pick([f"{_name(who, leader1)} led them through the first lap.", f"After one lap it was {_name(who, leader1)} in front."])
             if leader1 != pole else pick([f"{_name(who, pole)} kept the lead into the first corner.",
                                           f"{_name(who, pole)} converted pole into the lead."])))
    if len(one):
        g, lo = one.sort_values("gained").iloc[-1], one.sort_values("gained").iloc[0]
        if g["gained"] >= 3:
            text += " " + pick([f"{str(g['name']).title()} made a flying start, up {int(g['gained'])} places.",
                                f"The start of the day belonged to {str(g['name']).title()}, who gained {int(g['gained'])} places."])
        if lo["gained"] <= -3:
            text += " " + pick([f"{str(lo['name']).title()} lost {abs(int(lo['gained']))} places on the opening lap.",
                                f"It was a difficult start for {str(lo['name']).title()}, down {abs(int(lo['gained']))}."])
    add(1, "Lights out", text, "start")

    # --- safety cars ---
    neutral = sorted(R.neutral_laps(laps, control))
    periods, cur = [], []
    for lap in neutral:
        if cur and lap != cur[-1] + 1:
            periods.append(cur)
            cur = []
        cur.append(lap)
    if cur:
        periods.append(cur)
    stops = R.pit_laps(laps)
    for p in periods:
        if p[0] <= 1 or p[0] >= n_laps:
            continue
        msgs = control[(control["lap_number"] >= p[0]) & (control["lap_number"] <= p[-1])]["message"].fillna("").str.upper()
        kind = "virtual safety car" if msgs.str.contains("VIRTUAL|VSC").any() else (
            "red flag" if msgs.str.contains(r"RED FLAG", regex=True).any() else "safety car")
        pitted = sorted({_code(who, d) for d, s in stops.items() if any(l in s for l in p)})
        text = pick([f"On lap {p[0]} the {kind} came out.", f"Lap {p[0]}: {kind.capitalize()}."]) + " "
        text += (pick([f"{', '.join(pitted[:5])} dived into the pits for a cheaper stop.",
                       f"That was the signal for {', '.join(pitted[:5])} to pit."]) if pitted
                 else pick(["Nobody took the chance to pit.", "The field stayed out."]))
        add(p[0], kind.capitalize(), text, "sc")

    # --- lead changes ---
    leaders = laps.dropna(subset=["position"])
    leaders = leaders[leaders["position"] == 1].sort_values("lap_number")[["lap_number", "driver_number"]]
    prev = None
    changes = 0
    for lap, num in leaders.itertuples(index=False):
        if prev is not None and num != prev and lap > 1:
            in_pits = lap in stops.get(int(prev), set()) or (lap - 1) in stops.get(int(prev), set())
            if changes < 6:
                add(lap, "New leader", pick([f"Lap {lap}: {_name(who, num)} takes the lead"
                                             + (" as " + _name(who, prev) + " pits." if in_pits else " from " + _name(who, prev) + "."),
                                             f"{_name(who, num)} moves to the front on lap {lap}"
                                             + (", with " + _name(who, prev) + " in the pit lane." if in_pits else ".")]), "lead")
            changes += 1
        prev = num

    # --- the podium's stops ---
    podium = order[:3]
    parts = []
    for n in podium:
        s = sorted(lap for lap in stops.get(int(n), set()) if lap > 1)
        firsts = [l for k, l in enumerate(s) if k == 0 or l - s[k - 1] > 1]
        if firsts:
            parts.append(f"{_code(who, n)} on lap{'s' if len(firsts) > 1 else ''} {', '.join(map(str, firsts))}")
    if parts:
        mid = min(min((l for l in stops.get(int(n), set()) if l > 1), default=n_laps // 2) for n in podium)
        add(mid, "The stops", pick(["The podium finishers came in: ", "Strategy: "]) + "; ".join(parts) + ".", "pit")

    # --- the climber ---
    finish_pos = {n: k + 1 for k, n in enumerate(order)}
    gains = {n: grid[n] - finish_pos[n] for n in finish_pos if n in grid}
    if gains:
        best = max(gains, key=gains.get)
        if gains[best] >= 4:
            add(int(n_laps * 0.75), "The climb", pick([f"{_name(who, best)} came from {ordinal(grid[best])} on the grid to finish {ordinal(finish_pos[best])}.",
                                                       f"Drive of the day material: {_name(who, best)}, from P{grid[best]} to P{finish_pos[best]}."]), "climb")

    # --- the finish ---
    winner, field = R.field_breakdown(folder)
    text = pick([f"{_name(who, winner)} wins the {info['race_name']}!", f"Chequered flag: victory for {_name(who, winner)}."])
    if len(field):
        second = field.iloc[0]
        parts = {k: -second[k] for k in R.BUCKETS}
        decisive = max(parts, key=lambda k: abs(parts[k]))
        text += " " + pick([f"{_name(who, second['driver_number'])} was second, {abs(second['total']):.1f} seconds behind.",
                            f"The gap to {_name(who, second['driver_number'])} in second: {abs(second['total']):.1f} seconds."])
        text += " " + pick([f"The race was decided by {BUCKET_WORDS[decisive]}.",
                            f"Where was it won? Mostly in {BUCKET_WORDS[decisive]}."])
    if len(order) > 2:
        text += f" {_name(who, order[2])} completed the podium."
    add(n_laps, "The finish", text, "finish")

    scenes.sort(key=lambda s: (s["lap"], s["kind"] == "finish"))
    return {"title": f"{info['race_name']} {info['season']}", "laps": n_laps, "scenes": scenes}


if __name__ == "__main__":
    import sys
    f = f"{int(sys.argv[1])}_{int(sys.argv[2]):02d}" if len(sys.argv) == 3 else "2025_12"
    out = film(f)
    print(out["title"])
    for s in out["scenes"]:
        print(f"  lap {s['lap']:>2} · {s['title']}: {s['text']}")
