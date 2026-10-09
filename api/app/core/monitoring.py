"""Error monitoring with Sentry.

The only module that imports ``sentry_sdk``. The rest of the app calls the
functions below, so the vendor stays in one place, and everything here is a
no-op when ``SENTRY_DSN`` is unset (tests, CI, local runs).

What reaches Sentry:

  * Unhandled exceptions. The FastAPI integration captures every 500.
  * ``DomainError``s with a 5xx status (``Misconfigured``, ``UpstreamError``,
    ``FeatureUnavailable``). The integration captures these too: the handler
    in ``app.main`` receives an exception whose ``status_code`` is in 500-599.
    The cause they were raised from (a Resend or Storage error) comes with them.
  * Failures the app answers with a clean response, or swallows so a request
    can still succeed, sent with ``report``: the database being unreachable, a
    constraint a route didn't check up front, a prize email that didn't go out.

Log records are breadcrumbs, not events. Every ``logger.exception`` that
matters is already covered above, so turning logs into events as well would
report each email outage twice.
"""

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.scrubber import DEFAULT_DENYLIST, EventScrubber

from app.core.config import settings

# Request bodies are attached to error events. Mask the member's personal data
# and one-time codes in them; the defaults already cover tokens, passwords and
# the Authorization header.
_DENYLIST = [*DEFAULT_DENYLIST, "email", "name", "phone", "code"]


def init_monitoring() -> None:
    """Start Sentry. Call once, before the FastAPI app is created."""
    if not settings.sentry_dsn:
        return
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment,
        # None lets the SDK fall back to SENTRY_RELEASE or the local git SHA.
        release=settings.sentry_release or None,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        # No member IPs, cookies or query strings.
        send_default_pii=False,
        # Frame variables would carry what the scrubber can't see by key: the
        # recipient, and email bodies holding claim links and login codes.
        include_local_variables=False,
        event_scrubber=EventScrubber(denylist=_DENYLIST, recursive=True),
        integrations=[LoggingIntegration(event_level=None)],
    )


def tag_program(slug: str) -> None:
    """Label whatever the current request sends with the program it works on."""
    sentry_sdk.set_tag("program", slug)


def report(exc: BaseException) -> None:
    """Send an exception the app handled on purpose."""
    sentry_sdk.capture_exception(exc)
