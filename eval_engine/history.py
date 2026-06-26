"""
Saves eval run results to disk and loads the "baseline" run to compare
against. The baseline is the one known-good run that's committed to
git, so CI and your laptop always compare against the same thing --
not just whatever happens to exist on one machine.
"""

import json
import os

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")
HISTORY_DIR = os.path.join(REPORTS_DIR, "history")
BASELINE_PATH = os.path.join(REPORTS_DIR, "baseline.json")


def save_run(run: dict) -> str:
    """Save a run result to reports/history/<timestamp>.json (local only, gitignored).
    Returns the saved path."""
    os.makedirs(HISTORY_DIR, exist_ok=True)
    timestamp_safe = run["run_timestamp"].replace(":", "-")
    path = os.path.join(HISTORY_DIR, f"{timestamp_safe}.json")
    with open(path, "w") as f:
        json.dump(run, f, indent=2)
    return path


def load_previous_run() -> dict | None:
    """Load the committed baseline run, or None if no baseline has been set yet."""
    if not os.path.exists(BASELINE_PATH):
        return None
    with open(BASELINE_PATH) as f:
        return json.load(f)


def set_baseline(run: dict) -> str:
    """Promote a run to be the new baseline. This is a deliberate, manual action --
    not something that happens automatically after every run."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    with open(BASELINE_PATH, "w") as f:
        json.dump(run, f, indent=2)
    return BASELINE_PATH
