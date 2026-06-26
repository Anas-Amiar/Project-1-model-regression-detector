"""
Main entry point: run this any time you change the prompt to check
whether you've made the AI feature better or worse.

Usage:
    python3 run_eval.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from eval_engine.runner import run_eval
from eval_engine.history import save_run, load_previous_run
from eval_engine.diff import compare_runs
from eval_engine.report import generate_html_report
from eval_engine.alerts import send_slack_alert


def main():
    print("Running golden dataset through classifier...\n")
    current_run = run_eval(use_mock=True)  # flip to use_mock=False once you have an API key
    print(f"Pass rate: {current_run['passed_cases']}/{current_run['total_cases']} "
          f"({current_run['pass_rate']*100:.1f}%)\n")

    previous_run = load_previous_run()
    diff = compare_runs(current_run, previous_run)

    print(f"--- Comparison to previous run ---")
    print(diff["message"])

    if not diff["is_first_run"]:
        print(f"Previous pass rate: {diff['previous_pass_rate']*100:.1f}%")
        print(f"Current pass rate:  {diff['current_pass_rate']*100:.1f}%")

    if diff["regressions"]:
        print("\nRegressions (used to pass, now fail):")
        for r in diff["regressions"]:
            print(f"  - {r['id']}: \"{r['input'][:60]}...\" ({r['previously']} -> {r['now']})")

    if diff["improvements"]:
        print("\nImprovements (used to fail, now pass):")
        for r in diff["improvements"]:
            print(f"  - {r['id']}: \"{r['input'][:60]}...\" ({r['previously']} -> {r['now']})")

    save_path = save_run(current_run)
    print(f"\nRun saved to: {save_path}")

    report_path = generate_html_report(current_run, diff)
    print(f"HTML report: {report_path}")

    if diff["severity"] in ("critical", "warning"):
        send_slack_alert(current_run, diff, report_path)

    if diff["severity"] == "critical":
        sys.exit(1)  # non-zero exit code = CI will block the merge later


if __name__ == "__main__":
    main()
