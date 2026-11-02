import time
from pathlib import Path

import pandas as pd
import requests

BASE_URL = "https://api.jolpi.ca/ergast/f1"
SEASONS = range(2016, 2027)   # 2016 to 2026 (2026 = completed races so far)
LIMIT = 100                   # rows per API call (the API's max)

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")


def get_json(url, params):
    """Call the API, and wait and retry if it says we're going too fast."""
    for attempt in range(5):
        resp = requests.get(url, params=params, timeout=30)
        if resp.status_code == 429:          # "too many requests"
            time.sleep(5 * (attempt + 1))
            continue
        resp.raise_for_status()
        return resp.json()
    raise RuntimeError(f"API kept refusing: {url}")


def fetch_results(season):
    """All race results for one season, one row per driver per race."""
    rows, offset = [], 0
    while True:
        data = get_json(f"{BASE_URL}/{season}/results.json",
                        {"limit": LIMIT, "offset": offset})["MRData"]
        for race in data["RaceTable"]["Races"]:
            for r in race["Results"]:
                rows.append({
                    "season": int(race["season"]),
                    "round": int(race["round"]),
                    "race_name": race["raceName"],
                    "circuit": race["Circuit"]["circuitId"],
                    "date": race["date"],
                    "driver": r["Driver"]["driverId"],
                    "constructor": r["Constructor"]["constructorId"],
                    "grid": int(r["grid"]),
                    "finish_position": int(r["position"]),
                    "status": r["status"],
                    "points": float(r["points"]),
                })
        offset += LIMIT
        if offset >= int(data["total"]):
            break
        time.sleep(0.5)
    return rows


def fetch_qualifying(season):
    """Qualifying results for one season."""
    rows, offset = [], 0
    while True:
        data = get_json(f"{BASE_URL}/{season}/qualifying.json",
                        {"limit": LIMIT, "offset": offset})["MRData"]
        for race in data["RaceTable"]["Races"]:
            for q in race["QualifyingResults"]:
                rows.append({
                    "season": int(race["season"]),
                    "round": int(race["round"]),
                    "driver": q["Driver"]["driverId"],
                    "quali_position": int(q["position"]),
                })
        offset += LIMIT
        if offset >= int(data["total"]):
            break
        time.sleep(0.5)
    return rows


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    results, quali = [], []
    for season in SEASONS:
        print(f"Downloading {season}...")
        results += fetch_results(season)
        time.sleep(0.5)
        quali += fetch_qualifying(season)
        time.sleep(0.5)

    results_df = pd.DataFrame(results)
    quali_df = pd.DataFrame(quali)

    # Save the data exactly as downloaded
    results_df.to_csv(RAW_DIR / "results_raw.csv", index=False)
    quali_df.to_csv(RAW_DIR / "quali_raw.csv", index=False)

    # Combine into one table: one row per driver per race
    df = results_df.merge(quali_df, on=["season", "round", "driver"], how="left")
    df = df.sort_values(["season", "round", "finish_position"]).reset_index(drop=True)
    df.to_csv(PROCESSED_DIR / "results.csv", index=False)

    print(f"Done. {len(df)} rows saved to data/processed/results.csv")


if __name__ == "__main__":
    main()