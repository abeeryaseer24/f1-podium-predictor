"""Tyre physics for the Tyre Physics page and the Academy: teaching models of how a tyre grips.

THE MAGIC FORMULA (Pacejka). The force a tyre makes as it slips:
    F = D sin(C atan(B x - E (B x - atan(B x))))
  x = slip angle (cornering) or slip ratio (braking/driving)
  D = peak force (grip x load), C = shape, B = stiffness, E = curvature near the peak
Force rises almost in a straight line with small slip, peaks, then falls away as the tyre slides.

LOAD SENSITIVITY. Grip per newton falls as the load rises:  mu = mu0 x (Fz / Fz0)^(-k)

COMBINED SLIP (friction ellipse). A tyre braking hard has less left for cornering:
    (Fx / Fx_max)^2 + (Fy / Fy_max)^2 <= 1

TEMPERATURE (one-node model). The tread heats from the sliding power it absorbs and cools to
the air and track. Grip is best inside a window and falls off either side:
    m c dT/dt = a x sliding power - h (T - T_air)
    grip factor = exp(-((T - T_opt) / width)^2)

The real g-g diagram comes from the race's fastest lap: longitudinal g from how fast the speed
changes, lateral g from speed^2 x the curvature of the track (lapsim.build_track).

All numbers are typical published values for racing slicks, not Pirelli data.

Test from the terminal:
  python src/tyre_physics.py
"""
import numpy as np

import lapsim

# Typical magic-formula shape for a racing slick (lateral), per unit of peak force
B_LAT, C_LAT, E_LAT = 14.0, 1.65, 0.1        # x in radians: peak near 6 degrees
B_LONG, C_LONG, E_LONG = 14.0, 1.65, 0.3     # x as slip ratio: peak near 10 %
FZ0 = 2000.0                                 # N, reference load on one tyre (car weight / 4)


def magic(x, D, B, C, E):
    """Pacejka's magic formula."""
    bx = B * np.asarray(x, dtype=float)
    return D * np.sin(C * np.arctan(bx - E * (bx - np.arctan(bx))))


def mu_at(load, mu0=1.7, k=0.12, fz0=FZ0):
    """Friction coefficient at a given vertical load (load sensitivity)."""
    return mu0 * np.power(np.maximum(load, 1.0) / fz0, -k)


def lateral_force(slip_deg, load, mu0=1.7, k=0.12, B=B_LAT, C=C_LAT, E=E_LAT):
    D = mu_at(load, mu0, k) * load
    return magic(np.radians(slip_deg), D, B, C, E)


def longitudinal_force(slip_ratio, load, mu0=1.7, k=0.12, B=B_LONG, C=C_LONG, E=E_LONG):
    D = mu_at(load, mu0, k) * load
    return magic(slip_ratio, D, B, C, E)


def peak_slip(B, C, E, lo=0.0, hi=0.6, n=4000):
    """Where the magic formula peaks (in its own x units)."""
    x = np.linspace(lo, hi, n)
    return float(x[np.argmax(magic(x, 1.0, B, C, E))])


def ellipse(fx_max, fy_max, n=181):
    """The friction ellipse: (Fx, Fy) pairs on the limit."""
    a = np.linspace(0, 2 * np.pi, n)
    return fx_max * np.cos(a), fy_max * np.sin(a)


# ---------- temperature ----------

def stint_temperature(laps=25, push=1.0, t_air=25.0, t_start=60.0, t_opt=100.0, width=30.0,
                      heat=1.0, cool=1.0, lap_time=90.0, steps_per_lap=90):
    """A toy stint: tread temperature and grip factor lap by lap.

    push  = how hard the driver uses the tyre (1 = on the limit everywhere, 0.8 = managing)
    heat, cool = scale the heating and cooling (a hot track, a cold day, a kinder compound)
    Returns dict of arrays per lap: temperature (°C, lap average), grip factor (0-1), wear (0-1).
    """
    dt = lap_time / steps_per_lap
    T = t_start
    wear = 0.0
    out_t, out_g, out_w = [], [], []
    # Sliding power over a lap: high in corners and braking, low on straights (a fixed pattern)
    pattern = 0.35 + 0.65 * np.abs(np.sin(np.linspace(0, 6 * np.pi, steps_per_lap)))
    for _ in range(laps):
        temps = []
        for p in pattern:
            grip = np.exp(-((T - t_opt) / width) ** 2)
            sliding = heat * 7.6 * (push ** 3) * p * (1.05 - 0.1 * grip)   # less grip -> more sliding
            T += dt * (sliding - cool * 0.06 * (T - t_air)) / 4.0
            wear += dt * 1.1e-4 * (push ** 2) * p * (1 + max(0.0, T - t_opt - width) / 15)
            temps.append(T)
        T_lap = float(np.mean(temps))
        out_t.append(T_lap)
        out_g.append(float(np.exp(-((T_lap - t_opt) / width) ** 2)) * (1 - 0.35 * min(wear, 1.0) ** 2))
        out_w.append(min(wear, 1.0))
    return {"lap": np.arange(1, laps + 1), "temperature": np.array(out_t), "grip": np.array(out_g),
            "wear": np.array(out_w)}


# ---------- real g-g ----------

def real_gg(track_df, track=None):
    """Lateral and longitudinal g at every point of the real fastest lap."""
    track = track or lapsim.build_track(track_df)
    real = lapsim.real_trace(track_df, track)
    v = real["speed_kmh"] / 3.6
    ds = track.length / len(track.s)
    # Smooth the speed a little before differentiating: the samples are about 4 per second
    v_s = lapsim._circular_smooth(v, sigma_points=3)
    long_g = (np.roll(v_s, -1) ** 2 - np.roll(v_s, 1) ** 2) / (4 * ds) / lapsim.G
    lat_g = v_s ** 2 * track.curvature / lapsim.G
    return {"s": track.s, "lat_g": lat_g, "long_g": long_g, "speed_kmh": real["speed_kmh"]}


if __name__ == "__main__":
    print(f"Lateral peak at {np.degrees(peak_slip(B_LAT, C_LAT, E_LAT)):.1f} degrees, "
          f"longitudinal peak at {peak_slip(B_LONG, C_LONG, E_LONG):.0%} slip")
    for load in (1000, 2000, 4000, 8000):
        print(f"  load {load} N: mu {mu_at(load):.2f}, peak lateral force {lateral_force(6, load):.0f} N")
    s = stint_temperature(push=1.0)
    m = stint_temperature(push=0.85)
    print(f"Push: grip lap 5 {s['grip'][4]:.2f}, lap 25 {s['grip'][-1]:.2f} | "
          f"Manage: lap 5 {m['grip'][4]:.2f}, lap 25 {m['grip'][-1]:.2f}")
