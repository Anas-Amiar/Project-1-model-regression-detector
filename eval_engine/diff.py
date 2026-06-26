"""
The core value of this whole project: compares a new eval run against
the previous one and tells you exactly what got better or worse.
"""

WARNING_THRESHOLD = 0.03  # 3% pass-rate drop triggers a warning
CRITICAL_THRESHOLD = 0.08  # 8% pass-rate drop triggers a critical alert


def compare_runs(current: dict, previous: dict | None) -> dict:
    """Compare two eval runs and return a diff summary."""
    if previous is None:
        return {
            "is_first_run": True,
            "pass_rate_delta": 0.0,
            "severity": "none",
            "regressions": [],
            "improvements": [],
            "message": "This is the first recorded run. Nothing to compare against yet.",
        }

    pass_rate_delta = current["pass_rate"] - previous["pass_rate"]

    # build lookup of previous results by test case id
    previous_by_id = {r["id"]: r for r in previous["results"]}

    regressions = []
    improvements = []
    for result in current["results"]:
        prev_result = previous_by_id.get(result["id"])
        if prev_result is None:
            continue  # new test case, nothing to compare
        if prev_result["passed"] and not result["passed"]:
            regressions.append({
                "id": result["id"],
                "input": result["input"],
                "previously": prev_result["actual_category"],
                "now": result["actual_category"],
            })
        elif not prev_result["passed"] and result["passed"]:
            improvements.append({
                "id": result["id"],
                "input": result["input"],
                "previously": prev_result["actual_category"],
                "now": result["actual_category"],
            })

    drop = -pass_rate_delta
    if drop >= CRITICAL_THRESHOLD:
        severity = "critical"
    elif drop >= WARNING_THRESHOLD:
        severity = "warning"
    else:
        severity = "ok"

    return {
        "is_first_run": False,
        "previous_pass_rate": previous["pass_rate"],
        "current_pass_rate": current["pass_rate"],
        "pass_rate_delta": round(pass_rate_delta, 4),
        "severity": severity,
        "regressions": regressions,
        "improvements": improvements,
        "message": _build_message(severity, regressions, improvements, pass_rate_delta),
    }


def _build_message(severity, regressions, improvements, pass_rate_delta) -> str:
    if severity == "critical":
        return f"CRITICAL: {len(regressions)} regression(s) detected. Pass rate dropped {abs(pass_rate_delta)*100:.1f}%."
    if severity == "warning":
        return f"WARNING: {len(regressions)} regression(s) detected. Pass rate dropped {abs(pass_rate_delta)*100:.1f}%."
    if regressions:
        return f"{len(regressions)} regression(s) detected, but within acceptable threshold."
    if improvements:
        return f"No regressions. {len(improvements)} case(s) improved."
    return "No change. All previously passing cases still pass."
