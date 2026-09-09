"""Shared Resend-sending plumbing and HTML email shell.

Split out of ``email_verification.py`` so the DOI flow and the member-login
code flow (``member_auth.py``) share one implementation of "send a themed
code email via Resend" instead of two near-identical copies.
"""

import logging
from typing import Optional

import resend
from resend.exceptions import ResendError

from app.core.config import settings

logger = logging.getLogger("uvicorn.error")

# The SDK's default HTTP timeout (30s) outlives the serverless function budget,
# so a slow provider would surface as an opaque platform timeout instead of an
# error this module can classify and log. Cap it well under that budget.
SEND_TIMEOUT_SECONDS = 10

try:
    resend.default_http_client = resend.RequestsClient(timeout=SEND_TIMEOUT_SECONDS)
except AttributeError:  # SDK too old to expose a pluggable HTTP client
    pass

# Statuses Resend uses for failures a retry cannot resolve: a rejected or
# missing API key, an unverified sender domain, a recipient the account is not
# allowed to mail, a malformed payload. Everything else - 429, 5xx, network
# trouble - is treated as transient.
PERMANENT_SEND_STATUSES = frozenset({400, 401, 402, 403, 404, 405, 409, 413, 422})


class EmailDeliveryError(Exception):
    """The email could not be handed to the email provider.

    ``transient`` separates the two cases that need opposite answers: a rate
    limit or provider blip is worth retrying, while a rejected API key or an
    unverified sender domain fails identically forever and needs a human to fix
    the deployment - telling that caller to "try again shortly" hides a broken
    deployment behind an endpoint that can never succeed.
    """

    def __init__(self, reason: str, *, transient: bool) -> None:
        super().__init__(reason)
        self.reason = reason
        self.transient = transient


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


def email_shell(content: str) -> str:
    """Wrap an email's content in the shared card layout.

    Table layout + inline styles: the only markup broadly supported across
    email clients (no external stylesheets, no flex/grid).
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
              <td style="background-color:{PRIMARY};height:4px;line-height:4px;font-size:0;">&nbsp;</td>
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


def _send_status(exc: ResendError) -> Optional[int]:
    # ResendError.code is documented as the HTTP status but is typed as
    # str | int, and the SDK also synthesises a 500 for client-side failures.
    try:
        return int(exc.code)
    except (TypeError, ValueError):
        return None


def _send_reason(exc: ResendError) -> str:
    """The provider's own explanation, condensed for a log line."""
    status = _send_status(exc)
    head = f"Resend {status}" if status is not None else "Resend"
    error_type = getattr(exc, "error_type", None)
    if error_type:
        head = f"{head} {error_type}"
    detail = str(getattr(exc, "message", "") or exc).strip()
    return f"{head}: {detail}" if detail else head


def send_email(to: str, subject: str, text: str, html: str) -> None:
    """Hand an email to Resend, raising ``EmailDeliveryError`` on failure."""
    resend.api_key = settings.resend_api_key
    try:
        resend.Emails.send(
            {
                "from": settings.doi_from_email,
                "to": [to],
                "subject": subject,
                "text": text,
                "html": html,
            }
        )
    except ResendError as exc:
        status = _send_status(exc)
        raise EmailDeliveryError(
            _send_reason(exc),
            transient=status is None or status not in PERMANENT_SEND_STATUSES,
        ) from exc
    except Exception as exc:  # noqa: BLE001 - anything else is still a send failure
        raise EmailDeliveryError(
            f"{type(exc).__name__}: {exc}".strip(), transient=True
        ) from exc
