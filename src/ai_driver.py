"""AI driver: a driver learned from real laps, driving the lap simulator's car.

THE IDEA. The lap simulator (lapsim.py) drives every point of a lap exactly at the car's limit:
it brakes at the last possible metre, takes every corner at the tyres' exact limit and is back on
full power the instant it can. No human drives like that. Real drivers give some corners a
margin and attack others harder than a simple tyre model thinks possible, lift on fast kinks,
and brake and accelerate in their own shape.

THE DATA. Each prepared race has its fastest lap at about four samples a second (track.parquet)
and a calibrated car for the simulator. At every 4 m of that lap we describe the SITUATION from
the simulator's point of view (its speed, the tyres' corner limit, whether it's braking,
cornering or accelerating, how far to the next braking zone, the corner speeds coming up over
the next 25-300 m, curvature, slope, g-forces), and the CHOICE the real driver made: their speed
there as a share of the simulator's.

THE MODEL. A gradient-boosted tree model (scikit-learn) learns that choice from the situation.
That is behaviour cloning, the simplest kind of imitation learning: copy what experts do in each
situation. (Copying the pedals directly was tried first; small errors compounded round the lap
and the car ended up seconds slow. Copying the speed choice and letting the physics produce the
pedals is the stable version.)

DRIVING. The learned speed choice becomes the driver's target at every point, and the lap
simulator's physics turn it into a lap the car can actually do: it can only accelerate as hard
as the engine and tyres allow, and must start braking early enough to make the next target.

THE HONEST TEST. Grouped by circuit: the driver is trained without a circuit, then drives it.
Scored on how closely its speed trace follows the real lap, against the simulator's own trace.

  python src/ai_driver.py --train       build the data, cross-validate, train, save every lap
  python src/ai_driver.py --missing     drive new races (the pipeline runs this)
  python src/ai_driver.py 2025 10       drive one race with the saved driver and print the result
"""
import json
import math
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lapsim as L

ROOT = Path(__file__).resolve().parent.parent
MODEL_FILE = ROOT / "models" / "ai_driver.joblib"
REPORT_FILE = ROOT / "data" / "processed" / "ai_driver.json"
LAPS_DIR = ROOT / "data" / "processed" / "ai_driver"

LOOK = (25, 50, 100, 200, 300)        # m ahead for the corner-speed preview
FEATURES = (["v_sim", "v_corner", "at_corner_limit", "braking", "cornering", "to_brake", "since_brake",
             "curv", "curv_ahead", "slope", "long_g", "lat_g", "vmax_ahead", "vmin_behind"]
            + [f"vmin_{d}" for d in LOOK])


def _rolling(values, steps, fn, ahead=True):
    """fn over the next (or previous) `steps` points of a lap, wrapping round."""
    n = len(values)
    padded = np.r_[values, values[:steps]] if ahead else np.r_[values[-steps:], values]
    win = np.lib.stride_tricks.sliding_window_view(padded, steps + 1)
    return fn(win, axis=1)[:n]


def _dist_to(mask, ds, ahead=True):
    """Metres to the next (or since the last) True point, wrapping round the lap."""
    n = len(mask)
    idx = np.flatnonzero(mask)
    if not len(idx):
        return np.full(n, n * ds)
    pos = np.arange(n)
    if ahead:
        nxt = idx[np.searchsorted(idx, pos) % len(idx)]
        return ((nxt - pos) % n) * ds
    prv = idx[(np.searchsorted(idx, pos, side="right") - 1) % len(idx)]
    return ((pos - prv) % n) * ds


def situation(car, track, sim=None):
    """The table of features at every point of the lap (one row per 4 m)."""
    sim = sim or L.simulate(car, track)
    n = len(track.s)
    ds = track.length / n
    vc = np.minimum(L.corner_limit(car, track), 120.0)
    mode = sim["mode"]
    brake_start = (mode == "brake") & (np.roll(mode, 1) != "brake")
    brake_end = (mode != "brake") & (np.roll(mode, 1) == "brake")
    kappa = np.abs(track.curvature)
    out = {
        "v_sim": sim["speed_kmh"], "v_corner": vc * 3.6, "at_corner_limit": sim["speed"] / vc,
        "braking": (mode == "brake").astype(float), "cornering": (mode == "corner").astype(float),
        "to_brake": np.minimum(_dist_to(brake_start, ds), 1500),
        "since_brake": np.minimum(_dist_to(brake_end, ds, False), 1500),
        "curv": kappa * 1000, "curv_ahead": _rolling(kappa, int(50 / ds), np.mean) * 1000,
        "slope": track.slope, "long_g": sim["long_g"], "lat_g": sim["lat_g"],
        "vmax_ahead": _rolling(sim["speed_kmh"], int(300 / ds), np.max),
        "vmin_behind": _rolling(sim["speed_kmh"], int(100 / ds), np.min, ahead=False),
    }
    for d in LOOK:
        out[f"vmin_{d}"] = _rolling(vc * 3.6, max(1, int(d / ds)), np.min)
    return pd.DataFrame(out)[FEATURES], sim


# ---------- driving a speed plan ----------

def drive_plan(car, track, target):
    """The lap simulator's physics, driving to a target speed (m/s) at every point instead of the
    tyres' corner limit: accelerate as hard as possible, brake as late as possible, never above
    the target."""
    n = len(track.s)
    ds = track.length / n
    m, rho = car.mass, track.rho
    q_down, q_drag = 0.5 * rho * car.cza, 0.5 * rho * car.cxa
    power = car.power_kw * 1000.0
    kappa = np.abs(track.curvature).tolist()
    slope = track.slope.tolist()
    vc = np.asarray(target, float).tolist()
    n0_ls = (m * L.G) ** car.load_sensitivity
    one_minus = 1 - car.load_sensitivity

    def long_grip(v, i):
        normal = m * L.G + q_down * v * v
        grip = car.grip * n0_ls * normal ** one_minus
        left = 1 - (m * v * v * kappa[i] / grip) ** 2
        return (grip * math.sqrt(left) if left > 0 else 0.1 * grip), normal

    start = int(np.argmin(target))
    fwd, bwd = [0.0] * n, [0.0] * n
    v = vc[start]
    for step in range(n):
        i = (start + step) % n
        v = min(v, vc[i])
        fwd[i] = v
        g, normal = long_grip(v, i)
        a = (min(power / max(v, 1.0), g * car.rear_share) - q_drag * v * v - car.rolling * normal
             - m * L.G * slope[i]) / m
        v = math.sqrt(max(v * v + 2 * a * ds, 1.0))
    v = vc[start]
    for step in range(n):
        i = (start - step) % n
        v = min(v, vc[i], fwd[i])
        bwd[i] = v
        g, normal = long_grip(v, i)
        decel = (g + q_drag * v * v + car.rolling * normal + m * L.G * slope[i]) / m
        v = math.sqrt(max(v * v + 2 * max(decel, 0.0) * ds, 1.0))
    speed = np.minimum(fwd, bwd)
    nxt = np.roll(speed, -1)
    dt = 2 * ds / (speed + nxt)
    braking = np.array(bwd) < np.array(fwd) - 1e-6
    accelerating = (nxt > speed + 1e-3) & ~braking
    throttle = np.where(braking, 0, np.where(accelerating, 100, np.where(nxt >= speed - 1e-3, 60, 0)))
    return {"s": track.s, "speed": speed, "speed_kmh": speed * 3.6, "time": np.r_[0, np.cumsum(dt)[:-1]],
            "lap_time": float(dt.sum()), "brake": braking.astype(int), "throttle": throttle}


# ---------- training data ----------

def race_rows(folder, calibration):
    track_df = pd.read_parquet(L.RACES_DIR / folder / "track.parquet")
    track = L.build_track(track_df)
    car = L.calibrated_car(folder, calibration)
    df, sim = situation(car, track)
    real = L.real_trace(track_df, track)
    df["target"] = np.log(np.clip(real["speed_kmh"], 30, None) / np.clip(sim["speed_kmh"], 30, None))
    df["folder"] = folder
    return df


def all_rows():
    calibration = L.load_calibration()
    usable = sorted(f for f, c in calibration.items() if c.get("usable"))
    frames = []
    for f in usable:
        try:
            frames.append(race_rows(f, calibration))
        except Exception as error:
            print(f"  {f}: skipped ({error})")
    return pd.concat(frames, ignore_index=True), calibration


def circuit_of(folder):
    info = json.loads((L.RACES_DIR / folder / "info.json").read_text(encoding="utf-8"))
    return info.get("location") or info["race_name"]


# ---------- the model ----------

def fit(df):
    from sklearn.ensemble import HistGradientBoostingRegressor
    model = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.06, max_leaf_nodes=31,
                                          min_samples_leaf=60, l2_regularization=1.0, random_state=1)
    return model.fit(df[FEATURES].to_numpy(), df["target"].clip(-0.4, 0.3))


def drive(model, car, track):
    """The learned driver's lap: its speed choice at every point, made drivable by the physics."""
    feats, sim = situation(car, track)
    ratio = np.exp(L._circular_smooth(model.predict(feats.to_numpy()), sigma_points=4))
    lap = drive_plan(car, track, sim["speed"] * ratio)
    lap["sim"] = sim
    return lap


def compare(folder, model, calibration=None):
    """Drive one circuit and compare: learned driver, limit simulator, real lap."""
    calibration = calibration or L.load_calibration()
    track_df = pd.read_parquet(L.RACES_DIR / folder / "track.parquet")
    track = L.build_track(track_df)
    car = L.calibrated_car(folder, calibration)
    ai = drive(model, car, track)
    sim = ai["sim"]
    real = L.real_trace(track_df, track)

    def rmse(a):
        return float(np.sqrt(np.mean((a - real["speed_kmh"]) ** 2)))

    real_brake = real["brake"] > 50
    return {"folder": folder, "real_lap": real["lap_time"], "sim_lap": sim["lap_time"], "ai_lap": ai["lap_time"],
            "sim_rmse": rmse(sim["speed_kmh"]), "ai_rmse": rmse(ai["speed_kmh"]),
            "brake_agree": float(((ai["brake"] > 0) == real_brake).mean()),
            "sim_brake_agree": float(((sim["mode"] == "brake") == real_brake).mean())}, ai, track, real


def save_lap(folder, ai, real, track, every=2):
    """The learned driver's lap for the app: speed, throttle, brake and time every 8 m."""
    LAPS_DIR.mkdir(parents=True, exist_ok=True)
    sl = slice(None, None, every)
    out = {"s": np.round(track.s[sl], 1).tolist(), "ai_kmh": np.round(ai["speed_kmh"][sl], 1).tolist(),
           "ai_time": np.round(ai["time"][sl], 3).tolist(), "ai_lap": round(ai["lap_time"], 3),
           "ai_brake": ai["brake"][sl].astype(int).tolist(), "ai_throttle": ai["throttle"][sl].astype(int).tolist(),
           "sim_kmh": np.round(ai["sim"]["speed_kmh"][sl], 1).tolist(), "sim_lap": round(ai["sim"]["lap_time"], 3),
           "real_kmh": np.round(real["speed_kmh"][sl], 1).tolist(), "real_lap": round(real["lap_time"], 3),
           "length": round(float(track.length), 1)}
    (LAPS_DIR / f"{folder}.json").write_text(json.dumps(out), encoding="utf-8")


def train(folds=8):
    t0 = time.time()
    df, calibration = all_rows()
    df["circuit"] = df["folder"].map(circuit_of)
    print(f"{len(df):,} points from {df['folder'].nunique()} races ({time.time() - t0:.0f} s)")
    circuits = np.array(sorted(df["circuit"].unique()))
    rng = np.random.default_rng(3)
    rng.shuffle(circuits)
    results = []
    for k, test_c in enumerate(np.array_split(circuits, folds)):
        model = fit(df[~df["circuit"].isin(test_c)])
        for folder in sorted(df.loc[df["circuit"].isin(test_c), "folder"].unique()):
            r, ai, track, real = compare(folder, model, calibration)
            r["circuit"] = circuit_of(folder)
            results.append(r)
            save_lap(folder, ai, real, track)            # the app shows the driver on circuits it never saw
            print(f"  fold {k + 1}: {folder} real {r['real_lap']:.2f} sim {r['sim_lap']:.2f} ai {r['ai_lap']:.2f} "
                  f"| rmse sim {r['sim_rmse']:.1f} ai {r['ai_rmse']:.1f}", flush=True)
    res = pd.DataFrame(results)
    model = fit(df)
    MODEL_FILE.parent.mkdir(exist_ok=True)
    joblib.dump(model, MODEL_FILE)
    report = {
        "races": int(len(res)), "circuits": int(res["circuit"].nunique()),
        "ai_rmse": float(res["ai_rmse"].median()), "sim_rmse": float(res["sim_rmse"].median()),
        "closer_share": float((res["ai_rmse"] < res["sim_rmse"]).mean()),
        "ai_gap": float((res["ai_lap"] - res["real_lap"]).median()),
        "sim_gap": float((res["sim_lap"] - res["real_lap"]).median()),
        "ai_gap_abs": float((res["ai_lap"] - res["real_lap"]).abs().median()),
        "brake_agree": float(res["brake_agree"].median()), "sim_brake_agree": float(res["sim_brake_agree"].median()),
        "per_race": res.round(3).to_dict("records"), "built": time.strftime("%Y-%m-%d"),
    }
    REPORT_FILE.write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(f"Unseen circuits: speed trace off by {report['ai_rmse']:.1f} km/h (simulator {report['sim_rmse']:.1f}); "
          f"closer than the simulator on {report['closer_share']:.0%} of races; lap time off by "
          f"{report['ai_gap']:+.2f} s (median)")


def load():
    return joblib.load(MODEL_FILE)


def drive_missing():
    """Drive every calibrated race that has no saved lap yet, each with a version of the driver
    trained without that circuit, so the app never shows it on a track it learned from."""
    calibration = L.load_calibration()
    usable = sorted(f for f, c in calibration.items() if c.get("usable"))
    todo = [f for f in usable if not (LAPS_DIR / f"{f}.json").exists()]
    if not todo:
        print("Every calibrated race already has an AI lap.")
        return
    df, _ = all_rows()
    df["circuit"] = df["folder"].map(circuit_of)
    for folder in todo:
        model = fit(df[df["circuit"] != circuit_of(folder)])
        r, ai, track, real = compare(folder, model, calibration)
        save_lap(folder, ai, real, track)
        print(f"{folder}: AI {r['ai_lap']:.2f} s, real {r['real_lap']:.2f} s")


def main(args):
    if args and args[0] == "--train":
        train()
        return
    if args and args[0] == "--missing":
        drive_missing()
        return
    folder = f"{int(args[0])}_{int(args[1]):02d}"
    r, *_ = compare(folder, load())
    print(json.dumps(r, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
