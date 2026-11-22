"""Race Director: real incidents from race control, and what the stewards decided.

Race control's feed (OpenF1, 2023 onwards) notes every incident ("TURN 6 INCIDENT INVOLVING CARS 22 (TSU)
AND 87 (BEA) NOTED - CAUSING A COLLISION") and then announces what happened to it:
  "REVIEWED NO FURTHER INVESTIGATION"                   -> no action
  "UNDER INVESTIGATION" ... "NO FURTHER ACTION"         -> no action (after a look)
  "10 SECOND TIME PENALTY FOR CAR 22 (TSU) - ..."       -> a time penalty
  "DRIVE THROUGH PENALTY ..." / "STOP AND GO ..."      -> a harsher penalty
  "WILL BE INVESTIGATED AFTER THE RACE"                 -> decided later, not in the feed (left out)
This pairs each noted incident with its decision, so visitors can make the call themselves first.
"""
import json
import re

import pandas as pd

from predictor import RACES_DIR

CHOICES = ["No action", "5-second penalty", "10-second penalty", "Drive-through or harsher"]
INCIDENT = re.compile(r"((?:TURN \d+ |LAP \d+ |PIT LANE |PIT EXIT |PIT ENTRY )?INCIDENT INVOLVING CARS? [^-]+?)\s+"
                      r"(?:NOTED|UNDER INVESTIGATION|REVIEWED|WILL BE)", re.I)
CARS = re.compile(r"(\d+) \(([A-Z]{3})\)")


def outcome(text):
    t = text.upper()
    if "DRIVE THROUGH" in t or "STOP AND GO" in t or "STOP/GO" in t or "DISQUALIF" in t or "BLACK FLAG" in t:
        return CHOICES[3]
    if "10 SECOND" in t:
        return CHOICES[2]
    if "5 SECOND" in t:
        return CHOICES[1]
    if "NO FURTHER" in t:
        return CHOICES[0]
    return None


def incidents_in(folder):
    path = RACES_DIR / folder
    rc = pd.read_parquet(path / "race_control.parquet").sort_values("t")
    info = json.loads((path / "info.json").read_text())
    msgs = rc["message"].fillna("").tolist()
    laps = rc["lap_number"].tolist()
    out, seen = [], set()
    for k, m in enumerate(msgs):
        if "NOTED" not in m.upper() or m.upper().startswith("FIA STEWARDS"):
            continue
        hit = INCIDENT.search(m)
        if not hit:
            continue
        desc = hit.group(1).strip()
        if desc in seen:
            continue
        seen.add(desc)
        reason = re.sub(r"\s*\(\d{1,2}:\d{2}(:\d{2})?\)", "", m.split(" - ", 1)[1]).strip().title() if " - " in m else ""
        cars = CARS.findall(desc)
        decision, after, penalised = None, False, None
        for later in msgs[k + 1:]:
            u = later.upper()
            if "PENALTY SERVED" in u:
                continue
            if desc.upper() in u:
                if "AFTER THE RACE" in u:
                    after = True
                    break
                if "NO FURTHER" in u:
                    decision = CHOICES[0]
                    break
            elif "PENALTY FOR CAR" in u and cars and any(f"CAR {n} ({c})" in u for n, c in cars) and \
                    (not reason or reason.upper() in u):
                decision = outcome(u)
                hit_car = CARS.search(u.split("PENALTY FOR", 1)[1])
                penalised = hit_car.group(2) if hit_car else None
                break
        if decision and not after:
            out.append({"folder": folder, "race": f"{info['race_name']} {info['season']}", "season": info["season"],
                        "lap": int(laps[k]) if pd.notna(laps[k]) else None, "incident": desc.title(),
                        "reason": reason or "Unspecified", "cars": [c for _, c in cars], "decision": decision,
                        "penalised": penalised if decision != CHOICES[0] else None})
    return out


def all_incidents():
    rows = []
    for path in sorted(RACES_DIR.glob("*_*")):
        if (path / "race_control.parquet").exists() and (path / "info.json").exists():
            rows.extend(incidents_in(path.name))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = all_incidents()
    print(len(df), "decided incidents")
    print(df["decision"].value_counts())
    print(df.groupby("reason")["decision"].agg(lambda s: s.value_counts().index[0]).head(12))
    print(df.sample(5, random_state=1)[["race", "lap", "incident", "reason", "decision", "penalised"]].to_string())
