# Model Regression Detection System

A CI/CD pipeline for LLM-powered features. Whenever a prompt or model change is proposed,
it runs the feature against a hand-verified golden dataset, flags any quality regressions,
and blocks the pull request before bad behavior reaches production.

The feature under test is a customer support email classifier: given an email, it returns
a category (`billing`, `technical`, `account`, `general`) and a one-sentence summary.

## Why this exists

Most teams change LLM prompts the same way they'd edit a typo: push it, see if anyone
complains. There's no equivalent of a unit test suite for "does this prompt still work."
This project is that test suite — git-diff for prompt behavior, with a pass/fail gate
on every pull request.

## How it works

```
classifier.py          The AI feature itself (mock mode + real OpenAI mode)
prompts/v1.yaml         Versioned prompt config (system prompt + few-shot examples)
golden_dataset/v1.json   10 hand-labeled test emails (the answer key)
eval_engine/
  runner.py              Runs the dataset through the classifier and scores each case
  history.py             Loads/saves the baseline run to compare against
  diff.py                Compares current run vs. baseline, flags regressions
  report.py              Generates an HTML scorecard report
  alerts.py               Builds and sends the Slack alert (or dry-run prints it)
reports/
  baseline.json          The committed "known good" run — CI always compares against this
  history/                Local-only run history (gitignored)
.github/workflows/eval.yml   Runs the pipeline automatically on every relevant PR
run_eval.py              Main entry point — run this to check your changes
update_baseline.py       Run this to deliberately promote a run to be the new baseline
```

### The core flow

1. You change `classifier.py` or a file in `prompts/`.
2. You open a pull request.
3. GitHub Actions runs `python3 run_eval.py` automatically.
4. The eval engine runs all 10 golden test cases through the classifier and scores them.
5. It compares the result against `reports/baseline.json` (the last known-good run).
6. If the pass rate drops by 8%+ ("critical") or 3%+ ("warning"), the run exits with an
   error code, the PR check fails, and (if configured) a Slack alert fires.
7. If the change is intentional and you're happy with the new behavior, run
   `python3 update_baseline.py` to promote it to the new baseline.

## Setup

```bash
git clone https://github.com/Anas-Amiar/model-regression-detector.git
cd model-regression-detector
pip install -r requirements.txt
python3 run_eval.py
```

By default everything runs in **mock mode** — a simple keyword-based fake classifier, so
you can run the whole pipeline with no API key. To use a real LLM:

1. Get an OpenAI API key.
2. `export OPENAI_API_KEY=sk-...`
3. In `run_eval.py`, change `run_eval(use_mock=True)` to `run_eval(use_mock=False)`.

To get Slack alerts instead of the local dry-run printout:

1. Create a Slack incoming webhook URL.
2. `export SLACK_WEBHOOK_URL=https://hooks.slack.com/...` locally, or add it as a
   repository secret named `SLACK_WEBHOOK_URL` for GitHub Actions.

## Adding new test cases

Edit `golden_dataset/v1.json` and add an entry to `test_cases`:

```json
{
  "id": "tc_011",
  "input": "the email text",
  "expected_category": "billing",
  "expected_summary": "one sentence describing what the email is about",
  "difficulty": "easy",
  "notes": "why this case matters"
}
```

Write these by hand. Don't generate them with an LLM — the whole point is that the
expected answer is verified ground truth, not the model grading itself.

## Adjusting regression thresholds

In `eval_engine/diff.py`:

```python
WARNING_THRESHOLD = 0.03   # 3% pass-rate drop triggers a warning
CRITICAL_THRESHOLD = 0.08  # 8% pass-rate drop triggers a critical alert + blocks merge
```

## Updating the baseline

The baseline (`reports/baseline.json`) is only updated deliberately, never automatically.
After a change you're confident in:

```bash
python3 update_baseline.py
git add reports/baseline.json
git commit -m "Update baseline after improving X"
```

## Architecture decisions

**Why a committed baseline file instead of local run history?**
The first version of this system kept a folder of timestamped run results and always
compared against "whatever ran last." That worked locally but silently broke in CI:
GitHub Actions spins up a fresh machine for every run with no memory of past runs, so it
always reported "first run, nothing to compare" — even when a real regression was sitting
right there. The fix was to commit one `baseline.json` to git so CI and your laptop are
always comparing against the same fixed point, and to make updating it a deliberate,
separate step (`update_baseline.py`) rather than something that happens automatically
after every run.

**Why mock mode by default?**
So the entire pipeline — dataset, scoring, diffing, reporting, alerting, CI — can be built,
run, and demoed without needing an API key. The mock classifier is intentionally simple
(keyword matching) so it has real, visible blind spots (e.g. it fails on non-English input
and sarcastic phrasing), which makes for a good demonstration of what the eval system is
supposed to catch once a smarter model is wired in.

**Why pass/fail is based on category match only (for now)**
Summary quality is scored with a simple word-overlap heuristic for visibility, but it
doesn't currently affect pass/fail. The natural next step is an LLM-as-judge score for
summary quality, which would replace the word-overlap heuristic with something more
reliable.

## What's deliberately out of scope for v1

- Multi-dimensional LLM-as-judge scoring (planned, not built)
- Drift detection across a rolling window of runs (per the original project spec)
- Statistical significance testing on small deltas
