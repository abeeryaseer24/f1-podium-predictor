"""Lap Simulator engine: how fast a Formula 1 car can go round a real circuit, and why.

It is a "quasi-steady-state" lap simulator, the kind teams used before full vehicle models
and still use for quick studies. At every point of the lap the car is treated as a single
point with a mass, a tyre grip limit, downforce, drag and an engine:

  1. Corner limit. In a corner the tyres must supply  m v^2 x curvature  sideways. The tyres
     can give  mu x N, where N is the car's weight PLUS its downforce (which grows with v^2).
     Solving that gives the fastest speed the car can take each point of the track.
  2. Forward pass. Out of each corner the car accelerates as hard as the engine and the rear
     tyres allow, minus drag, rolling resistance and any uphill slope.
  3. Backward pass. Into each corner it brakes as late as the tyres allow (drag helps).
  The car's speed everywhere is the lowest of the three. The lap time is the track length
  divided by that speed, added up point by point.

Tyres share their grip between cornering and braking or accelerating (the "friction circle"),
and grip grows more slowly than the load on the tyre ("load sensitivity"), which is why
doubling downforce does not double cornering grip.

The track comes from the race's fastest lap in OpenF1 (track.parquet: x, y, z in tenths of
a metre). It is smoothed into a spline so the curvature can be measured. The air gets
thinner with altitude (Mexico City is at 2,240 m), so downforce and drag drop there.

CALIBRATION. For every prepared race, calibrate() finds the wing level, the grip and the
power that make the simulated speed trace match the real fastest lap best, and saves them in
data/processed/lapsim_calibration.json. The app then starts every circuit from its own
calibrated car, and the visitor changes things from there.

Simple, stated assumptions (this is a teaching model, not a team's simulator):
- a point mass: no suspension, no weight transfer, no yaw; one grip number for the whole car
- the wing level moves downforce (in a straight line) and drag (with its square) together
- the engine gives constant power at every speed (no gears, no energy limits per lap)
- no DRS, no tyre wear, no fuel burn during the lap, no wind, no kerbs
- the real lap is the race's fastest lap, so it already includes race fuel and worn tyres

Usage:
  python src/lapsim.py 2025 16        one race: calibrate it and print how close it gets
  python src/lapsim.py --all          calibrate every prepared race (the pipeline runs this)
  python src/lapsim.py --missing      only races that are not calibrated yet
"""
import json
import math
import sys
from dataclasses import asdict, dataclass, replace
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.interpolate import splev, splprep
from scipy.optimize import minimize

ROOT = Path(__file__).resolve().parent.parent
RACES_DIR = ROOT / "data" / "races"
CALIBRATION_FILE = ROOT / "data" / "processed" / "lapsim_calibration.json"

G = 9.81                    # m/s^2
RHO_SEA = 1.225             # air density at sea level, kg/m^3
SCALE_HEIGHT = 8500.0       # m: air density falls by e every 8.5 km
STEP = 4.0                  # m between simulated points
SMOOTHING = 0.5             # spline smoothing: allowed average error per track point, in metres

MAX_GAP = 120.0             # m: bigger gaps between position samples mean missing data
MAX_RMSE = 35.0             # km/h: a calibration this far off the real lap isn't used

# The wing level runs from 0 (Monza-style low drag) to 1 (Monaco-style maximum downforce).
# Ranges are typical published estimates for modern cars, as downforce or drag coefficient
# times frontal area (m^2). Downforce in newtons = 0.5 x air density x CzA x speed^2.
# Downforce rises in a straight line with the wing level, drag with its square, the way a
# wing's induced drag grows with the square of its lift. So the first steps of wing are cheap
# and the last ones expensive, and every circuit has its own best wing level.
CZA_LOW, CZA_HIGH = 3.2, 5.6
CXA_LOW, CXA_HIGH = 1.00, 1.90
DRAG_CURVE = 2.0           # drag grows as wing squared: each extra step of wing costs more drag than the last


@dataclass(frozen=True)
class Car:
    """Everything the simulator knows about the car. All values are editable in the app."""
    mass: float = 820.0           # kg, car + driver + race fuel left at the fastest lap
    power_kw: float = 720.0       # kW at the wheels, engine + electric motor together
    wing: float = 0.5             # 0 = lowest drag, 1 = most downforce
    grip: float = 1.70            # tyre friction coefficient at the car's static weight
    load_sensitivity: float = 0.12  # how quickly grip per newton falls as load rises (0 = none)
    rear_share: float = 0.56      # share of the load on the driven (rear) wheels
    rolling: float = 0.012        # rolling resistance coefficient
    downforce_scale: float = 1.0  # extra multiplier on downforce (aero upgrades)
    drag_scale: float = 1.0       # extra multiplier on drag

    @property
    def cza(self):
        return (CZA_LOW + self.wing * (CZA_HIGH - CZA_LOW)) * self.downforce_scale

    @property
    def cxa(self):
        return (CXA_LOW + self.wing ** DRAG_CURVE * (CXA_HIGH - CXA_LOW)) * self.drag_scale


# ---------- the track ----------

@dataclass
class Track:
    s: np.ndarray            # m from the start line, every STEP metres
    x: np.ndarray            # m (centred)
    y: np.ndarray
    z: np.ndarray            # m above sea level
    curvature: np.ndarray    # 1/m (positive = turning left)
    slope: np.ndarray        # rise over run
    length: float            # m
    rho: float               # air density at this circuit, kg/m^3
    source_index: np.ndarray  # nearest point of track.parquet for every simulated point
    source_s: np.ndarray      # where each point of track.parquet sits along this track, m


def build_track(track_df, step=STEP, smoothing=SMOOTHING):
    """Turn track.parquet into an evenly spaced, smoothed track with curvature and slope."""
    pts = track_df[["x", "y", "z"]].to_numpy(dtype=float) / 10.0      # tenths of a metre -> m
    keep = np.r_[True, np.hypot(*np.diff(pts[:, :2], axis=0).T) > 0.05]
    pts = pts[keep]
    xy_centre = pts[:, :2].mean(axis=0)

    # A closed (periodic) smoothing spline through the points
    closed = np.vstack([pts, pts[:1]])
    tck, _ = splprep([closed[:, 0], closed[:, 1], closed[:, 2]], s=len(closed) * smoothing ** 2,
                     per=True, k=3)

    # Sample finely, measure length, then resample at even spacing in metres
    fine_u = np.linspace(0, 1, 20_000, endpoint=False)
    fx, fy, fz = splev(fine_u, tck)
    seg = np.hypot(np.diff(np.r_[fx, fx[0]]), np.diff(np.r_[fy, fy[0]]))
    fine_s = np.r_[0, np.cumsum(seg)[:-1]]
    length = float(seg.sum())
    n = int(round(length / step))
    s = np.linspace(0, length, n, endpoint=False)
    u = np.interp(s, fine_s, fine_u)

    x, y, z = splev(u, tck)
    dx, dy, dz = splev(u, tck, der=1)
    ddx, ddy, _ = splev(u, tck, der=2)
    curvature = (dx * ddy - dy * ddx) / np.power(dx * dx + dy * dy, 1.5)
    slope = dz / np.hypot(dx, dy)

    # Light extra smoothing of curvature (a few metres) removes leftover noise
    curvature = _circular_smooth(curvature, sigma_points=max(1, int(round(6 / step))))
    slope = np.clip(_circular_smooth(slope, sigma_points=max(1, int(round(30 / step)))), -0.2, 0.2)

    altitude = float(np.mean(z))
    rho = RHO_SEA * math.exp(-max(altitude, 0) / SCALE_HEIGHT)

    # Which original point is closest to each simulated point (for the 3D view and comparisons)
    src = pts[:, :2]
    d = (x[:, None] - src[None, :, 0]) ** 2 + (y[:, None] - src[None, :, 1]) ** 2
    source_index = np.flatnonzero(keep)[d.argmin(axis=1)]
    # ...and where along our track each original point sits, in metres
    source_s = np.full(len(track_df), np.nan)
    source_s[np.flatnonzero(keep)] = s[d.argmin(axis=0)]

    return Track(s=s, x=x - xy_centre[0], y=y - xy_centre[1], z=z, curvature=curvature,
                 slope=slope, length=length, rho=rho, source_index=source_index, source_s=source_s)


def _circular_smooth(values, sigma_points):
    """Gaussian smoothing that wraps round the lap."""
    radius = int(3 * sigma_points)
    k = np.exp(-0.5 * (np.arange(-radius, radius + 1) / sigma_points) ** 2)
    k /= k.sum()
    padded = np.r_[values[-radius:], values, values[:radius]]
    return np.convolve(padded, k, mode="valid")


# ---------- the physics ----------

def _grip_force(car, normal):
    """Tyre grip in newtons for a given vertical load, with load sensitivity."""
    n0 = car.mass * G
    return car.grip * n0 ** car.load_sensitivity * np.power(normal, 1 - car.load_sensitivity)


def corner_limit(car, track):
    """The fastest speed (m/s) the tyres allow at every point, using all the grip sideways."""
    k = np.abs(track.curvature)
    q = 0.5 * track.rho * car.cza
    lo = np.full_like(k, 5.0)
    hi = np.full_like(k, 150.0)
    # Bisection on: grip(m g + q v^2) - m v^2 k >= 0  (vectorised over every point)
    for _ in range(40):
        v = 0.5 * (lo + hi)
        ok = _grip_force(car, car.mass * G + q * v * v) >= car.mass * v * v * k
        lo = np.where(ok, v, lo)
        hi = np.where(ok, hi, v)
    return lo


def simulate(car, track):
    """Simulate one flying lap. Returns a dict of arrays (one value per track point) and the lap time."""
    n = len(track.s)
    ds = track.length / n
    m, rho = car.mass, track.rho
    q_down, q_drag = 0.5 * rho * car.cza, 0.5 * rho * car.cxa
    power = car.power_kw * 1000.0
    kappa = np.abs(track.curvature).tolist()
    slope = track.slope.tolist()
    v_corner = corner_limit(car, track)
    vc = v_corner.tolist()
    n0_ls = (m * G) ** car.load_sensitivity
    one_minus = 1 - car.load_sensitivity
    mu = car.grip

    def long_grip(v, i):
        normal = m * G + q_down * v * v
        grip = mu * n0_ls * normal ** one_minus
        lateral = m * v * v * kappa[i]
        left = 1 - (lateral / grip) ** 2
        return (grip * math.sqrt(left) if left > 0 else 0.0), normal

    start = int(np.argmin(v_corner))

    # Forward pass: accelerate as hard as possible, starting from the slowest corner
    fwd = [0.0] * n
    v = vc[start]
    for step in range(n):
        i = (start + step) % n
        v = min(v, vc[i])
        fwd[i] = v
        grip_long, normal = long_grip(v, i)
        drive = min(power / max(v, 1.0), grip_long * car.rear_share)
        a = (drive - q_drag * v * v - car.rolling * normal - m * G * slope[i]) / m
        v = math.sqrt(max(v * v + 2 * a * ds, 1.0))

    # Backward pass: brake as late as possible
    bwd = [0.0] * n
    v = vc[start]
    for step in range(n):
        i = (start - step) % n
        v = min(v, vc[i], fwd[i])
        bwd[i] = v
        grip_long, normal = long_grip(v, i)
        decel = (grip_long + q_drag * v * v + car.rolling * normal + m * G * slope[i]) / m
        v = math.sqrt(max(v * v + 2 * max(decel, 0.0) * ds, 1.0))

    speed = np.minimum(np.array(fwd), np.array(bwd))
    nxt = np.roll(speed, -1)
    dt = 2 * ds / (speed + nxt)
    time = np.r_[0, np.cumsum(dt)[:-1]]

    accel = (nxt * nxt - speed * speed) / (2 * ds)
    lat_g = speed * speed * np.abs(track.curvature) / G
    braking = np.array(bwd) < np.array(fwd) - 1e-6
    corner_limited = speed >= v_corner - 1e-6
    mode = np.where(braking, "brake", np.where(corner_limited, "corner", "throttle"))

    downforce = q_down * speed * speed
    drag = q_drag * speed * speed
    return {
        "s": track.s, "time": time, "speed": speed, "speed_kmh": speed * 3.6,
        "long_g": accel / G, "lat_g": lat_g, "mode": mode,
        "downforce_n": downforce, "drag_n": drag, "corner_limit": v_corner,
        "lap_time": float(dt.sum()),
    }


def gears(speed_kmh, top_speed_kmh=None):
    """A display gear (1-8) for every point, from evenly stepped ratios. Not used by the physics."""
    top = top_speed_kmh or float(np.max(speed_kmh)) * 1.02
    ratios = top * np.geomspace(0.30, 1.0, 8)      # top speed of each gear
    return np.minimum(np.searchsorted(ratios, speed_kmh) + 1, 8)


# ---------- comparing with the real lap ----------

def _real_positions(track):
    """Where each real sample sits along our track (m), with the start-line wrap fixed."""
    at = track.source_s
    ok = ~np.isnan(at)
    # The lap is a loop: the first few original points can map near the end of the track,
    # and the last few near the start
    first, last = np.arange(len(at)) < len(at) // 4, np.arange(len(at)) > len(at) * 3 // 4
    at = np.where(ok & first & (at > track.length * 0.75), at - track.length, at)
    at = np.where(ok & last & (at < track.length * 0.25), at + track.length, at)
    return at, ok


def real_progress(track_df, track):
    """The real lap as (time in s, distance round the lap in m), for animating it."""
    at, ok = _real_positions(track)
    t = track_df["s"].to_numpy(dtype=float)[ok]
    s = np.maximum.accumulate(at[ok])                 # never run backwards
    lap = t[-1] + float(np.median(np.diff(t)))
    return np.r_[t, lap], np.r_[s, s[0] + track.length]


def real_trace(track_df, track):
    """The real fastest lap's speed (km/h), throttle and brake at every simulated point."""
    t = track_df.reset_index(drop=True)
    at, ok = _real_positions(track)
    order = np.argsort(at[ok])
    where = at[ok][order]

    def along(column):
        values = t[column].to_numpy(dtype=float)[ok][order]
        return np.interp(track.s, where, values, period=track.length)

    return {
        "speed_kmh": along("speed"),
        "throttle": along("throttle"),
        "brake": along("brake"),
        "lap_time": float(t["s"].iloc[-1] + np.median(np.diff(t["s"]))),
    }


def speed_error(sim, real):
    """Root-mean-square gap between simulated and real speed, km/h."""
    return float(np.sqrt(np.mean((sim["speed_kmh"] - real["speed_kmh"]) ** 2)))


def fit(track_df, track=None, start=None):
    """Find wing, grip and power so the simulated speed trace matches the real lap best."""
    track = track or build_track(track_df)
    real = real_trace(track_df, track)
    base = start or Car()

    def make(params):
        wing, grip, power = params
        return replace(base, wing=float(np.clip(wing, 0, 1)), grip=float(np.clip(grip, 0.8, 3.0)),
                       power_kw=float(np.clip(power, 300, 1200)))

    def cost(params):
        sim = simulate(make(params), track)
        time_gap = (sim["lap_time"] - real["lap_time"]) / real["lap_time"] * 100
        return speed_error(sim, real) + 4.0 * time_gap ** 2

    best = None
    for wing in (0.2, 0.5, 0.8):                     # a few starting points, keep the best
        result = minimize(cost, [wing, base.grip, base.power_kw], method="Nelder-Mead",
                          options={"xatol": 1e-3, "fatol": 1e-3, "maxiter": 160,
                                   "initial_simplex": [[wing, base.grip, base.power_kw],
                                                       [wing + 0.25, base.grip, base.power_kw],
                                                       [wing, base.grip + 0.25, base.power_kw],
                                                       [wing, base.grip, base.power_kw + 120]]})
        if best is None or result.fun < best.fun:
            best = result
    car = make(best.x)
    sim = simulate(car, track)
    return car, sim, real, track


# ---------- calibration files ----------

def load_calibration():
    if CALIBRATION_FILE.exists():
        return json.loads(CALIBRATION_FILE.read_text())
    return {}


def calibrated_car(folder, calibration=None):
    """The calibrated car for one prepared race, or the default car if it isn't calibrated."""
    entry = (calibration if calibration is not None else load_calibration()).get(folder)
    if not entry:
        return Car()
    fields = Car.__dataclass_fields__
    return Car(**{k: v for k, v in entry["car"].items() if k in fields})


def calibrate(folder, calibration):
    track_df = pd.read_parquet(RACES_DIR / folder / "track.parquet")
    problem = track_problem(track_df)
    car, sim, real, track = fit(track_df)
    rmse = speed_error(sim, real)
    if not problem and rmse > MAX_RMSE:
        problem = f"the simulated speed is off by {rmse:.0f} km/h on average"
    calibration[folder] = {
        "car": {k: round(v, 4) for k, v in asdict(car).items()},
        "sim_lap": round(sim["lap_time"], 3),
        "real_lap": round(real["lap_time"], 3),
        "speed_rmse_kmh": round(rmse, 2),
        "length_m": round(track.length, 1),
        "air_density": round(track.rho, 4),
        "usable": not problem,
        "problem": problem,
    }
    return calibration[folder]


def track_problem(track_df):
    """A reason this lap's position data can't be trusted, or '' if it looks fine.

    OpenF1 positions sometimes freeze for a few seconds and then jump (2026 Hungary), which
    cuts corners off the track. A car at 340 km/h covers about 25 m between samples, so a gap
    of more than MAX_GAP metres means points are missing.
    """
    xy = track_df[["x", "y"]].to_numpy(dtype=float) / 10
    steps = np.hypot(*np.diff(xy, axis=0).T)
    if steps.max() > MAX_GAP:
        return f"the position data jumps {steps.max():.0f} m at one point"
    closing = float(np.hypot(*(xy[-1] - xy[0])))
    if closing > MAX_GAP:
        return f"the lap doesn't close up (the ends are {closing:.0f} m apart)"
    return ""


def save_calibration(calibration):
    CALIBRATION_FILE.parent.mkdir(parents=True, exist_ok=True)
    CALIBRATION_FILE.write_text(json.dumps(dict(sorted(calibration.items())), indent=1))


def main(args):
    folders = sorted(p.name for p in RACES_DIR.glob("*_*") if (p / "track.parquet").exists())
    calibration = load_calibration()
    if args and args[0] == "--all":
        todo = folders
    elif args and args[0] == "--missing":
        todo = [f for f in folders if f not in calibration]
    elif len(args) == 2:
        todo = [f"{int(args[0])}_{int(args[1]):02d}"]
    else:
        print(__doc__)
        return
    for folder in todo:
        entry = calibrate(folder, calibration)
        c = entry["car"]
        print(f"{folder}: sim {entry['sim_lap']:.3f}s vs real {entry['real_lap']:.3f}s, "
              f"speed off by {entry['speed_rmse_kmh']:.1f} km/h on average | wing {c['wing']:.2f}, "
              f"grip {c['grip']:.2f}, power {c['power_kw']:.0f} kW, air {entry['air_density']:.3f}"
              + (f"  NOT USED: {entry['problem']}" if entry["problem"] else ""))
    save_calibration(calibration)


if __name__ == "__main__":
    main(sys.argv[1:])
