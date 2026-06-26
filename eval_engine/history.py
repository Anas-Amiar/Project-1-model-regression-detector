"""
Saves eval run results to disk and loads the most recent previous run,
so we always have something to compare against.
"""

import json
import os
import glob

HISTORY_DIR = os.path.join(os.path.dirname(__file__), "..", "reports", "history")


def save_run(run: dict) -> str:
    """Save a run result to reports/history/<timestamp>.json. Returns the saved path."""
    os.makedirs(HISTORY_DIR, exist_ok=True)
    timestamp_safe = run["run_timestamp"].replace(":", "-")
    path = os.path.join(HISTORY_DIR, f"{timestamp_safe}.json")
    with open(path, "w") as f:
        json.dump(run, f, indent=2)
    return path


def load_previous_run() -> dict | None:
    """Load the most recent saved run, or None if this is the first run ever."""
    os.makedirs(HISTORY_DIR, exist_ok=True)
    files = sorted(glob.glob(os.path.join(HISTORY_DIR, "*.json")))
    if not files:
        return None
    with open(files[-1]) as f:
        return json.load(f)
