"""
Generates a human-readable HTML report for an eval run + its diff
against the previous run. This is what you'd open in a browser (or
link to from a Slack alert) to see exactly what changed.
"""

import os

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Eval Report - {run_timestamp}</title>
<style>
  body {{ font-family: -apple-system, sans-serif; max-width: 900px; margin: 40px auto; color: #222; }}
  h1 {{ font-size: 20px; }}
  .scorecard {{ display: flex; gap: 24px; margin: 20px 0; }}
  .stat {{ background: #f4f4f4; padding: 12px 20px; border-radius: 8px; }}
  .stat .label {{ font-size: 12px; color: #666; }}
  .stat .value {{ font-size: 22px; font-weight: 600; }}
  .severity-critical {{ color: #c0392b; }}
  .severity-warning {{ color: #d68910; }}
  .severity-ok {{ color: #27ae60; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
  th, td {{ text-align: left; padding: 8px 10px; border-bottom: 1px solid #eee; font-size: 14px; }}
  .pass {{ color: #27ae60; }}
  .fail {{ color: #c0392b; font-weight: 600; }}
  .regression-row {{ background: #fdecea; }}
  .improvement-row {{ background: #eafaf1; }}
</style>
</head>
<body>
  <h1>Eval Run Report</h1>
  <p>Prompt version: <b>{prompt_version}</b> &middot; Run time: {run_timestamp}</p>

  <div class="scorecard">
    <div class="stat"><div class="label">Pass Rate</div><div class="value">{pass_rate_pct}%</div></div>
    <div class="stat"><div class="label">Passed</div><div class="value">{passed_cases}/{total_cases}</div></div>
    <div class="stat"><div class="label">vs Previous</div><div class="value severity-{severity}">{delta_str}</div></div>
  </div>

  <p class="severity-{severity}"><b>{message}</b></p>

  <h3>Regressions ({regression_count})</h3>
  {regressions_table}

  <h3>Improvements ({improvement_count})</h3>
  {improvements_table}

  <h3>All Test Cases</h3>
  <table>
    <tr><th>ID</th><th>Difficulty</th><th>Input</th><th>Expected</th><th>Actual</th><th>Status</th></tr>
    {all_rows}
  </table>
</body>
</html>
"""


def _rows_table(items, cols):
    if not items:
        return "<p><i>None</i></p>"
    rows = "".join(
        "<tr>" + "".join(f"<td>{item.get(c, '')}</td>" for c in cols) + "</tr>"
        for item in items
    )
    header = "".join(f"<th>{c}</th>" for c in cols)
    return f"<table><tr>{header}</tr>{rows}</table>"


def generate_html_report(current_run: dict, diff: dict) -> str:
    """Build the HTML report and save it to reports/. Returns the file path."""
    os.makedirs(REPORTS_DIR, exist_ok=True)

    delta = diff.get("pass_rate_delta", 0.0)
    delta_str = f"{delta*100:+.1f}%" if not diff.get("is_first_run") else "first run"

    all_rows = "".join(
        f"""<tr class="{'regression-row' if any(r['id']==res['id'] for r in diff.get('regressions', [])) else ''}">
            <td>{res['id']}</td><td>{res['difficulty']}</td>
            <td>{res['input'][:70]}</td>
            <td>{res['expected_category']}</td><td>{res['actual_category']}</td>
            <td class="{'pass' if res['passed'] else 'fail'}">{'PASS' if res['passed'] else 'FAIL'}</td>
        </tr>"""
        for res in current_run["results"]
    )

    html = HTML_TEMPLATE.format(
        run_timestamp=current_run["run_timestamp"],
        prompt_version=current_run["prompt_version"],
        pass_rate_pct=round(current_run["pass_rate"] * 100, 1),
        passed_cases=current_run["passed_cases"],
        total_cases=current_run["total_cases"],
        severity=diff.get("severity", "none"),
        delta_str=delta_str,
        message=diff.get("message", ""),
        regression_count=len(diff.get("regressions", [])),
        improvement_count=len(diff.get("improvements", [])),
        regressions_table=_rows_table(diff.get("regressions", []), ["id", "input", "previously", "now"]),
        improvements_table=_rows_table(diff.get("improvements", []), ["id", "input", "previously", "now"]),
        all_rows=all_rows,
    )

    timestamp_safe = current_run["run_timestamp"].replace(":", "-")
    path = os.path.join(REPORTS_DIR, f"report_{timestamp_safe}.html")
    with open(path, "w") as f:
        f.write(html)
    return path
