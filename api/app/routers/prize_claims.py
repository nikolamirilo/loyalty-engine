from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Redemption
from app.schemas import PrizeClaimOut, PrizeClaimRequest
from app.services.prize_claims import (
    claim_with_token,
    find_by_token,
    is_link_expired,
    program_of,
)

# No X-Program-Id here: the token names one prize, and the prize's program is
# read from it. A header sent anyway is ignored, so a link can never be
# claimed into the wrong program.
router = APIRouter(prefix="/prizes/claim", tags=["Prize claims"])


def _claim_out(db: Session, redemption: Redemption) -> PrizeClaimOut:
    return PrizeClaimOut(
        redemption_id=redemption.id,
        reward=redemption.reward,
        program=program_of(db, redemption),
        member_name=redemption.member.name,
        claimed_at=redemption.claimed_at,
        expires_at=redemption.claim_token_expires_at,
        expired=redemption.claimed_at is None and is_link_expired(redemption),
    )


@router.get("/{token}", response_model=PrizeClaimOut)
def preview(token: str, db: Session = Depends(get_db)):
    """The prize behind an emailed claim link, without claiming it."""
    return _claim_out(db, find_by_token(db, token))


@router.post("", response_model=PrizeClaimOut)
def claim(body: PrizeClaimRequest, db: Session = Depends(get_db)):
    """Claim the prize behind an emailed link. Claiming twice changes nothing."""
    return _claim_out(db, claim_with_token(db, body.token))
