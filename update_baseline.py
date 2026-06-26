"""
Run this when you're happy with the current classifier/prompt behavior
and want to "bless" it as the new baseline that future runs (including
CI) compare against.

Usage:
    python3 run_eval.py        # check current behavior first
    python3 update_baseline.py # if it looks good, promote it
"""

from eval_engine.runner import run_eval
from eval_engine.history import set_baseline


def main():
    print("Running golden dataset to capture the new baseline...\n")
    current_run = run_eval(use_mock=True)  # flip to use_mock=False once you have an API key
    print(f"Pass rate: {current_run['passed_cases']}/{current_run['total_cases']} "
          f"({current_run['pass_rate']*100:.1f}%)")

    path = set_baseline(current_run)
    print(f"\nBaseline updated: {path}")
    print("Remember to 'git add reports/baseline.json' and commit this change.")


if __name__ == "__main__":
    main()
