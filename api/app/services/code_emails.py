"""What the DOI and member-login code emails share: the HTML layout and the
resend cooldown.

Split out of ``email_verification.py`` so the DOI flow and the member-login
code flow (``member_auth.py``) share one implementation instead of two
near-identical copies. Delivery itself is ``app.integrations.email``.
"""

import math
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.core.errors import RateLimited

# The shortest gap allowed between two code emails to the same person. Every
# trigger mails a fresh code (so a member who lost the email can get another),
# which makes this the only thing stopping a caller from flooding an inbox by
# triggering in a loop - and from buying 5 more guesses every few seconds.
RESEND_COOLDOWN = timedelta(seconds=60)


# The app's light-mode design tokens (client/app/globals.css), hardcoded
# because email clients don't reliably honor prefers-color-scheme.
BACKGROUND = "#f8fafc"  # --background
SURFACE = "#ffffff"  # --surface
MUTED = "#475569"  # --muted
FAINT = "#64748b"  # --faint
LINE = "#e2e8f0"  # --line
PRIMARY = "#5b4bd6"  # --primary
PRIMARY_FG = "#ffffff"  # --primary-fg
CODE_BG = "#efecfd"  # --primary-subtle
CODE_FG = "#4338ca"  # --primary-subtle-fg


def email_shell(content: str, accent: str = PRIMARY) -> str:
    """Wrap an email's content in the shared card layout.

    Table layout + inline styles: the only markup broadly supported across
    email clients (no external stylesheets, no flex/grid). ``accent`` colours
    the top stripe, so a program-branded email can wear its own colour.
    """
    return f"""\
<!DOCTYPE html>
<html>
  <body style="margin:0;padding:0;background-color:{BACKGROUND};font-family:-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:{BACKGROUND};padding:32px 16px;">
      <tr>
        <td align="center">
          <table role="presentation" width="480" cellpadding="0" cellspacing="0" style="background-color:{SURFACE};border:1px solid {LINE};border-radius:12px;max-width:480px;width:100%;overflow:hidden;">
            <tr>
              <td style="background-color:{accent};height:4px;line-height:4px;font-size:0;">&nbsp;</td>
            </tr>
            <tr>
              <td style="padding:40px;text-align:center;">
{content}
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
"""


def expiry_note(subject: str, ttl_minutes: int) -> str:
    return f"""\
                <p style="margin:24px 0 0;font-size:13px;color:{FAINT};">
                  This {subject} expires in {ttl_minutes} minutes. If you didn't request this, you can ignore this email.
                </p>"""


def code_email_html(code: str, ttl_minutes: int, label: str = "Your verification code") -> str:
    # There's no real "copy" button here - email clients strip all JavaScript,
    # so a clipboard button can't actually run. This is the standard
    # alternative: a large, spaced-out, monospaced code that's trivial to
    # tap-and-select-all.
    return email_shell(
        f"""\
                <p style="margin:0 0 8px;font-size:14px;color:{MUTED};">{label}</p>
                <table role="presentation" align="center" cellpadding="0" cellspacing="0" style="margin:16px auto;background-color:{CODE_BG};border-radius:10px;">
                  <tr>
                    <td style="padding:20px 28px;">
                      <span style="font-family:'SFMono-Regular',Consolas,Menlo,monospace;font-size:40px;font-weight:700;letter-spacing:10px;color:{CODE_FG};">{code}</span>
                    </td>
                  </tr>
                </table>
                <p style="margin:16px 0 0;font-size:13px;color:{FAINT};">
                  Tap and hold the code above to select and copy it.
                </p>
{expiry_note("code", ttl_minutes)}"""
    )


def enforce_resend_cooldown(last_sent_at: Optional[datetime], now: datetime) -> None:
    """Refuse with 429 if this person was mailed a code under RESEND_COOLDOWN ago.

    A 429 rather than a silent 200: the caller has to be able to tell "a new
    email is on its way" from "nothing was sent", and when to try again.
    """
    if last_sent_at is None:
        return
    if last_sent_at.tzinfo is None:  # read back naive from the DB; stored as UTC
        last_sent_at = last_sent_at.replace(tzinfo=timezone.utc)
    remaining = (last_sent_at + RESEND_COOLDOWN - now).total_seconds()
    if remaining > 0:
        wait = math.ceil(remaining)
        raise RateLimited(
            f"A code was just sent. Please wait {wait} seconds before requesting another.",
            retry_after=wait,
        )
