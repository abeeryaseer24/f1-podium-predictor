"""Race-day lock: save the next race's prediction, then check nothing earlier was changed.
Run by the race-day lock robot (.github/workflows/lock.yml) when lock_gate.py says it's time."""
import subprocess
import sys
from pathlib import Path

from checks import check_log_unchanged, check_predictions, snapshot_log

ROOT = Path(__file__).resolve().parent.parent


def main():
    before = snapshot_log()
    subprocess.run([sys.executable, str(ROOT / "src" / "log_prediction.py")], check=True, cwd=ROOT)
    print("\nSafety checks")
    check_predictions()
    check_log_unchanged(before)
    print("\nRace-day lock finished.")


if __name__ == "__main__":
    main()
