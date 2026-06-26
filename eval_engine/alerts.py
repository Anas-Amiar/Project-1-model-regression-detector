"""
Sends a Slack alert summarizing the eval run + diff.

If SLACK_WEBHOOK_URL is set in the environment, this actually posts to
Slack. If it's not set, it just prints the message that *would* be
sent -- so you can build and test this fully before you have a
Slack workspace.
"""

import os
import json


def build_slack_message(current_run: dict, diff: dict, report_path: str | None = None) -> dict:
    """Build the Slack message payload (Slack's "blocks" format)."""
    severity_emoji = {
        "critical": ":red_circle:",
        "warning": ":large_yellow_circle:",
        "ok": ":large_green_circle:",
        "none": ":white_circle:",
    }
    severity = diff.get("severity", "none")
    emoji = severity_emoji.get(severity, ":white_circle:")

    headline = (
        f"{emoji} *Eval Run: {current_run['prompt_version']}* — "
        f"{current_run['passed_cases']}/{current_run['total_cases']} passed "
        f"({current_run['pass_rate']*100:.1f}%)"
    )

    lines = [headline, diff.get("message", "")]

    if diff.get("regressions"):
        lines.append("\n*Regressions:*")
        for r in diff["regressions"][:5]:  # cap so the message doesn't get huge
            lines.append(f"  - `{r['id']}`: {r['previously']} -> {r['now']}")

    if report_path:
        lines.append(f"\nFull report: {report_path}")

    text = "\n".join(lines)

    return {
        "text": text,
        "blocks": [
            {"type": "section", "text": {"type": "mrkdwn", "text": text}}
        ],
    }


def send_slack_alert(current_run: dict, diff: dict, report_path: str | None = None) -> bool:
    """
    Send the alert. Returns True if it was actually sent to Slack,
    False if it just printed locally (dry-run mode, no webhook configured).
    """
    message = build_slack_message(current_run, diff, report_path)
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")

    if not webhook_url:
        print("\n--- [DRY RUN] No SLACK_WEBHOOK_URL set. This is what would be sent to Slack: ---")
        print(message["text"])
        print("--- [END DRY RUN] ---")
        return False

    import httpx

    response = httpx.post(webhook_url, json=message, timeout=10)
    response.raise_for_status()
    return True
