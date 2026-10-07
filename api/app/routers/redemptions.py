from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.program import get_program
from app.models import Member, Program, Redemption, RedemptionSource, TransactionType
from app.schemas import PrizeAssignOut, PrizeAssignRequest, RedemptionOut
from app.services.points import record_transaction
from app.services.prize_claims import claim_prize, issue_claim_token, send_prize_email
from app.services.rewards import assert_available, consume_stock, get_reward_or_404, grant_prize
from app.services.scoping import get_scoped_or_404

router = APIRouter(tags=["Redemptions"])


@router.post("/members/{member_id}/redeem/{reward_id}", response_model=RedemptionOut, status_code=201)
def redeem_reward(
    member_id: UUID,
    reward_id: UUID,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    member = (
        db.query(Member)
        .filter(Member.id == member_id, Member.program_id == program.id)
        .with_for_update()
        .first()
    )
    if not member:
        raise HTTPException(404, "Member not found")

    reward = get_reward_or_404(db, reward_id, program, lock=True)
    assert_available(reward)
    if member.total_points < reward.points_cost:
        raise HTTPException(400, f"Insufficient points: has {member.total_points}, needs {reward.points_cost}")

    consume_stock(reward)
    # Debits total_points and re-applies the tier in one place.
    record_transaction(
        db, member, -reward.points_cost, TransactionType.spend, f"Redeemed: {reward.name}"
    )

    redemption = Redemption(
        member_id=member.id,
        reward_id=reward.id,
        points_spent=reward.points_cost,
        source=RedemptionSource.redeemed,
    )
    db.add(redemption)
    db.commit()
    db.refresh(redemption)
    return redemption


@router.post("/members/{member_id}/prizes/{reward_id}", response_model=PrizeAssignOut, status_code=201)
def assign_prize(
    member_id: UUID,
    reward_id: UUID,
    # Optional so callers that send no body keep working.
    body: Optional[PrizeAssignRequest] = Body(default=None),
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    member = get_scoped_or_404(db, Member, member_id, program, "Member")

    reward = get_reward_or_404(db, reward_id, program, lock=True)
    assert_available(reward)

    redemption = grant_prize(db, member.id, reward)
    token = issue_claim_token(redemption) if body and body.send_email else None
    db.commit()
    db.refresh(redemption)

    out = PrizeAssignOut.model_validate(redemption)
    # Sent only after the commit: the email links to a prize that must exist,
    # and a failed send leaves the prize assigned (see email_error).
    if token is not None:
        out.email_error = send_prize_email(member, reward, program, token)
        out.email_sent = out.email_error is None
    return out


@router.post(
    "/members/{member_id}/prizes/{redemption_id}/claim", response_model=RedemptionOut
)
def claim_member_prize(
    member_id: UUID,
    redemption_id: UUID,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    """Claim an assigned prize for a signed-in member. Claiming twice changes nothing."""
    get_scoped_or_404(db, Member, member_id, program, "Member")
    redemption = (
        db.query(Redemption)
        .filter(Redemption.id == redemption_id, Redemption.member_id == member_id)
        .first()
    )
    if not redemption:
        raise HTTPException(404, "Prize not found")
    return claim_prize(db, redemption)


@router.get("/members/{member_id}/prizes", response_model=list[RedemptionOut])
def list_member_prizes(
    member_id: UUID,
    source: Optional[RedemptionSource] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    # Resolving the member inside the program scopes the rows below: a
    # redemption hangs off the membership, so it cannot belong to another one.
    get_scoped_or_404(db, Member, member_id, program, "Member")
    # joinedload the reward so serializing RedemptionOut.reward doesn't lazy-load
    # one query per row (N+1).
    q = (
        db.query(Redemption)
        .options(joinedload(Redemption.reward))
        .filter(Redemption.member_id == member_id)
    )
    if source is not None:
        q = q.filter(Redemption.source == source)
    return q.order_by(Redemption.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/members/{member_id}/redemptions", response_model=list[RedemptionOut])
def list_member_redemptions(
    member_id: UUID,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    get_scoped_or_404(db, Member, member_id, program, "Member")
    # joinedload the reward so serializing RedemptionOut.reward doesn't lazy-load
    # one query per row (N+1).
    return (
        db.query(Redemption)
        .options(joinedload(Redemption.reward))
        .filter(Redemption.member_id == member_id)
        .order_by(Redemption.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
