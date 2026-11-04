"""Quick check: does OpenF1 give us what the 3D pages need, for free? (2023 onwards)

Usage:  python src/openf1_check.py                 (the latest finished 2026 race)
        python src/openf1_check.py 2025 Monaco     (a season and a place name)
"""
import sys
from datetime import datetime, timezone

import requests

BASE = "https://api.openf1.org/v1"


def get(endpoint, **params):
    """Returns (rows, problem). problem is None when it worked."""
    try:
        r = requests.get(f"{BASE}/{endpoint}", params=params, timeout=120)
    except requests.RequestException as error:
        return [], f"network error: {error}"
    if r.status_code in (401, 403):
        return [], f"LOCKED (HTTP {r.status_code}, needs a login)"
    if r.status_code != 200:
        return [], f"HTTP {r.status_code}"
    data = r.json()
    if isinstance(data, dict):               # an error message instead of rows
        return [], str(data)[:120]
    return data, None


def report(name, rows, problem, detail=""):
    if problem:
        print(f"  MISSING  {name}  ({problem})")
    elif not rows:
        print(f"  MISSING  {name}  (no data)")
    else:
        print(f"  OK       {name}  {detail}")


year = int(sys.argv[1]) if len(sys.argv) > 1 else 2026
place = sys.argv[2] if len(sys.argv) > 2 else None

sessions, problem = get("sessions", year=year, session_name="Race")
if problem or not sessions:
    print("Could not list races:", problem or "none found")
    sys.exit(1)

now = datetime.now(timezone.utc).isoformat()
finished = [s for s in sessions if s["date_start"] < now]
if place:
    finished = [s for s in finished
                if place.lower() in f"{s.get('location', '')} {s.get('country_name', '')}".lower()]
if not finished:
    print("No finished race found.")
    sys.exit(1)

race = finished[-1]
key = race["session_key"]
print(f"\n{race.get('location')} ({race.get('country_name')}) {year}\n")

drivers, p = get("drivers", session_key=key)
report("Drivers, team colours, full names", drivers, p,
       f"({len(drivers)} drivers, e.g. {drivers[0].get('full_name')}, "
       f"colour #{drivers[0].get('team_colour')})" if drivers else "")

laps, p = get("laps", session_key=key)
report("Lap times", laps, p, f"({len(laps)} laps)")

stints, p = get("stints", session_key=key)
compounds = sorted({s.get("compound") for s in stints if s.get("compound")})
report("Tyre compounds and stints", stints, p, f"({len(stints)} stints, {compounds})")

pits, p = get("pit", session_key=key)
report("Pit stops", pits, p, f"({len(pits)} stops)")

positions, p = get("position", session_key=key)
report("Positions during the race", positions, p, f"({len(positions)} updates)")

messages, p = get("race_control", session_key=key)
safety = sum("SAFETY CAR" in (m.get("message") or "").upper() for m in messages)
report("Race control (flags, safety car)", messages, p,
       f"({len(messages)} messages, {safety} about the safety car)")

weather, p = get("weather", session_key=key)
rain = any(w.get("rainfall") for w in weather)
report("Weather", weather, p, f"({len(weather)} readings, rain: {rain})")

if drivers:
    number = drivers[0]["driver_number"]
    location, p = get("location", session_key=key, driver_number=number)
    report("Car position on track (x, y, z)", location, p,
           f"({len(location)} points for car {number})")
    car, p = get("car_data", session_key=key, driver_number=number)
    report("Car telemetry (speed, throttle, brake, gear)", car, p,
           f"({len(car)} points for car {number})")

practice, p = get("sessions", meeting_key=race["meeting_key"], session_name="Practice 2")
if practice:
    practice_laps, p = get("laps", session_key=practice[0]["session_key"])
    report("Practice (FP2) lap times", practice_laps, p, f"({len(practice_laps)} laps)")
else:
    print("  --       No FP2 at this event (probably a sprint weekend)")