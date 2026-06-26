"""
The test runner: takes the golden dataset, runs every test case through
the classifier, and scores each one. This is the "grading" step.
"""

import json
import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from classifier import classify_email


def score_case(case: dict, result) -> dict:
    """Score a single test case. Returns a dict with pass/fail + details."""
    category_correct = result.category == case["expected_category"]

    # crude summary similarity: word overlap ratio (good enough for v1,
    # later this gets replaced by an LLM-as-judge score)
    expected_words = set(case["expected_summary"].lower().split())
    actual_words = set(result.summary.lower().split())
    overlap = len(expected_words & actual_words) / max(len(expected_words), 1)

    return {
        "id": case["id"],
        "difficulty": case["difficulty"],
        "input": case["input"],
        "expected_category": case["expected_category"],
        "actual_category": result.category,
        "category_correct": category_correct,
        "expected_summary": case["expected_summary"],
        "actual_summary": result.summary,
        "summary_overlap_score": round(overlap, 2),
        "passed": category_correct,  # v1: pass/fail is based on category match only
    }


def run_eval(
    dataset_path: str = "golden_dataset/v1.json",
    prompt_version: str = "v1",
    use_mock: bool = True,
) -> dict:
    """Run the full golden dataset through the classifier and return a results object."""
    with open(dataset_path) as f:
        dataset = json.load(f)

    case_results = []
    for case in dataset["test_cases"]:
        result = classify_email(case["input"], prompt_version=prompt_version, use_mock=use_mock)
        case_results.append(score_case(case, result))

    total = len(case_results)
    passed = sum(r["passed"] for r in case_results)

    return {
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "prompt_version": prompt_version,
        "dataset_version": dataset["dataset_version"],
        "total_cases": total,
        "passed_cases": passed,
        "pass_rate": round(passed / total, 4) if total else 0,
        "results": case_results,
    }


if __name__ == "__main__":
    run = run_eval(use_mock=True)
    print(f"Pass rate: {run['passed_cases']}/{run['total_cases']} ({run['pass_rate']*100:.1f}%)")
    for r in run["results"]:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"  [{status}] {r['id']}")
