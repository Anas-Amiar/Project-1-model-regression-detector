"""Quick sanity check: run the mock classifier against the golden dataset
and just print pass/fail per case. The real eval engine (next step) will
do this properly with scoring, but this lets us eyeball it first."""

import json
from classifier import classify_email

with open("golden_dataset/v1.json") as f:
    dataset = json.load(f)

correct = 0
for case in dataset["test_cases"]:
    result = classify_email(case["input"], use_mock=True)
    is_correct = result.category == case["expected_category"]
    correct += is_correct
    status = "PASS" if is_correct else "FAIL"
    print(f"[{status}] {case['id']} ({case['difficulty']}): expected={case['expected_category']}, got={result.category}")

print(f"\n{correct}/{len(dataset['test_cases'])} correct")
