"""Email delivery through Resend.

The only module that talks to the email provider. The code emails themselves,
their layout and their resend cooldown, live in ``app.services.code_emails``.
"""

from typing import Optional

import resend
from resend.exceptions import ResendError

from app.core.config import settings

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
                "from": settings.EMAIL_FROM,
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
