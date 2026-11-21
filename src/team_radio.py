"""Team Radio: the real radio messages of a race, transcribed and sorted by topic.

OpenF1's team_radio endpoint lists every clip the broadcast published, with a link to the
audio on Formula 1's live-timing server. This downloads each clip, transcribes it with
faster-whisper (an open-source speech-to-text model that runs on the CPU, free), and sorts it
into a topic with simple keyword rules. The audio itself is never saved or re-hosted: the app
links to Formula 1's own copy.

Saves data/races/<folder>/team_radio.parquet:
  t, lap, driver_number, url, text, topic

Transcripts are automatic and contain mistakes, especially names and engineering slang.
The app says so wherever it shows them.

Usage:
  python src/team_radio.py 2025 12          one race
  python src/team_radio.py --missing --limit 3   races without a transcript yet (the robot runs this)
"""
import argparse
import json
import os
import re
import tempfile

import pandas as pd
import requests

from predictor import RACES_DIR
from prepare_race import get, timed, to_dt

MODEL_SIZE = "base.en"
# Words Whisper otherwise mishears on F1 radio. Passed as a hint, not forced.
PROMPT = ("Formula 1 team radio. Box, box. Slicks, inters, softs, mediums, hards. DRS, undercut, "
          "overcut, safety car, VSC, pit lane, deg, plan B, copy, push, P1.")

TOPICS = [
    ("Pit stop call", r"\bbox\b|\bboxing\b|pit (this|next) lap|stay out|\bplan [a-d]\b|pit confirm"),
    ("Tyres", r"\btyres?\b|\btires?\b|\bgrip\b|\bdeg\b|degradation|\bsofts?\b|\bmediums?\b|\bhards?\b|"
              r"\binters?\b|intermediate|\bslicks?\b|\bwets?\b|graining|blister|front[- ]left|rear[- ]left|"
              r"front[- ]right|rear[- ]right|\bcliff\b"),
    ("Weather", r"\brain\b|raining|\bwet\b|\bdry\b|drying|drizzle|spitting|\bdamp\b"),
    ("Car problem", r"\bproblem\b|\bissue\b|\bdamage\b|\bpower\b|losing power|engine|gearbox|\bbrakes?\b|"
                    r"vibration|\bfailure\b|\bstop the car\b|retire|\bsmoke\b|\bfire\b|\bleak\b"),
    ("Incident or penalty", r"penalt|investigat|steward|\bcrash|contact|hit me|into the side|track limits|"
                            r"\bwarning\b|\bflag\b|\bunsafe\b|dangerous"),
    ("Celebration", r"get in|well done|\bwe won\b|\bp1\b|podium|great job|fantastic|amazing|"
                    r"\bthank you\b|\bthanks\b|let's go|brilliant|what a race"),
    ("Pace and gaps", r"\bgap\b|\bsecond[s]?\b|\btenths?\b|\bpace\b|\bpush\b|\bfaster\b|\bslower\b|"
                      r"\bdelta\b|\bcatching\b|\binterval\b|\bbehind\b|\bahead\b|lap time"),
]
OTHER = "Other"


def topic(text):
    t = (text or "").lower()
    for name, pattern in TOPICS:
        if re.search(pattern, t):
            return name
    return OTHER


def lap_of(laps, driver, t):
    """Which lap the driver was on at time t (seconds from the session start)."""
    d = laps[laps["driver_number"] == driver].sort_values("t_start")
    started = d[d["t_start"] <= t]
    return int(started["lap_number"].iloc[-1]) if len(started) else 0


_model = None


def model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
    return _model


def transcribe(url):
    """Download one clip to a temporary file, transcribe it, delete the file."""
    try:
        audio = requests.get(url, timeout=60)
        audio.raise_for_status()
    except requests.RequestException:
        return ""
    handle = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    try:
        handle.write(audio.content)
        handle.close()
        segments, _ = model().transcribe(handle.name, beam_size=1, vad_filter=True, initial_prompt=PROMPT)
        return " ".join(s.text.strip() for s in segments).strip()
    except Exception:                    # an unreadable clip: skip it, keep going
        return ""
    finally:
        os.unlink(handle.name)


def build(folder):
    path = RACES_DIR / folder
    info = json.loads((path / "info.json").read_text())
    t0 = to_dt(pd.Series([info["session_start"]])).iloc[0]
    rows = timed(get("team_radio", {"session_key": info["openf1_session_key"]}), t0)
    out = path / "team_radio.parquet"
    if rows.empty:
        pd.DataFrame(columns=["t", "lap", "driver_number", "url", "text", "topic"]).to_parquet(out, index=False)
        return 0
    laps = pd.read_parquet(path / "laps.parquet")
    rows = rows.rename(columns={"recording_url": "url"}).sort_values("t")
    rows["lap"] = [lap_of(laps, int(d), t) for d, t in zip(rows["driver_number"], rows["t"])]
    rows["text"] = [transcribe(u) for u in rows["url"]]
    rows["topic"] = rows["text"].map(topic)
    rows[["t", "lap", "driver_number", "url", "text", "topic"]].to_parquet(out, index=False)
    return len(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("season", nargs="?", type=int)
    parser.add_argument("round", nargs="?", type=int)
    parser.add_argument("--missing", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    if args.season and args.round:
        todo = [f"{args.season}_{args.round:02d}"]
    elif args.missing:
        todo = [p.name for p in sorted(RACES_DIR.glob("*_*"), reverse=True)        # newest first
                if (p / "info.json").exists() and (p / "laps.parquet").exists()
                and not (p / "team_radio.parquet").exists()]
        if args.limit:
            todo = todo[:args.limit]
    else:
        print(__doc__)
        return
    try:
        import faster_whisper  # noqa: F401  (checked up front, so a missing install saves nothing)
    except ImportError:
        raise SystemExit("faster-whisper isn't installed: no transcripts made this run.")
    for folder in todo:
        n = build(folder)
        print(f"{folder}: {n} radio messages transcribed")


if __name__ == "__main__":
    main()
