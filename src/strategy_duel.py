"""Strategy Duel: two players run the same driver's strategy in the same real race, at the same time.

A host picks a race and a driver and gets a room code; a friend joins with the code (or the host plays our
strategist). The race runs in steps of STEP laps. At each step both players lock a call for the next
stretch: stay out, or box at the end of a chosen lap for a chosen tyre. When both have locked, the race
moves on and both see the gap. The car is the same for both, and the maths is the Race Engineer game's
(engineer.simulate): the real driver's pace with the tyres taken out, plus what your tyres cost and your
stops (cheaper under a safety car). The rules ask for two different dry compounds; a car that never
changes compound is disqualified.

STORAGE. Every action is one inserted row, never an update, so the two players can't overwrite each
other: the Supabase table `duel_moves` (server-side key, like Beat the AI), or a local JSON file.
    create table duel_moves (id bigint generated always as identity primary key, room text not null,
      player text not null, kind text not null, data jsonb not null, created_at timestamptz default now());
    alter table duel_moves enable row level security;
kinds: "create" {folder, driver, bot}, "join" {}, "call" {step, box: lap or null, tyre}, "name" {nickname}
"""
import json
import random
from datetime import datetime, timezone
from pathlib import Path

import picks

ROOT = Path(__file__).resolve().parent.parent
LOCAL_FILE = ROOT / "data" / "duel_moves_local.json"
TABLE = "duel_moves"
STEP = 5
BOT = "STRATEGIST"
LETTERS = "ABCDEFGHJKMNPQRSTUVWXYZ"


def new_room():
    return "".join(random.choice(LETTERS) for _ in range(4))


# ---------- storage ----------

def _read_local():
    return json.loads(LOCAL_FILE.read_text()) if LOCAL_FILE.exists() else []


def moves(room):
    conf = picks._supabase()
    if conf:
        import requests
        url, key = conf
        r = requests.get(f"{url}/rest/v1/{TABLE}", params={"room": f"eq.{room}", "select": "*", "order": "id.asc"},
                         headers=picks._headers(key), timeout=15)
        r.raise_for_status()
        return r.json()
    return [m for m in _read_local() if m["room"] == room]


def add(room, player, kind, data):
    row = {"room": room, "player": player, "kind": kind, "data": data,
           "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    conf = picks._supabase()
    if conf:
        import requests
        url, key = conf
        r = requests.post(f"{url}/rest/v1/{TABLE}", json=row, headers={**picks._headers(key), "Prefer": "return=minimal"},
                          timeout=15)
        r.raise_for_status()
        return
    rows = _read_local()
    row["id"] = len(rows) + 1
    LOCAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOCAL_FILE.write_text(json.dumps(rows + [row], indent=1))


# ---------- the state of a room, rebuilt from its moves ----------

def state(room_moves):
    """{folder, driver, host, guest, calls: {player: {step: call}}, names} or None if there's no such room."""
    create = next((m for m in room_moves if m["kind"] == "create"), None)
    if not create:
        return None
    host = create["player"]
    guest = BOT if create["data"].get("bot") else next((m["player"] for m in room_moves
                                                         if m["kind"] == "join" and m["player"] != host), None)
    calls, names = {host: {}}, {}
    if guest:
        calls[guest] = {}
    for m in room_moves:
        if m["kind"] == "call" and m["player"] in calls:
            calls[m["player"]].setdefault(int(m["data"]["step"]), m["data"])     # first call for a step counts
        if m["kind"] == "name":
            names[m["player"]] = m["data"]["nickname"]
    return {"folder": create["data"]["folder"], "driver": str(create["data"]["driver"]), "host": host, "guest": guest,
            "calls": calls, "names": names}


def steps(pack, driver):
    """The laps where the players decide: 1, 1+STEP, ... (the call covers laps lap..lap+STEP-1)."""
    n = pack["drivers"][driver]["laps"]
    return list(range(1, n - 1, STEP))


def plan_of(calls):
    """A player's stops, from their calls."""
    return [{"lap": c["box"], "tyre": c["tyre"], "age": 0, "free": False}
            for _, c in sorted(calls.items()) if c.get("box")]


def bot_calls(pack, driver):
    """Our strategist's real-time plan, written as calls."""
    stops = pack["drivers"][driver]["strategist"]
    out = {}
    for k, lap in enumerate(steps(pack, driver)):
        s = next((s for s in stops if lap <= s["lap"] < lap + STEP), None)
        out[k] = {"step": k, "box": s["lap"] if s else None, "tyre": s["tyre"] if s else None}
    return out


def time_to(pack, driver, plan, upto):
    """Race time after `upto` laps with these stops (the same maths as engineer.simulate)."""
    d, t = pack["drivers"][driver], pack["tyres"]
    comp, age, total, carry = d["startTyre"], d["startAge"], d["start"], 0.0
    stops = {s["lap"]: s for s in plan}
    for k in range(1, min(upto, d["laps"]) + 1):
        life = t["life"][comp]
        lap = d["pace"][k - 1] + t["offset"][comp] + t["wear"][comp] * age \
            + t["cliffRate"] * max(0.0, age - t["cliffStart"] * life) + carry
        carry = 0.0
        s = stops.get(k)
        if s:
            loss = 0.0 if s.get("free") else pack["pitLoss"] * (pack["scFactor"].get(d["neutral"][k - 1]) or 1.0)
            lap += 0.4 * loss
            carry = 0.6 * loss
            comp, age = s["tyre"], s.get("age", 0)
        else:
            age += 1
        total += lap
    return total + (d.get("calibration", 0.0) if upto >= d["laps"] else 0.0)


def tyre_now(pack, driver, plan, lap):
    """(compound, age) at the start of `lap`."""
    d = pack["drivers"][driver]
    comp, age = d["startTyre"], d["startAge"]
    for k in range(1, lap):
        s = next((s for s in plan if s["lap"] == k), None)
        comp, age = (s["tyre"], 0) if s else (comp, age + 1)
    return comp, age


def legal(pack, driver, plan):
    """The two-compound rule."""
    used = {pack["drivers"][driver]["startTyre"]} | {s["tyre"] for s in plan}
    return len(used) >= 2
