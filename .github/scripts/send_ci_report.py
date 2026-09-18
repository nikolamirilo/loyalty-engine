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

    latency = tail("reports/latency.md")
    for code, char in SHORTCODES.items():
        latency = latency.replace(code, char)
    log = tail("reports/pytest.txt")
    if not latency and not log:
        log = "No report was produced - the test job failed before pytest ran."

    text = "\n\n".join(
        part
        for part in [headline, context, f"Run: {run_url}", latency, log]
        if part
    )

    # Omitted rather than left blank when the caller passed no context.
    meta_context = f" &middot; {html.escape(context)}" if context else ""

    accent = "#16a34a" if passed else "#dc2626"
    blocks = "".join(
        f'<pre style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;'
        f'padding:16px;font-size:12px;line-height:1.5;overflow-x:auto;'
        f'white-space:pre-wrap;">{html.escape(part)}</pre>'
        for part in [latency, log]
        if part
    )
    body = f"""<!DOCTYPE html>
<html>
  <body style="margin:0;padding:24px;background:#f8fafc;font-family:-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#0f172a;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
      <tr><td align="center">
        <table role="presentation" width="640" cellpadding="0" cellspacing="0" style="background:#ffffff;border:1px solid #e2e8f0;border-radius:12px;max-width:640px;width:100%;overflow:hidden;">
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
