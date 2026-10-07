"""Claiming assigned prizes, and the email that links to the claim page.

An assigned prize starts unclaimed (``Redemption.claimed_at`` is null). The
member claims it in one of two ways, which end in the same place:

  * signed in, from their wallet (``claim_prize``);
  * from the prize email, whose link carries a random token
    (``claim_with_token``). The link works without signing in, like the DOI
    ``/verify`` link.

Only an HMAC hash of the token is stored, on the redemption itself, so the
raw token exists only in memory long enough to be emailed. The token names
one redemption, which belongs to one membership in one program, so the
program a claim lands in always comes from the token and never from the
caller.
"""

import hashlib
import hmac
import html
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import quote, urlencode

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import InvalidInput, Misconfigured, NotFound
from app.integrations.email import EmailDeliveryError, send_email
from app.models import Member, Program, Redemption, RedemptionSource, Reward
from app.services.code_emails import CODE_FG, FAINT, MUTED, PRIMARY, PRIMARY_FG, email_shell

logger = logging.getLogger("uvicorn.error")

# Long enough to survive a busy inbox. An expired link only retires the link:
# the prize stays in the member's wallet, where they can still claim it.
CLAIM_TTL = timedelta(days=30)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _as_aware(value: datetime) -> datetime:
    # Timestamps read back from the DB may be naive; stored values are UTC.
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def _hash_token(token: str) -> str:
    # The token is 256 random bits, so unlike a 6-digit DOI code it needs no
    # per-person salt. The prefix keeps these hashes apart from any other HMAC
    # made with the same key.
    return hmac.new(
        settings.api_token.encode(), f"prize-claim:{token}".encode(), hashlib.sha256
    ).hexdigest()


def issue_claim_token(redemption: Redemption) -> str:
    """Give an assigned prize a fresh claim token and return it, raw.

    Replaces any earlier token, so only the newest email's link works. The
    caller commits.
    """
    token = secrets.token_urlsafe(32)
    redemption.claim_token_hash = _hash_token(token)
    redemption.claim_token_expires_at = _now() + CLAIM_TTL
    return token


def is_link_expired(redemption: Redemption) -> bool:
    expires_at = redemption.claim_token_expires_at
    return expires_at is None or _now() > _as_aware(expires_at)


def _claim_link(program: Program, token: str) -> str:
    """The client page that claims this prize.

    The program's slug is in the path so the page can show the right brand
    before it has asked the API anything. It is only a hint: the page checks
    it against the program the token belongs to.
    """
    base = settings.client_base_url
    if not base:
        raise Misconfigured(
            "Prize emails need CLIENT_BASE_URL set to the public base URL of the client app."
        )
    return f"{base}/p/{quote(program.slug, safe='')}/claim?{urlencode({'token': token})}"


def _prize_email_html(member: Member, reward: Reward, program: Program, link: str) -> str:
    # Every value below comes from a person (names, descriptions) or carries
    # `&` (the link), so all of it is escaped. Colours were validated as
    # #rrggbb when they were saved.
    accent = program.primary_color or PRIMARY
    link = html.escape(link, quote=True)
    logo = (
        f'<img src="{html.escape(program.logo_url, quote=True)}" alt="{html.escape(program.name, quote=True)}" '
        'height="40" style="display:block;margin:0 auto 24px;height:40px;max-width:160px;" />'
        if program.logo_url
        else ""
    )
    description = (
        f'<p style="margin:8px 0 0;font-size:14px;color:{MUTED};">{html.escape(reward.description)}</p>'
        if reward.description
        else ""
    )
    return email_shell(
        f"""\
                {logo}
                <p style="margin:0 0 8px;font-size:14px;color:{MUTED};">Congratulations, {html.escape(member.name)}! You've won</p>
                <p style="margin:0;font-size:22px;font-weight:700;color:{CODE_FG};">{html.escape(reward.name)}</p>
                {description}
                <table role="presentation" align="center" cellpadding="0" cellspacing="0" style="margin:24px auto;">
                  <tr>
                    <td align="center" style="background-color:{accent};border-radius:10px;">
                      <a href="{link}" style="display:inline-block;padding:14px 32px;font-size:15px;font-weight:600;color:{PRIMARY_FG};text-decoration:none;">Claim your prize</a>
                    </td>
                  </tr>
                </table>
                <p style="margin:16px 0 0;font-size:12px;color:{FAINT};word-break:break-all;">
                  Or paste this address into your browser:<br />
                  <a href="{link}" style="color:{CODE_FG};">{link}</a>
                </p>
                <p style="margin:24px 0 0;font-size:13px;color:{FAINT};">
                  This link expires in {CLAIM_TTL.days} days. You can also claim the prize from your wallet in {html.escape(program.name)}.
                </p>""",
        accent=accent,
    )


def send_prize_email(member: Member, reward: Reward, program: Program, token: str) -> Optional[str]:
    """Email the member their prize. Returns why it failed, or None if it went out.

    Never raises: the prize is already assigned, and a failed email must not
    make the assignment look like it failed too.
    """
    try:
        link = _claim_link(program, token)
        send_email(
            member.email,
            f"You've won {reward.name}!",
            (
                f"Congratulations, {member.name}! You've won {reward.name} in {program.name}. "
                f"Claim it at {link} - the link expires in {CLAIM_TTL.days} days."
            ),
            _prize_email_html(member, reward, program, link),
        )
    except Misconfigured as exc:
        logger.error("Prize email for member %s not sent: %s", member.id, exc.detail)
        return exc.detail
    except EmailDeliveryError as exc:
        logger.exception(
            "Prize email for member %s not sent (from=%s): %s",
            member.id,
            settings.EMAIL_FROM,
            exc.reason,
        )
        return f"The email could not be sent. {exc.reason}"
    return None


def find_by_token(db: Session, token: str) -> Redemption:
    redemption = (
        db.query(Redemption)
        .filter(Redemption.claim_token_hash == _hash_token(token))
        .first()
    )
    if redemption is None:
        raise NotFound("This prize link is not valid.")
    return redemption


def program_of(db: Session, redemption: Redemption) -> Program:
    """The program a prize belongs to, through its membership."""
    return db.get(Program, redemption.member.program_id)


def claim_prize(db: Session, redemption: Redemption) -> Redemption:
    """Mark an assigned prize as claimed. Claiming twice changes nothing.

    The token is kept after a claim, so opening the emailed link again shows
    "already claimed" rather than "not valid".
    """
    if redemption.source != RedemptionSource.assigned:
        raise InvalidInput("Only assigned prizes can be claimed.")
    if redemption.claimed_at is None:
        redemption.claimed_at = _now()
        db.commit()
        db.refresh(redemption)
    return redemption


def claim_with_token(db: Session, token: str) -> Redemption:
    redemption = find_by_token(db, token)
    if redemption.claimed_at is None and is_link_expired(redemption):
        raise InvalidInput(
            "This prize link has expired. Sign in to claim the prize from your wallet."
        )
    return claim_prize(db, redemption)
