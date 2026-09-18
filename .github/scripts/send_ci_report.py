"""Email an API test report through Resend.

Uses the same provider the app already sends DOI and login mail with, so the
reports need no second email vendor and no SMTP secrets - only a sender
on the domain that is already verified in Resend.

Called by the report job in .github/workflows/api-tests.yml - for pushes,
manual runs and the scheduled runs alike - with the test job's outcome in the
environment, and reads whatever the test job left in reports/.
"""

import html
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import date

RESEND_ENDPOINT = "https://api.resend.com/emails"

# Sent on every request - see the note where the headers are built.
USER_AGENT = "loyalty-engine-ci-report/1.0"

# How much pytest output to include. A green run is a few lines; a failing run
# can be thousands, and mail clients truncate long bodies unpredictably. The
# tail is the part that matters - the failure summary pytest prints last.
MAX_LOG_LINES = 120


# conftest.py writes the result column as GitHub emoji shortcodes, which only
# GitHub renders. In an inbox they would read as literal ":white_check_mark:",
# so swap them for the characters they stand for.
SHORTCODES = {
    ":white_check_mark:": "\u2705",
    ":x:": "\u274c",
    ":fast_forward:": "\u23e9",
}


def tail(path: str, limit: int = MAX_LOG_LINES) -> str:
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines()
    except FileNotFoundError:
        return ""
    if len(lines) <= limit:
        return "\n".join(lines)
    return f"[... {len(lines) - limit} earlier lines omitted ...]\n" + "\n".join(lines[-limit:])


def require(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        sys.exit(
            f"{name} is not set. The report needs RESEND_API_KEY (secret), "
            "CI_REPORT_FROM and CI_REPORT_TO (repository variables)."
        )
    return value


# Result -> the colour its status cell gets in the table.
RESULT_COLOURS = {"passed": "#16a34a", "failed": "#dc2626", "skipped": "#94a3b8"}

CELL = "padding:8px 10px;border-bottom:1px solid #e2e8f0;font-size:13px;vertical-align:top;"
# Marks a call that belongs to the step named above it.
CONTINUED = '<span style="color:#cbd5e1;">&#8627;</span>'
MONO = "font-family:'SFMono-Regular',Consolas,Menlo,monospace;"


def load_report(path: str):
    """The structured latency report, or None if the run never got that far."""
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (FileNotFoundError, ValueError):
        return None


def summary_line(report: dict) -> str:
    slowest = report["slowest"]
    return (
        f"{len(report['calls'])} calls, {report['totalMs']} ms total, "
        f"slowest {slowest['method']} {slowest['route']} at {slowest['ms']} ms"
    )


def latency_table(report: dict) -> str:
    """The per-call table as real table markup.

    Inline styles and plain <table> rows on purpose: mail clients strip
    stylesheets, and many still do not lay out flex or grid.
    """
    head = "".join(
        f'<th align="{align}" style="padding:8px 10px;border-bottom:2px solid #e2e8f0;'
        f'font-size:11px;letter-spacing:0.04em;text-transform:uppercase;color:#64748b;'
        f'font-weight:600;">{label}</th>'
        for label, align in (
            ("Step", "left"),
            ("Method", "left"),
            ("Route", "left"),
            ("Status", "right"),
            ("Latency", "right"),
        )
    )

    rows = []
    previous = None
    for call in report["calls"]:
        # A test makes one call for the thing it does and then more to check the
        # result. Naming the step only on the first makes the follow-ups read as
        # what they are - a DELETE answering 204 and then a GET answering 404 is
        # the deletion being proved, not the delete failing.
        step = "" if call["step"] == previous else call["step"]
        previous = call["step"]
        outcome = call.get("outcome", "")
        colour = RESULT_COLOURS.get(outcome, "#0f172a")
        # Tint the whole row for a failure, so it is findable without reading.
        tint = ' style="background:#fef2f2;"' if outcome == "failed" else ""
        rows.append(
            f"<tr{tint}>"
            f'<td style="{CELL}">{html.escape(step) if step else CONTINUED}</td>'
            f'<td style="{CELL}{MONO}color:#475569;">{html.escape(call["method"])}</td>'
            f'<td style="{CELL}{MONO}word-break:break-all;">{html.escape(call["route"])}</td>'
            f'<td align="right" style="{CELL}{MONO}color:{colour};font-weight:600;">'
            f'{call["status"]}</td>'
            f'<td align="right" style="{CELL}{MONO}white-space:nowrap;">{call["ms"]} ms</td>'
            "</tr>"
        )

    return (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        'style="width:100%;border-collapse:collapse;margin:0 0 12px;">'
        f"<tr>{head}</tr>{''.join(rows)}</table>"
        f'<p style="margin:0;font-size:12px;color:#64748b;">{html.escape(summary_line(report))}</p>'
    )


def latency_text(report: dict) -> str:
    """Plain-text alternative: aligned columns, no markdown pipes."""
    rows = []
    previous = None
    for call in report["calls"]:
        step = "" if call["step"] == previous else call["step"]
        previous = call["step"]
        rows.append(
            [
                step or "  \u21b3",
                call["method"],
                call["route"],
                str(call["status"]),
                f"{call['ms']} ms",
            ]
        )
    headers = ["Step", "Method", "Route", "Status", "Latency"]
    widths = [
        max(len(headers[i]), *(len(r[i]) for r in rows)) if rows else len(headers[i])
        for i in range(len(headers))
    ]
    def line(cells):
        return "  ".join(cell.ljust(widths[i]) for i, cell in enumerate(cells)).rstrip()

    return "\n".join(
        [line(headers), line(["-" * w for w in widths]), *(line(r) for r in rows), "", summary_line(report)]
    )


def pre(text: str) -> str:
    return (
        '<pre style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;'
        "padding:16px;font-size:12px;line-height:1.5;overflow-x:auto;"
        f'white-space:pre-wrap;margin:0 0 12px;">{html.escape(text)}</pre>'
    )


def main() -> None:
    api_key = require("RESEND_API_KEY")
    sender = require("REPORT_FROM")
    # Comma-separated, so one variable can fan out to the whole team.
    recipients = [addr.strip() for addr in require("REPORT_TO").split(",") if addr.strip()]

    result = os.environ.get("TEST_RESULT", "unknown")
    # Local time of this run. Several runs land on the same day, so without it
    # their subjects would be identical and thread together in most clients.
    slot = os.environ.get("SLOT", "").strip()
    # What set this run off, e.g. "scheduled run" or "push to main", so a
    # report that arrives off-schedule is not mistaken for a slot.
    context = os.environ.get("RUN_CONTEXT", "").strip()
    run_url = os.environ.get("RUN_URL", "")
    repo = os.environ.get("REPO", "loyalty-engine")
    stamp = f"{date.today().isoformat()} {slot}".strip()

    # The subject is the whole alert: it has to be unmistakable in a phone
    # notification, where only the first few words are visible. Failure leads
    # with a red circle and the word FAILED in caps; success is quiet enough to
    # filter away. Both end with the date so a missing day is visible too.
    passed = result == "success"
    if passed:
        subject = f"✅ API tests passed - {repo} - {stamp}"
        headline = "All API tests passed"
    elif result == "failure":
        subject = f"🔴 FAILED - API tests - {repo} - {stamp}"
        headline = "API tests FAILED"
    else:
        # cancelled, skipped, or the job never produced a result.
        subject = f"⚠️ API tests did not run ({result}) - {repo} - {stamp}"
        headline = f"API tests did not complete: {result}"

    report = load_report("reports/latency.json")

    # The raw pytest output is only worth carrying when something went wrong:
    # on a green run it repeats the table above and adds a screenful of
    # collection lines. On a red one it holds the tracebacks.
    log = "" if passed and report else tail("reports/pytest.txt")

    if report:
        table_html = latency_table(report)
        table_text = latency_text(report)
    else:
        # No structured report, e.g. the job died before pytest finished. Fall
        # back to the markdown meant for the GitHub summary, emoji and all.
        markdown = tail("reports/latency.md")
        for code, char in SHORTCODES.items():
            markdown = markdown.replace(code, char)
        table_html = pre(markdown) if markdown else ""
        table_text = markdown

    if not table_html and not log:
        log = "No report was produced - the test job failed before pytest ran."

    text = "\n\n".join(
        part
        for part in [headline, context, f"Run: {run_url}", table_text, log]
        if part
    )

    # Omitted rather than left blank when the caller passed no context.
    meta_context = f" &middot; {html.escape(context)}" if context else ""

    accent = "#16a34a" if passed else "#dc2626"
    blocks = table_html + (pre(log) if log else "")
    body = f"""<!DOCTYPE html>
<html>
  <body style="margin:0;padding:24px;background:#f8fafc;font-family:-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#0f172a;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
      <tr><td align="center">
        <table role="presentation" width="720" cellpadding="0" cellspacing="0" style="background:#ffffff;border:1px solid #e2e8f0;border-radius:12px;max-width:720px;width:100%;overflow:hidden;">
          <tr><td style="background:{accent};height:4px;line-height:4px;font-size:0;">&nbsp;</td></tr>
          <tr><td style="padding:32px;">
            <h1 style="margin:0 0 4px;font-size:20px;">{html.escape(headline)}</h1>
            <p style="margin:0 0 24px;font-size:13px;color:#64748b;">{html.escape(repo)} &middot; {stamp} Europe/Zurich{meta_context}</p>
            {blocks}
            <p style="margin:24px 0 0;font-size:13px;">
              <a href="{html.escape(run_url)}" style="color:#5b4bd6;">Open the full run in GitHub Actions</a>
            </p>
          </td></tr>
        </table>
      </td></tr>
    </table>
  </body>
</html>
"""

    payload = json.dumps(
        {"from": sender, "to": recipients, "subject": subject, "text": text, "html": body}
    ).encode()
    request = urllib.request.Request(
        RESEND_ENDPOINT,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            # api.resend.com sits behind Cloudflare, which bans urllib's default
            # "Python-urllib/3.x" agent outright - that request never reaches
            # Resend and comes back as a 403 whose body is "error code: 1010"
            # rather than Resend's usual JSON. Any ordinary agent string gets
            # through. The app's own mail goes via the resend SDK over requests,
            # which is why only this script ever hit it.
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            print(f"Resend accepted the report ({response.status}): {subject}")
    except urllib.error.HTTPError as exc:
        # Resend explains rejections in the body - an unverified sender domain
        # or a bad key both land here, and both need a human.
        sys.exit(f"Resend rejected the report ({exc.code}): {exc.read().decode(errors='replace')}")
    except urllib.error.URLError as exc:
        sys.exit(f"Could not reach Resend: {exc.reason}")

    # Exit red when the tests were red. The test job already fails the run on
    # its own; this keeps the report job's own status honest about what it just
    # mailed, rather than showing green next to a failure.
    if not passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
