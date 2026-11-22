"""Power unit and energy model: the lap simulator with a battery.

lapsim.py gives the car a fixed power. Here the power comes from two sources:
  combustion engine (ICE)  always available, ice_kw
  electric motor (MGU-K)   up to k_kw, but only while the battery has energy

THE BATTERY. The motor harvests energy under braking (up to k_kw, and only as much as the
braking power) and spends it on the straights. The state of charge is tracked point by point
round the lap. When it runs out, the motor stops helping: the car "clips", losing speed at the
end of a straight even at full throttle.

TWO WAYS TO RUN A LAP
  race        the lap must pay for itself: the battery ends where it started
  qualifying  start with a full battery and use all of it

DEPLOYMENT. The visitor chooses on which straights to deploy. Everywhere else the car uses the
engine alone. Harvesting happens in every braking zone, up to the per-lap harvest limit.

ACTIVE AERO (2026). In straight mode the wings flatten and drag falls (illustratively by a
third); the car switches back to corner mode wherever it needs grip.

The numbers for each era are rounded public figures, not team data:
  2026: ICE ~400 kW, MGU-K 350 kW, harvest up to ~8.5 MJ a lap, a ~4 MJ battery window
  2022-25: ICE ~560 kW, MGU-K 120 kW, 4 MJ deploy limit a lap, plus the MGU-H recharging
           from the turbo at full throttle (modelled as a steady 80 kW)

It is a teaching model: no gearbox, no thermal limits, no clever harvesting on the throttle
("super clipping"), and every straight is either all-deploy or none.

Test from the terminal:
  python src/energy.py 2025 16
"""
import math
import sys
from dataclasses import dataclass, replace

import numpy as np

import lapsim

ERAS = {
    "2026 rules": {"ice_kw": 400.0, "k_kw": 350.0, "harvest_mj": 8.5, "window_mj": 4.0, "deploy_mj": 99.0,
                   "active_aero": True, "h_kw": 0.0},
    "2022–2025 rules": {"ice_kw": 560.0, "k_kw": 120.0, "harvest_mj": 6.0, "window_mj": 4.0, "deploy_mj": 4.0,
                        "active_aero": False, "h_kw": 80.0},
}
STRAIGHT_DRAG = 0.67          # drag in active-aero straight mode, as a share of corner mode (illustrative)
MIN_STRAIGHT = 150            # m: a stretch of full throttle at least this long counts as a straight


@dataclass(frozen=True)
class PowerUnit:
    ice_kw: float = 400.0
    k_kw: float = 350.0
    harvest_mj: float = 8.5      # most the motor may harvest in one lap
    window_mj: float = 4.0       # usable battery window
    deploy_mj: float = 99.0      # most the motor may deploy in one lap (99 = no separate limit)
    active_aero: bool = True
    h_kw: float = 0.0            # MGU-H: charging from the turbo at full throttle (2014-2025 only)


def straights(car, track):
    """Full-throttle stretches of the plain lap: [(start index, end index, start m, end m)]."""
    sim = lapsim.simulate(car, track)
    on = sim["mode"] == "throttle"
    n, ds = len(on), track.length / len(on)
    out, i = [], 0
    while i < n:
        if on[i]:
            j = i
            while j + 1 < n and on[j + 1]:
                j += 1
            if (j - i + 1) * ds >= MIN_STRAIGHT:
                out.append((i, j, track.s[i], track.s[j]))
            i = j + 1
        else:
            i += 1
    return out


def simulate(car, track, pu, deploy_on=None, mode="race", iterations=4):
    """One lap with the battery. deploy_on = one True/False per straight (None = deploy everywhere)."""
    n = len(track.s)
    ds = track.length / n
    zones = straights(car, track)
    deploy = np.zeros(n, dtype=bool)
    straight_mask = np.zeros(n, dtype=bool)
    for k, (i, j, _, _) in enumerate(zones):
        straight_mask[i:j + 1] = True
        if deploy_on is None or (k < len(deploy_on) and deploy_on[k]):
            deploy[i:j + 1] = True

    m, rho = car.mass, track.rho
    q_down = 0.5 * rho * car.cza
    drag_corner, drag_straight = 0.5 * rho * car.cxa, 0.5 * rho * car.cxa * (STRAIGHT_DRAG if pu.active_aero else 1)
    kappa, slope = np.abs(track.curvature), track.slope
    v_corner = lapsim.corner_limit(car, track)
    n0_ls = (m * lapsim.G) ** car.load_sensitivity

    def long_grip(v, i):
        normal = m * lapsim.G + q_down * v * v
        grip = car.grip * n0_ls * normal ** (1 - car.load_sensitivity)
        lat = m * v * v * kappa[i]
        left = 1 - (lat / grip) ** 2
        return (grip * math.sqrt(left) if left > 0 else 0.0), normal

    start = int(np.argmin(v_corner))
    budget = pu.window_mj * 1e6 if mode == "qualifying" else 0.0       # energy available at the start
    k_w, ice_w = pu.k_kw * 1000, pu.ice_kw * 1000
    harvest_cap, deploy_cap = pu.harvest_mj * 1e6, pu.deploy_mj * 1e6
    harvest_at = np.zeros(n)                       # J harvested at each point (from the last iteration)
    deploy_scale = 1.0

    for _ in range(iterations):
        # Forward pass, with the battery
        fwd = np.zeros(n)
        soc = np.zeros(n)
        motor = np.zeros(n)
        charge = budget
        used = 0.0
        turbo_total = 0.0
        v = v_corner[start]
        for step in range(n):
            i = (start + step) % n
            v = min(v, v_corner[i])
            fwd[i] = v
            soc[i] = charge
            dt = ds / max(v, 1.0)
            turbo = pu.h_kw * 1000 * dt if straight_mask[i] else 0.0      # MGU-H recharging on the throttle
            charge = min(charge + harvest_at[i] + turbo, pu.window_mj * 1e6 + budget)
            turbo_total += turbo
            grip_long, normal = long_grip(v, i)
            want_k = k_w * deploy_scale if deploy[i] else 0.0
            p_k = min(want_k, max(charge, 0.0) / dt, max(deploy_cap - used, 0.0) / dt)
            drive = min((ice_w + p_k) / max(v, 1.0), grip_long * car.rear_share)
            if p_k > 0 and drive < (ice_w + p_k) / max(v, 1.0):           # grip-limited: motor not fully used
                p_k = max(0.0, drive * v - ice_w)
            motor[i] = p_k
            charge -= p_k * dt
            used += p_k * dt
            drag = drag_straight if straight_mask[i] else drag_corner
            a = (drive - drag * v * v - car.rolling * normal - m * lapsim.G * slope[i]) / m
            v = math.sqrt(max(v * v + 2 * a * ds, 1.0))

        # Backward pass: braking, and how much the motor can harvest there
        bwd = np.zeros(n)
        new_harvest = np.zeros(n)
        v = v_corner[start]
        for step in range(n):
            i = (start - step) % n
            v = min(v, v_corner[i], fwd[i])
            bwd[i] = v
            grip_long, normal = long_grip(v, i)
            decel = (grip_long + drag_corner * v * v + car.rolling * normal + m * lapsim.G * slope[i]) / m
            if bwd[i] < fwd[i] - 1e-6:                                    # braking here
                braking_power = grip_long * v
                new_harvest[i] = min(k_w, braking_power) * ds / max(v, 1.0)
            v = math.sqrt(max(v * v + 2 * max(decel, 0.0) * ds, 1.0))
        speed = np.minimum(fwd, bwd)
        braking = bwd < fwd - 1e-6
        new_harvest[~braking] = 0.0
        total = new_harvest.sum()
        if total > harvest_cap:
            new_harvest *= harvest_cap / total
        harvest_at = new_harvest

        # Race mode: deployment can't exceed what the lap harvests. Scale it back if it does.
        harvested = harvest_at.sum() + turbo_total
        deployed = float(np.sum(motor * ds / np.maximum(fwd, 1.0)))
        if mode == "race" and deployed > harvested + 1:
            deploy_scale *= max(0.05, harvested / deployed)

    nxt = np.roll(speed, -1)
    dt = 2 * ds / (speed + nxt)
    clipping = deploy & (motor < k_w * deploy_scale * 0.98) & (speed >= fwd - 1e-6) & ~braking
    phase = np.where(braking, "harvest", np.where(motor > 1000, "deploy", np.where(clipping, "clip", "engine")))
    return {
        "s": track.s, "speed_kmh": speed * 3.6, "time": np.r_[0, np.cumsum(dt)[:-1]], "lap_time": float(dt.sum()),
        "soc_mj": soc / 1e6, "motor_kw": motor / 1000, "phase": phase,
        "harvested_mj": float((harvest_at.sum() + turbo_total) / 1e6),
        "turbo_mj": float(turbo_total / 1e6),
        "deployed_mj": float(np.sum(motor * ds / np.maximum(fwd, 1.0)) / 1e6),
        "deploy_scale": deploy_scale, "straights": zones,
        "clip_share": float(clipping.sum() / max(deploy.sum(), 1)),
    }


def car_for(folder, era):
    """The circuit's calibrated chassis, with the chosen era's power unit.

    The calibrated power is effective power at the wheels for a 2022-25 car (engine plus a
    120 kW motor), so each era is scaled from it: that keeps the chassis and the power unit
    consistent with the real lap the calibration was fitted to.
    """
    base = lapsim.calibrated_car(folder)
    e = dict(ERAS[era])
    ref = ERAS["2022–2025 rules"]
    ice_eff = max(base.power_kw - ref["k_kw"], 200.0)            # effective engine power, 2022-25
    e["ice_kw"] = ice_eff * e["ice_kw"] / ref["ice_kw"]
    pu = PowerUnit(**e)
    return replace(base, power_kw=e["ice_kw"] + e["k_kw"]), pu


if __name__ == "__main__":
    import pandas as pd
    folder = f"{int(sys.argv[1])}_{int(sys.argv[2]):02d}" if len(sys.argv) == 3 else "2025_16"
    track = lapsim.build_track(pd.read_parquet(lapsim.RACES_DIR / folder / "track.parquet"))
    for era in ERAS:
        car, pu = car_for(folder, era)
        for mode in ("race", "qualifying"):
            r = simulate(car, track, pu, mode=mode)
            print(f"{era:16s} {mode:10s} lap {r['lap_time']:.3f}s  harvested {r['harvested_mj']:.2f} MJ  "
                  f"deployed {r['deployed_mj']:.2f} MJ  top {r['speed_kmh'].max():.0f} km/h  "
                  f"straights {len(r['straights'])}  clipping {r['clip_share']:.0%} of deploy zones")
