"""Rain Crossover: when were slicks faster than intermediates, and who switched at the right moment?

For a race run partly in the wet, every clean lap (no lap 1, no pit laps, no safety-car laps) is put in
one of two groups: on wet-weather tyres (intermediates or full wets) or on slicks. Each lap, the median
time of each group is compared. The CROSSOVER is the lap where the faster group changes: slicks
becoming faster as the track dries, or intermediates becoming faster as rain arrives.

Each driver's switches between wet tyres and slicks are then measured against the nearest crossover in
the same direction: how many laps early or late they came in, and roughly how much time that cost
(the gap between the groups on the laps they spent on the wrong tyre).

Rain at the circuit comes from OpenF1's weather feed (rainfall flag, by lap).
"""
import numpy as np
import pandas as pd

import race_story as R

WET = {"INTERMEDIATE", "WET"}
SLICK = {"SOFT", "MEDIUM", "HARD"}


def is_mixed(laps, min_laps=20):
    c = laps["compound"].value_counts()
    return sum(c.get(x, 0) for x in WET) >= min_laps and sum(c.get(x, 0) for x in SLICK) >= min_laps


def analyse(folder):
    laps, pits, control, info = R.load(folder)
    neutral = R.neutral_laps(laps, control)
    stops = R.pit_laps(laps)
    d = laps.dropna(subset=["lap_duration", "compound"]).copy()
    d = d[(d["lap_number"] > 1) & ~d["lap_number"].isin(neutral)]
    d = d[[lap not in stops.get(int(n), set()) for n, lap in zip(d["driver_number"], d["lap_number"])]]
    d["group"] = np.where(d["compound"].isin(WET), "Wet tyres", np.where(d["compound"].isin(SLICK), "Slicks", None))
    d = d.dropna(subset=["group"])
    med = d.groupby(["lap_number", "group"])["lap_duration"].agg(["median", "size"]).reset_index()
    med = med[med["size"] >= 1]
    wide = med.pivot(index="lap_number", columns="group", values="median")
    for col in ("Wet tyres", "Slicks"):
        if col not in wide:
            wide[col] = np.nan
    wide["gap"] = wide["Slicks"] - wide["Wet tyres"]          # < 0: slicks faster
    both = wide.dropna(subset=["gap"])
    crossings = []
    signs = np.sign(both["gap"]).tolist()
    lap_list = both.index.tolist()
    current = None
    for k, sg in enumerate(signs):           # a change only counts if it holds for three compared laps
        if sg == 0:
            continue
        ahead = [s for s in signs[k:k + 3] if s != 0]
        if current is None:
            if len(ahead) >= 2 and all(s == sg for s in ahead):
                current = sg
            continue
        if sg != current and len(ahead) >= 3 and all(s == sg for s in ahead):
            crossings.append({"lap": int(lap_list[k]), "to": "Slicks" if sg < 0 else "Wet tyres"})
            current = sg

    # Rain by lap from the weather feed
    path = R.RACES_DIR / folder / "weather.parquet"
    rain_laps = []
    if path.exists():
        w = pd.read_parquet(path)
        lead = laps.groupby("lap_number")["t_start"].min()
        for lap, t0 in lead.items():
            t1 = lead.get(lap + 1, t0 + 120)
            near = w[(w["t"] >= t0 - 60) & (w["t"] <= t1)]
            if len(near) and near["rainfall"].astype(float).max() > 0:
                rain_laps.append(int(lap))

    for c in crossings:
        c["measured"] = True

    # Each driver's switches between wet tyres and slicks
    raw = []
    for num, g in laps.sort_values("lap_number").groupby("driver_number"):
        g = g.dropna(subset=["compound"])
        fam = g["compound"].map(lambda c: "Wet tyres" if c in WET else "Slicks" if c in SLICK else None)
        prev_fam = None
        pitted = stops.get(int(num), set())
        for lap, f in zip(g["lap_number"], fam):
            if f and prev_fam and f != prev_fam and int(lap) in pitted:   # a real tyre change in the pits
                raw.append((int(num), int(lap), f))
            if f and (prev_fam is None or int(lap) in pitted):
                prev_fam = f

    # Where the two groups never ran clean laps side by side, there's no direct comparison. Then the
    # crossover is estimated as the lap by which half of the field's switches that way had happened.
    for to in ("Slicks", "Wet tyres"):
        laps_to = sorted(lap for _, lap, f in raw if f == to)
        if len(laps_to) >= 5 and not any(c["to"] == to for c in crossings):
            crossings.append({"lap": int(np.median(laps_to)), "to": to, "measured": False})
    crossings.sort(key=lambda c: c["lap"])

    who = R.drivers(info)
    switches = []
    for num, lap, f in raw:
        same = [c for c in crossings if c["to"] == f]
        best = min(same, key=lambda c: abs(c["lap"] - lap)) if same else None
        cost = None
        if best and best["measured"]:          # a time cost only where the two groups were really compared
            lo, hi = sorted((lap, best["lap"]))
            seg = wide.loc[(wide.index >= lo) & (wide.index < hi), "gap"].abs().dropna()
            cost = float(seg.sum())
        switches.append({"driver_number": num, "code": who.get(num, {}).get("code", str(num)),
                         "team": who.get(num, {}).get("team", ""), "colour": who.get(num, {}).get("colour") or "#8a8a96",
                         "lap": lap, "to": f, "crossover": best["lap"] if best else None,
                         "laps_off": int(lap - best["lap"]) if best else None, "cost": cost})
    return {"info": info, "laps": wide.reset_index(), "crossings": crossings, "rain_laps": rain_laps,
            "switches": pd.DataFrame(switches), "neutral": sorted(neutral)}


def mixed_races():
    out = []
    for path in sorted(R.RACES_DIR.glob("*_*")):
        if (path / "laps.parquet").exists() and is_mixed(pd.read_parquet(path / "laps.parquet")):
            out.append(path.name)
    return out


if __name__ == "__main__":
    for folder in mixed_races():
        a = analyse(folder)
        print(folder, a["info"]["race_name"], "crossovers:", a["crossings"], "rain laps:", len(a["rain_laps"]),
              "switches:", len(a["switches"]))
