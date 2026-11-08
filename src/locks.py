"""Locked predictions kept in the online database (Supabase table "locks").

Why: GitHub's timer is unreliable (the "every 3 hours" robot often runs only 2-3 times a day), so the
robot can't be trusted to lock a race on time. Instead, the first time anyone opens the app after the
lock time (8 hours before lights out), the app makes the prediction and saves it here. The first save
wins and can never be overwritten. The robot later copies that exact row into predictions.csv.

The table is created once in Supabase's SQL editor:
    create table locks (season int not null, round int not null, data jsonb not null,
                        created_at timestamptz not null default now(), primary key (season, round));
    alter table locks enable row level security;
"""
import requests

from picks import _headers, _supabase

TABLE = "locks"


def get_locks(season=None):
    """Every lock saved in the database (optionally one season) as a list of rows, or [] if offline."""
    conf = _supabase()
    if not conf:
        return []
    url, key = conf
    params = {"select": "data", "order": "round"}
    if season is not None:
        params["season"] = f"eq.{int(season)}"
    response = requests.get(f"{url}/rest/v1/{TABLE}", params=params, headers=_headers(key), timeout=15)
    response.raise_for_status()
    return [r["data"] for r in response.json()]


def get_lock(season, rnd):
    """The saved lock for one race, or None."""
    return next((r for r in get_locks(season) if int(r["round"]) == int(rnd)), None)


def save_lock(row):
    """Save a lock unless one already exists for that race (the first save always wins).
    Returns the lock that is stored afterwards, which may be someone else's earlier save."""
    conf = _supabase()
    if not conf:
        return None
    url, key = conf
    body = {"season": int(row["season"]), "round": int(row["round"]), "data": row}
    response = requests.post(f"{url}/rest/v1/{TABLE}?on_conflict=season,round", json=body,
                             headers={**_headers(key), "Prefer": "resolution=ignore-duplicates,return=minimal"},
                             timeout=15)
    response.raise_for_status()
    return get_lock(row["season"], row["round"])
