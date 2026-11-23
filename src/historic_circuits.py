"""Historic circuits in 3D: old layouts rebuilt from OpenStreetMap with real elevation.

THE SHAPES come from OpenStreetMap (© OpenStreetMap contributors, Open Database Licence), fetched once
through the free Overpass API and kept in data/historic/osm_<key>.json:
  Nordschleife   the route relation of today's Nordschleife, its ways already in lap order
  Hockenheim     the 1965-2001 layout: the forest section is kept in OpenStreetMap as abandoned raceway
                 ways, joined to the parts of the current track the old one shared
The ways are stitched end to end into one closed loop, turned into metres and evened out every 5 m.

THE HEIGHTS come from OpenTopoData's free public API (the EU-DEM 25 m model in Europe), sampled every
25 m and smoothed, so the Nordschleife's 300 m of climb shows in the 3D view and in the physics.

Each track is saved as data/historic/<key>.parquet in the same form as a race's track.parquet (x, y, z
in tenths of a metre), so the lap simulator and the 3D kit read it like any other circuit.

  python src/historic_circuits.py --fetch      fetch the OpenStreetMap shapes (slow, polite, once)
  python src/historic_circuits.py              stitch, add heights, save every circuit, then drive the
                                               1975, 2001 and 2026 cars round them (summary.json)
"""
import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parent.parent
HIST = ROOT / "data" / "historic"
MIRRORS = ["https://overpass.private.coffee/api/interpreter", "https://overpass.kumi.systems/api/interpreter",
           "https://overpass-api.de/api/interpreter"]
ELEVATION = "https://api.opentopodata.org/v1/eudem25m"
HEAD = {"User-Agent": "f1-podium-predictor (open-source project)"}

CIRCUITS = {
    "nordschleife": {"query": "[out:json][timeout:120];relation(38566);out geom;", "kind": "relation"},
    "hockenheim": {"query": '[out:json][timeout:120];(way(49.30,8.52,49.37,8.67)["highway"="raceway"];'
                            'way(49.30,8.52,49.37,8.67)["abandoned:highway"="raceway"];);out geom;',
                   "kind": "ways", "snap": 40.0, "link": 200.0,
                   # pieces that were never part of the 1994-2001 Grand Prix lap
                   "skip": ["Boxengasse", "Rallycross", "Quartermile", "Kleiner Kurs", "Schikanenvariante",
                            "1932-1968", "ohne Schikane", "pitlane"]},
}


# ---------- fetching ----------

def overpass(query):
    for attempt in range(10):
        try:
            r = requests.post(MIRRORS[attempt % len(MIRRORS)], data={"data": query}, headers=HEAD, timeout=180)
            if r.status_code == 200:
                return r.json()
        except requests.RequestException:
            pass
        time.sleep(4 * (attempt + 1))
    raise RuntimeError("Overpass kept refusing")


def fetch():
    HIST.mkdir(parents=True, exist_ok=True)
    for key, c in CIRCUITS.items():
        path = HIST / f"osm_{key}.json"
        if path.exists():
            continue
        path.write_text(json.dumps(overpass(c["query"])), encoding="utf-8")
        print(f"{key}: fetched")


# ---------- stitching ----------

def _pts(way):
    return [(g["lat"], g["lon"]) for g in way["geometry"]]


def stitch_in_order(ways):
    """Ways listed in lap order: join them, flipping any that run the other way."""
    loop = list(_pts(ways[0]))
    if len(ways) > 1:
        nxt = _pts(ways[1])
        if min(_d(loop[0], nxt[0]), _d(loop[0], nxt[-1])) < min(_d(loop[-1], nxt[0]), _d(loop[-1], nxt[-1])):
            loop.reverse()
    for w in ways[1:]:
        p = _pts(w)
        if _d(loop[-1], p[-1]) < _d(loop[-1], p[0]):
            p.reverse()
        loop.extend(p[1:] if _d(loop[-1], p[0]) < 1e-9 else p)
    return loop


def stitch_cycle(elements, cfg):
    """Ways in no order: the longest closed loop through them (the graph is small, so a full search
    is quick), after leaving out the pieces in cfg["skip"]."""
    def skipped(w):
        text = " ".join(str(v) for v in w.get("tags", {}).values())
        return any(k in text for k in cfg.get("skip", []))
    ways = [w for w in elements if w["type"] == "way" and w.get("geometry") and not skipped(w)]

    # Ways usually meet at a shared node, but old, abandoned pieces are often mapped with small gaps
    # between them: endpoints closer than cfg["snap"] metres are treated as the same junction.
    tol = cfg.get("snap", 0.5)
    raw_ends = [(g["lat"], g["lon"]) for w in ways for g in (w["geometry"][0], w["geometry"][-1])]
    junction = list(range(len(raw_ends)))

    def find(i):
        while junction[i] != i:
            junction[i] = junction[junction[i]]
            i = junction[i]
        return i
    for i, a in enumerate(raw_ends):
        for j in range(i):
            b = raw_ends[j]
            if math.hypot((a[0] - b[0]) * 111_320, (a[1] - b[1]) * 111_320 * math.cos(math.radians(a[0]))) < tol:
                junction[find(i)] = find(j)
    index = {id(w): k for k, w in enumerate(ways)}

    def end(w, i):
        return find(2 * index[id(w)] + (0 if i == 0 else 1))
    length = {}
    adj = {}
    for k, w in enumerate(ways):
        p = _pts(w)
        length[k] = sum(math.dist((a[0] * 111_320, a[1] * 72_000), (b[0] * 111_320, b[1] * 72_000)) for a, b in zip(p, p[1:]))
        a, b = end(w, 0), end(w, -1)
        adj.setdefault(a, []).append((k, b))
        adj.setdefault(b, []).append((k, a))
    best = (0.0, [])

    def walk(start, node, used, path, total):
        nonlocal best
        for k, other in adj.get(node, []):
            if k in used:
                continue
            if other == start and total + length[k] > best[0]:
                best = (total + length[k], path + [(k, node)])
            if other != start and other not in {n for _, n in path}:
                walk(start, other, used | {k}, path + [(k, node)], total + length[k])

    for start in adj:
        walk(start, start, frozenset(), [], 0.0)
    loop = []
    for k, frm in best[1]:
        p = _pts(ways[k])
        if end(ways[k], 0) != frm:
            p.reverse()
        loop.extend(p if not loop else p[1:])
    return loop


def stitch_via_old_section(elements, cfg):
    """A lap that leaves the current track for an abandoned section and comes back.

    Every point of every way becomes a node of a graph. The abandoned section (the forest loop at
    Hockenheim) is found as the longest chain of abandoned raceway; its two loose ends are linked to
    the nearest point of the current track (up to cfg["link"] metres away: the bit of track that joined
    them was rebuilt and is no longer mapped). The lap is then the shortest path on the current track
    from the start line to one end, the abandoned section, and the shortest path back to the line."""
    import heapq

    def skipped(w):
        text = " ".join(str(v) for v in w.get("tags", {}).values())
        return any(k in text for k in cfg.get("skip", []))
    ways = [w for w in elements if w["type"] == "way" and w.get("geometry")]
    key = lambda g: (round(g["lat"], 7), round(g["lon"], 7))
    lat0 = ways[0]["geometry"][0]["lat"]
    metres = lambda a, b: math.hypot((a[0] - b[0]) * 111_320, (a[1] - b[1]) * 111_320 * math.cos(math.radians(lat0)))
    edges = {"old": {}, "new": {}}
    for w in ways:
        if skipped(w):
            continue
        kind = "old" if "abandoned:highway" in w.get("tags", {}) else "new"
        pts = [key(g) for g in w["geometry"]]
        for a, b in zip(pts, pts[1:]):
            d = metres(a, b)
            edges[kind].setdefault(a, []).append((b, d))
            edges[kind].setdefault(b, []).append((a, d))

    def dijkstra(graph, src, dst):
        dist, prev, todo = {src: 0.0}, {}, [(0.0, src)]
        while todo:
            d, u = heapq.heappop(todo)
            if u == dst:
                break
            if d > dist[u]:
                continue
            for v, w in graph.get(u, []):
                if d + w < dist.get(v, 1e18):
                    dist[v], prev[v] = d + w, u
                    heapq.heappush(todo, (d + w, v))
        path = [dst]
        while path[-1] != src:
            path.append(prev[path[-1]])
        return path[::-1], dist[dst]

    old, new = edges["old"], edges["new"]
    # join old pieces whose ends nearly touch, so the section is one chain
    ends = [n for n, nb in old.items() if len(nb) == 1]
    for i, a in enumerate(ends):
        for b in ends[:i]:
            if metres(a, b) < cfg.get("snap", 40.0):
                old[a].append((b, metres(a, b)))
                old[b].append((a, metres(a, b)))
    loose = [n for n, nb in old.items() if len(nb) == 1]
    best = None
    for i, a in enumerate(loose):                       # the two loose ends furthest apart along the old track
        for b in loose[:i]:
            try:
                path, d = dijkstra(old, a, b)
            except KeyError:
                continue
            if best is None or d > best[1]:
                best = (path, d)
    section = best[0]
    nearest = lambda p: min(new, key=lambda n: metres(n, p))
    a_link, b_link = nearest(section[0]), nearest(section[-1])
    if max(metres(a_link, section[0]), metres(b_link, section[-1])) > cfg.get("link", 200.0):
        raise ValueError("the old section doesn't come close enough to the current track")
    pit = [w for w in ways if "Boxengasse" in w.get("tags", {}).get("name", "")]
    mid = pit[0]["geometry"][len(pit[0]["geometry"]) // 2]
    line = nearest(key(mid))
    # the old lap ran from the line to the first corner and out into the forest: start with the end
    # that the line reaches first along the current track
    to_a, da = dijkstra(new, line, a_link)
    to_b, db = dijkstra(new, line, b_link)
    if db < da:
        section, a_link, b_link, to_a = section[::-1], b_link, a_link, to_b
    back, _ = dijkstra(new, b_link, line)
    loop = to_a + section + back[:-1]
    return loop


def _d(a, b):
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2


def to_metres(latlon):
    lat0 = np.mean([p[0] for p in latlon])
    k = 111_320.0
    x = np.array([(p[1]) * k * math.cos(math.radians(lat0)) for p in latlon])
    y = np.array([p[0] * k for p in latlon])
    return x - x.mean(), y - y.mean(), lat0


def even(x, y, step=5.0):
    """Points every `step` metres round the closed loop (duplicate points removed)."""
    keep = np.r_[True, np.hypot(np.diff(x), np.diff(y)) > 0.5]
    x, y = x[keep], y[keep]
    seg = np.hypot(np.diff(np.r_[x, x[0]]), np.diff(np.r_[y, y[0]]))
    s = np.r_[0, np.cumsum(seg)]
    n = int(s[-1] / step)
    t = np.linspace(0, s[-1], n, endpoint=False)
    return np.interp(t, s, np.r_[x, x[0]]), np.interp(t, s, np.r_[y, y[0]]), float(s[-1])


def heights(xe, ye, latlon_of, every=25.0):
    """Ground height (m) at every point, from OpenTopoData sampled every `every` metres and smoothed."""
    n = len(xe)
    step = max(1, int(every / 5.0))
    idx = list(range(0, n, step))
    pts = [latlon_of(xe[i], ye[i]) for i in idx]
    z = []
    for k in range(0, len(pts), 100):                       # 100 places per request, one request a second
        chunk = "|".join(f"{a:.6f},{b:.6f}" for a, b in pts[k:k + 100])
        for attempt in range(6):
            try:
                r = requests.get(ELEVATION, params={"locations": chunk}, headers=HEAD, timeout=60)
                if r.status_code == 200:
                    z += [res["elevation"] for res in r.json()["results"]]
                    break
            except requests.RequestException:
                pass
            time.sleep(3 * (attempt + 1))
        else:
            raise RuntimeError("OpenTopoData kept refusing")
        time.sleep(1.1)
    z = np.array([v if v is not None else np.nan for v in z], float)
    z = pd.Series(z).interpolate(limit_direction="both").to_numpy()
    full = np.interp(np.arange(n), idx + [n], np.r_[z, z[0]])
    k = 9                                                     # light smoothing: the model has 25 m cells
    pad = np.r_[full[-k:], full, full[:k]]
    return np.convolve(pad, np.ones(2 * k + 1) / (2 * k + 1), mode="same")[k:-k]


def build(key):
    raw = json.loads((HIST / f"osm_{key}.json").read_text(encoding="utf-8"))
    loop = (stitch_in_order([m for m in raw["elements"][0]["members"] if m["type"] == "way"])
            if CIRCUITS[key]["kind"] == "relation" else stitch_via_old_section(raw["elements"], CIRCUITS[key]))
    lat0 = float(np.mean([p[0] for p in loop]))
    lon0 = float(np.mean([p[1] for p in loop]))
    x, y, _ = to_metres(loop)
    xe, ye, length = even(x, y)
    k = 111_320.0
    cx = np.mean([p[1] for p in loop]) * k * math.cos(math.radians(lat0))
    cy = np.mean([p[0] for p in loop]) * k

    def latlon_of(px, py):
        return (py + cy) / k, (px + cx) / (k * math.cos(math.radians(lat0)))

    z = heights(xe, ye, latlon_of)
    df = pd.DataFrame({"x": np.round(xe * 10).astype(int), "y": np.round(ye * 10).astype(int),
                       "z": np.round(z * 10).astype(int)})
    df.to_parquet(HIST / f"{key}.parquet", index=False)
    print(f"{key}: {length / 1000:.3f} km, {len(df)} points, height {z.min():.0f}-{z.max():.0f} m")
    return df


# ---------- three eras of car, on the old tracks ----------

SMOOTHING = 2.0     # m: the spline may stray 2 m from OpenStreetMap's centre line, roughly a racing line

# Each era's car in lapsim terms. The tyre grip of the 1975 and 2001 cars is the one free number, fitted so
# the car matches a real benchmark lap on its own circuit (average speed, so a different layout length
# doesn't matter). The 2026 car is the middle of every calibrated 2026 car.
ERAS = {
    "1975": {"label": "1975 car", "colour": "#e8b33a",
             "car": dict(mass=680, power_kw=340, wing=0.0, downforce_scale=0.5, drag_scale=1.1),
             "fit": ("nordschleife", 196.4),
             "benchmark": "Niki Lauda's 1975 pole, 6:58.6 on the 22.8 km Grand Prix layout (196.4 km/h)"},
    "2001": {"label": "2001 car", "colour": "#27f4d2",
             "car": dict(mass=650, power_kw=610, wing=0.0, downforce_scale=0.95, drag_scale=0.95),
             "fit": ("hockenheim", 250.4),
             "benchmark": "Juan Pablo Montoya's 2001 pole, 1:38.117 on the 6.825 km layout (250.4 km/h)"},
    "2026": {"label": "2026 car", "colour": "#e10600", "car": None, "fit": None,
             "benchmark": "the middle of every 2026 car calibrated to a real circuit"},
}
FACTS = {
    "nordschleife": {"name": "Nürburgring Nordschleife", "years": "Grand Prix venue 1951–1976",
                     "note": "Today's 20.8 km loop. The Grand Prix layout also used the old pit straight, now under "
                             "the modern circuit, for 22.8 km.",
                     "record": "Fastest lap ever: Timo Bernhard, Porsche 919 Evo, 5:19.546 (2018)."},
    "hockenheim": {"name": "Hockenheimring, old layout", "years": "Grand Prix layout 1970s–2001",
                   "note": "The long forest straights with three chicanes, replaced in 2002 by today's shorter track. "
                           "The forest section is now woodland again.",
                   "record": ""},
}


def track_of(key):
    import lapsim as L
    return L.build_track(pd.read_parquet(HIST / f"{key}.parquet"), smoothing=SMOOTHING)


def modern_car():
    import statistics
    import lapsim as L
    cal = L.load_calibration()
    year = max(int(k[:4]) for k, v in cal.items() if v.get("usable"))
    cars = [v["car"] for k, v in cal.items() if k.startswith(str(year)) and v.get("usable")]
    return L.Car(**{**L.asdict(L.Car()), **{k: statistics.median(c[k] for c in cars)
                                            for k in ("mass", "power_kw", "wing", "grip")}})


def best_wing(car, track):
    import lapsim as L
    from dataclasses import replace
    return min((replace(car, wing=w) for w in np.linspace(0, 1, 11)), key=lambda c: L.simulate(c, track)["lap_time"])


def summarise():
    """Fit the era cars, drive every era round every circuit, save data/historic/summary.json."""
    import lapsim as L
    from dataclasses import replace
    from scipy.optimize import brentq
    keys = [k for k in CIRCUITS if (HIST / f"{k}.parquet").exists()]
    tracks = {k: track_of(k) for k in keys}
    cars, fitted = {}, {}
    for era, e in ERAS.items():
        if e["car"] is None:
            cars[era] = modern_car()
            continue
        base = L.Car(**{**L.asdict(L.Car()), **e["car"]})
        key, target = e["fit"]
        if key in tracks:
            tr = tracks[key]
            g = brentq(lambda g: tr.length / L.simulate(replace(base, grip=g), tr)["lap_time"] * 3.6 - target,
                       1.0, 3.0, xtol=1e-3)
            fitted[era] = True
        else:
            g = 1.7                              # its benchmark circuit isn't built yet: a typical grip
            fitted[era] = False
        cars[era] = replace(base, grip=round(g, 3))
    out = {"eras": {}, "circuits": {}}
    for era, car in cars.items():
        out["eras"][era] = {**{k: v for k, v in ERAS[era].items() if k != "car"}, "car": L.asdict(car),
                            "fitted": fitted.get(era, False)}
    for key, tr in tracks.items():
        laps = {}
        for era, car in cars.items():
            c = best_wing(car, tr) if era == "2026" else car
            sim = L.simulate(c, tr)
            laps[era] = {"lap": round(sim["lap_time"], 2), "avg_kmh": round(tr.length / sim["lap_time"] * 3.6, 1),
                         "top_kmh": round(float(sim["speed_kmh"].max())), "wing": round(c.wing, 2)}
        out["circuits"][key] = {**FACTS[key], "length_km": round(tr.length / 1000, 3),
                                "climb_m": round(float(tr.z.max() - tr.z.min())), "laps": laps}
        print(key, {e: v["lap"] for e, v in laps.items()})
    (HIST / "summary.json").write_text(json.dumps(out, indent=1), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch", action="store_true")
    parser.add_argument("keys", nargs="*")
    args = parser.parse_args()
    if args.fetch:
        fetch()
        return
    for key in args.keys or CIRCUITS:
        if (HIST / f"osm_{key}.json").exists():
            build(key)
    summarise()


if __name__ == "__main__":
    main()
