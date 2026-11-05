"""Beat the AI: visitors' podium picks, and how they are scored against our model.

Picks are saved in a small online database (Supabase). Only the app's server talks to it, with a
secret key kept in Streamlit's secrets, so visitors can never read or change anyone else's picks.
Without the key (testing on your PC), picks are saved in data/picks_local.json instead.

Each visitor is a random player code kept in their browser (no login, no email, no IP address).

Scoring is never shown to visitors, only who won:
  3 points for each podium driver in the exact spot, 1 for a podium driver in the wrong spot.
  Equal points and both gave a whole order: fewer places off wins. Otherwise it's a tie.
"""
import json
import os
import secrets as random_codes
from datetime import datetime, timezone

import requests

from predictor import ROOT

TABLE = "picks"
LOCAL_FILE = ROOT / "data" / "picks_local.json"
CODE_LETTERS = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"          # no 0/O or 1/I/L, easy to copy


# ---------- player codes ----------

def new_player_code():
    """A random code like 'K7Q2-9FMX'."""
    raw = "".join(random_codes.choice(CODE_LETTERS) for _ in range(8))
    return f"{raw[:4]}-{raw[4:]}"


def clean_code(text):
    """A code typed by a visitor, tidied up, or None if it isn't a valid code."""
    raw = "".join(ch for ch in str(text or "").upper() if ch.isalnum())
    if len(raw) != 8 or any(ch not in CODE_LETTERS for ch in raw):
        return None
    return f"{raw[:4]}-{raw[4:]}"


# ---------- where picks are saved ----------

def _base(url):
    """'https://abc.supabase.co/rest/v1/' -> 'https://abc.supabase.co' (forgives a copied API path)."""
    url = url.strip().rstrip("/")
    return url[:-len("/rest/v1")] if url.endswith("/rest/v1") else url


def _supabase():
    """(url, key) from Streamlit's secrets (the app) or environment variables (the robot), or None."""
    if os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_KEY"):
        return _base(os.environ["SUPABASE_URL"]), os.environ["SUPABASE_KEY"].strip()
    try:
        import streamlit as st
        conf = st.secrets["supabase"]
        return _base(conf["url"]), conf["key"].strip()
    except Exception:
        return None


def online():
    return _supabase() is not None


def _headers(key):
    headers = {"apikey": key, "Content-Type": "application/json"}
    if key.startswith("eyJ"):                       # older Supabase keys also go in Authorization
        headers["Authorization"] = f"Bearer {key}"
    return headers


def _read_local():
    return json.loads(LOCAL_FILE.read_text()) if LOCAL_FILE.exists() else []


def save_pick(player, season, rnd, podium, order=None, nickname=""):
    """Save (or replace) one player's pick for one race."""
    row = {"player": player, "season": int(season), "round": int(rnd),
           "podium": list(podium), "full_order": list(order) if order else None,
           "nickname": (nickname or "").strip()[:20] or None,
           "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    conf = _supabase()
    if conf:
        url, key = conf
        response = requests.post(f"{url}/rest/v1/{TABLE}?on_conflict=player,season,round", json=row,
                                 headers={**_headers(key), "Prefer": "resolution=merge-duplicates,return=minimal"},
                                 timeout=15)
        response.raise_for_status()
        return
    rows = [r for r in _read_local()
            if not (r["player"] == player and r["season"] == row["season"] and r["round"] == row["round"])]
    LOCAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOCAL_FILE.write_text(json.dumps(rows + [row], indent=1))


def get_picks(player):
    """Every pick this player has saved, as a list of dicts."""
    conf = _supabase()
    if conf:
        url, key = conf
        response = requests.get(f"{url}/rest/v1/{TABLE}", params={"player": f"eq.{player}", "select": "*"},
                                headers=_headers(key), timeout=15)
        response.raise_for_status()
        return response.json()
    return [r for r in _read_local() if r["player"] == player]


def ping():
    """A tiny read, so the free database isn't paused for being unused (the robot calls this)."""
    conf = _supabase()
    if conf:
        url, key = conf
        requests.get(f"{url}/rest/v1/{TABLE}", params={"select": "season", "limit": 1},
                     headers=_headers(key), timeout=15).raise_for_status()


# ---------- scoring (never shown, only who won) ----------

def podium_points(podium, actual):
    return sum(3 if p == a else (1 if p in actual else 0) for p, a in zip(podium, actual))


def places_off(order, real):
    """Average places between a predicted order and the real finishing positions."""
    gaps = [abs(real[d] - i) for i, d in enumerate(order, start=1) if d in real]
    return sum(gaps) / len(gaps) if gaps else None


def verdict(you, you_order, model, model_order, actual, real):
    """'win', 'lose' or 'tie' for the visitor against our model."""
    yours, ours = podium_points(you, actual), podium_points(model, actual)
    if yours != ours:
        return "win" if yours > ours else "lose"
    if you_order and len(you_order) > 3 and model_order:
        # compare on the same drivers: the ones the visitor placed
        model_pos = {d: i for i, d in enumerate(model_order, start=1)}
        same = [d for d in you_order if d in real and d in model_pos]
        if same:
            a = sum(abs(real[d] - (you_order.index(d) + 1)) for d in same) / len(same)
            b = sum(abs(real[d] - model_pos[d]) for d in same) / len(same)
            if round(a, 2) != round(b, 2):
                return "win" if a < b else "lose"
    return "tie"
