"""DOI (double opt-in) email verification.

A member proves ownership of their email by entering a short-lived numeric
code sent to it. Only a hash of the code is ever persisted
(``EmailVerificationCode.code_hash``); the raw code exists only in memory
long enough to be emailed.
"""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import resend
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import EmailVerificationCode, Member

CODE_TTL = timedelta(minutes=10)
RESEND_COOLDOWN = timedelta(seconds=60)
MAX_ATTEMPTS = 5


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _as_aware(value: datetime) -> datetime:
    # Timestamps read back from the DB may be naive; stored values are UTC.
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def resolve_member(db: Session, email: Optional[str], member_id: Optional[UUID]) -> Member:
    """Look up the member a DOI request refers to.

    Exactly one of `email`/`member_id` is required; if both are given they
    must resolve to the same member, so a caller can't be misdirected by a
    stale/mismatched pair.
    """
    if email is None and member_id is None:
        raise HTTPException(400, "Provide either email or member_id")

    member: Optional[Member] = None
    if member_id is not None:
        member = db.get(Member, member_id)
        if not member:
            raise HTTPException(404, "Member not found")
        if email is not None and member.email.lower() != email.lower():
            raise HTTPException(400, "email and member_id do not refer to the same member")
        return member

    member = db.query(Member).filter(Member.email == email).first()
    if not member:
        raise HTTPException(404, "Member not found")
    return member


def _generate_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def _hash_code(member_id: UUID, code: str) -> str:
    # Salted with member_id (via HMAC key = the existing shared API_TOKEN
    # secret) so the same code never hashes the same way across members.
    return hmac.new(
        settings.api_token.encode(), f"{member_id}:{code}".encode(), hashlib.sha256
    ).hexdigest()


def _latest_active_code(db: Session, member_id: UUID) -> Optional[EmailVerificationCode]:
    return (
        db.query(EmailVerificationCode)
        .filter(
            EmailVerificationCode.member_id == member_id,
            EmailVerificationCode.consumed_at.is_(None),
        )
        .order_by(EmailVerificationCode.created_at.desc())
        .first()
    )


def _verification_email_html(code: str, ttl_minutes: int) -> str:
    # Table layout + inline styles: the only markup broadly supported across
    # email clients (no external stylesheets, no flex/grid). There's no real
    # "copy" button here - email clients strip all JavaScript, so a clipboard
    # button can't actually run. This is the standard alternative: a large,
    # spaced-out, monospaced code that's trivial to tap-and-select-all.
    #
    # Colors are the app's light-mode design tokens (client/app/globals.css)
    # - hardcoded because email clients don't reliably honor prefers-color-scheme.
    background = "#f8fafc"  # --background
    surface = "#ffffff"  # --surface
    foreground = "#0f172a"  # --foreground
    muted = "#475569"  # --muted
    faint = "#64748b"  # --faint
    line = "#e2e8f0"  # --line
    primary = "#5b4bd6"  # --primary
    code_bg = "#efecfd"  # --primary-subtle
    code_fg = "#4338ca"  # --primary-subtle-fg

    return f"""\
<!DOCTYPE html>
<html>
  <body style="margin:0;padding:0;background-color:{background};font-family:-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:{background};padding:32px 16px;">
      <tr>
        <td align="center">
          <table role="presentation" width="480" cellpadding="0" cellspacing="0" style="background-color:{surface};border:1px solid {line};border-radius:12px;max-width:480px;width:100%;overflow:hidden;">
            <tr>
              <td style="background-color:{primary};height:4px;line-height:4px;font-size:0;">&nbsp;</td>
            </tr>
            <tr>
              <td style="padding:40px;text-align:center;">
                <p style="margin:0 0 8px;font-size:14px;color:{muted};">Your verification code</p>
                <table role="presentation" align="center" cellpadding="0" cellspacing="0" style="margin:16px auto;background-color:{code_bg};border-radius:10px;">
                  <tr>
                    <td style="padding:20px 28px;">
                      <span style="font-family:'SFMono-Regular',Consolas,Menlo,monospace;font-size:40px;font-weight:700;letter-spacing:10px;color:{code_fg};">{code}</span>
                    </td>
                  </tr>
                </table>
                <p style="margin:16px 0 0;font-size:13px;color:{faint};">
                  Tap and hold the code above to select and copy it.
                </p>
                <p style="margin:24px 0 0;font-size:13px;color:{faint};">
                  This code expires in {ttl_minutes} minutes. If you didn't request this, you can ignore this email.
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
"""


def _send_verification_email(to_email: str, code: str) -> None:
    ttl_minutes = int(CODE_TTL.total_seconds() // 60)
    resend.api_key = settings.resend_api_key
    resend.Emails.send(
        {
            "from": settings.doi_from_email,
            "to": [to_email],
            "subject": "Your verification code",
            "text": f"Your verification code is {code}. It expires in {ttl_minutes} minutes.",
            "html": _verification_email_html(code, ttl_minutes),
        }
    )


def trigger_verification(db: Session, member: Member) -> None:
    if member.email_verified_at is not None:
        raise HTTPException(409, "Member email is already verified")

    latest = _latest_active_code(db, member.id)
    now = _now()
    if latest is not None and now - _as_aware(latest.created_at) < RESEND_COOLDOWN:
        raise HTTPException(429, "Please wait before requesting another code")

    # A member should only ever have one outstanding code at a time.
    db.query(EmailVerificationCode).filter(
        EmailVerificationCode.member_id == member.id,
        EmailVerificationCode.consumed_at.is_(None),
    ).delete()

    code = _generate_code()
    db.add(
        EmailVerificationCode(
            member_id=member.id,
            code_hash=_hash_code(member.id, code),
            expires_at=now + CODE_TTL,
        )
    )
    db.commit()

    _send_verification_email(member.email, code)


def verify_code(db: Session, member: Member, code: str) -> Member:
    if member.email_verified_at is not None:
        return member

    row = _latest_active_code(db, member.id)
    if row is None:
        raise HTTPException(400, "No active verification code for this member")
    if _now() > _as_aware(row.expires_at):
        raise HTTPException(400, "Verification code has expired")

    if not secrets.compare_digest(row.code_hash, _hash_code(member.id, code)):
        row.attempts += 1
        if row.attempts >= MAX_ATTEMPTS:
            row.consumed_at = _now()
        db.commit()
        raise HTTPException(400, "Invalid verification code")

    row.consumed_at = _now()
    member.email_verified_at = _now()
    db.commit()
    db.refresh(member)
    return member
