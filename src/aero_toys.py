"""Two small aerodynamics models for the Simulator pages: porpoising and dirty air.

PORPOISING. A ground-effect floor makes more downforce the closer it runs to the track, until
the air underneath stalls. The car is a mass on its springs, pushed down by that downforce:
    m z'' = -k (z - z0) - c z' - (downforce(h) - downforce at rest)
As speed rises the car sinks; once the floor reaches its stall height the downforce collapses,
the car springs up, the flow reattaches (a little higher: hysteresis), the car is sucked down
again... a self-sustaining bounce. The flow takes a few hundredths of a second to stall and
recover, which is what keeps the cycle going. Stiffer springs, more damping or a higher ride
height stop it, and each costs downforce somewhere.

DIRTY AIR. Behind another car, the turbulent wake costs downforce. The FIA published the loss
when it set the 2022 rules: a 2021 car kept about 65 % of its downforce three car-lengths
(about 20 m) behind and 53 % one length (about 10 m) behind; the 2022 design targets were
96 % and 82 %. Between and beyond those points the loss is fitted with a smooth exponential.
The same wake cuts drag on the straights (the tow), which this applies more gently.

Both are teaching models with illustrative constants.
"""
import numpy as np

G = 9.81

# ---------- porpoising ----------


def floor_downforce(h_mm, speed_ms, rho=1.2, cza0=4.0, sensitivity=1.0, stall_mm=18.0, stalled=False):
    """Floor downforce (N) at ride height h (mm). Rises as the floor gets closer; collapses when stalled."""
    gain = 1.0 + sensitivity * 0.025 * (35.0 - h_mm)           # +2.5 % per mm below 35 mm (illustrative)
    gain = max(gain, 0.4)
    if stalled:
        gain *= 0.55                                            # most of the floor's suction is lost
    return 0.5 * rho * cza0 * gain * speed_ms ** 2


def porpoise(static_mm=35.0, spring_kn_m=900.0, damper_kns_m=15.0, sensitivity=1.0, speed_from=200.0,
             speed_to=330.0, seconds=8.0, mass=800.0, stall_mm=18.0, reattach_mm=24.0, lag_s=0.03):
    """Accelerate down a straight; return time, speed, ride height, vertical g and when bouncing starts."""
    dt = 0.0005
    n = int(seconds / dt)
    k, c = spring_kn_m * 1000, damper_kns_m * 1000
    # Start settled at the first speed: find where the springs hold up the downforce
    z, vz = 0.0, 0.0                      # suspension compression (m), positive = lower
    for _ in range(200):
        z = 0.5 * z + 0.5 * floor_downforce(static_mm - z * 1000, speed_from / 3.6, sensitivity=sensitivity) / k
        if static_mm - z * 1000 < stall_mm + 1:
            z = (static_mm - stall_mm - 1) / 1000
            break
    flow = 1.0                            # 1 = attached, 0 = fully stalled (lags the true state)
    stalled = False
    t = np.arange(n) * dt
    speed = np.linspace(speed_from, speed_to, n) / 3.6
    out_h, out_g, out_f = np.zeros(n), np.zeros(n), np.zeros(n)
    rest = floor_downforce(static_mm, 0.0)          # zero: at rest there is no downforce
    for i in range(n):
        h = static_mm - z * 1000
        if not stalled and h < stall_mm:
            stalled = True
        elif stalled and h > reattach_mm:
            stalled = False
        target = 0.0 if stalled else 1.0
        flow += (target - flow) * dt / lag_s
        f_att = floor_downforce(h, speed[i], sensitivity=sensitivity)
        f_st = floor_downforce(h, speed[i], sensitivity=sensitivity, stalled=True)
        f = f_st + (f_att - f_st) * flow - rest
        a = (f - k * z - c * vz) / mass
        vz += a * dt
        z += vz * dt
        if static_mm - z * 1000 < 2.0:                  # bottoming out on the plank
            z = (static_mm - 2.0) / 1000
            vz = min(vz, 0.0)
        out_h[i] = static_mm - z * 1000
        out_g[i] = a / G
        out_f[i] = f
    # Bouncing: peak-to-peak ride height over 0.25 s windows above 4 mm
    win = int(0.25 / dt)
    swing = np.array([out_h[j:j + win].max() - out_h[j:j + win].min() for j in range(0, n - win, win)])
    starts = np.flatnonzero(swing > 4.0)
    onset = float(speed[starts[0] * win] * 3.6) if len(starts) else None
    return {"t": t, "speed_kmh": speed * 3.6, "height_mm": out_h, "vertical_g": out_g, "onset_kmh": onset,
            "max_swing_mm": float(swing.max()) if len(swing) else 0.0,
            "downforce_n": out_f, "mean_downforce_n": float(out_f.mean())}


# ---------- dirty air ----------

FIA_POINTS = {   # metres behind -> share of downforce kept (FIA, 2021 vs 2022 targets)
    "2017–2021 cars": {10: 0.53, 20: 0.65},
    "2022+ cars": {10: 0.82, 20: 0.96},
}


def kept(gap_m, era):
    """Share of downforce kept gap_m metres behind another car (exponential through the FIA points)."""
    pts = FIA_POINTS[era]
    l10, l20 = 1 - pts[10], 1 - pts[20]
    decay = 10 / np.log(l10 / l20)                 # metres for the loss to fall by e
    amp = l10 * np.exp(10 / decay)
    return 1 - amp * np.exp(-np.asarray(gap_m, dtype=float) / decay)


def tow(gap_m):
    """Share of drag left in the slipstream (illustrative: up to about a quarter less right behind)."""
    return 1 - 0.25 * np.exp(-np.asarray(gap_m, dtype=float) / 25.0)
