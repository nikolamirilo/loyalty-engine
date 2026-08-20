"""Regression test for how a failed DOI verification email is reported.

`POST /doi/trigger` answered every send failure with the same 502 ("please try
again shortly") and swallowed the provider's exception, so a permanently broken
setup - an unverified sender domain, a rejected API key - looked like a blip and
never reached the logs.

Sends must now raise `EmailDeliveryError` carrying the provider's own reason,
with permanent failures (which no retry can fix) told apart from transient ones.

Run: ./venv/bin/python -m tests.test_doi_email_errors
"""

import os

os.environ.setdefault("DATABASE_URL", "postgresql://u:p@h:6543/postgres")
os.environ.setdefault("API_TOKEN", "test-token")
os.environ.setdefault("RESEND_API_KEY", "test-resend-key")
os.environ.setdefault("DOI_FROM_EMAIL", "noreply@example.com")

import uuid

import resend
from resend.exceptions import ResendError

from app.models import DOIType, Member
from app.services.email_verification import (EmailDeliveryError,
                                             _send_verification_email)

# Never persisted - the send path only reads the address and (for link emails)
# the id off it.
MEMBER = Member(id=uuid.uuid4(), name="Test Member", email="member@example.com")

# (label, exception raised by the SDK, expected `transient`, text expected in reason)
CASES = [
    (
        "unverified sender domain",
        ResendError(
            code=403,
            error_type="validation_error",
            message="The example.com domain is not verified.",
            suggested_action="Verify the domain.",
        ),
        False,
        "not verified",
    ),
    (
        "rejected api key",
        ResendError(
            code=401,
            error_type="missing_api_key",
            message="Missing API key in the authorization header.",
            suggested_action="Include the header.",
        ),
        False,
        "API key",
    ),
    (
        "rate limited",
        ResendError(
            code=429,
            error_type="rate_limit_exceeded",
            message="Too many requests.",
            suggested_action="Slow down.",
        ),
        True,
        "Too many requests",
    ),
    (
        "provider outage",
        ResendError(
            code=500,
            error_type="application_error",
            message="Something went wrong.",
            suggested_action="Try again.",
        ),
        True,
        "Something went wrong",
    ),
    (
        "network failure",
        RuntimeError("Request failed: connection reset"),
        True,
        "connection reset",
    ),
]


def main() -> None:
    failures = []
    original_send = resend.Emails.send

    try:
        for label, raised, expect_transient, expect_in_reason in CASES:
            def failing_send(_params, _options=None, _raised=raised):
                raise _raised

            resend.Emails.send = failing_send
            try:
                _send_verification_email(MEMBER, "123456", DOIType.code)
            except EmailDeliveryError as exc:
                if exc.transient != expect_transient:
                    failures.append(
                        f"{label}: transient={exc.transient}, expected {expect_transient}"
                    )
                if expect_in_reason not in exc.reason:
                    failures.append(
                        f"{label}: reason {exc.reason!r} does not mention "
                        f"{expect_in_reason!r}"
                    )
            except Exception as exc:  # noqa: BLE001 - that's the bug being guarded
                failures.append(
                    f"{label}: raised {type(exc).__name__} instead of EmailDeliveryError"
                )
            else:
                failures.append(f"{label}: send failure was not raised at all")
    finally:
        resend.Emails.send = original_send

    if failures:
        print("FAIL:")
        for f in failures:
            print("  -", f)
        raise SystemExit(1)
    print(f"OK: {len(CASES)} send failures classified and explained")


if __name__ == "__main__":
    main()
