from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import Member, PointsTransaction, Redemption, RedemptionSource, Reward, TransactionType
from routers.tiers import apply_tier
from schemas import RedemptionOut

router = APIRouter(tags=["Redemptions"])


@router.post("/members/{member_id}/redeem/{reward_id}", response_model=RedemptionOut, status_code=201)
def redeem_reward(member_id: UUID, reward_id: UUID, db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.id == member_id).with_for_update().first()
    if not member:
        raise HTTPException(404, "Member not found")

    reward = db.query(Reward).filter(Reward.id == reward_id).with_for_update().first()
    if not reward:
        raise HTTPException(404, "Reward not found")
    if not reward.is_active:
        raise HTTPException(400, "Reward is not active")
    if reward.stock is not None and reward.stock <= 0:
        raise HTTPException(400, "Reward is out of stock")
    if member.total_points < reward.points_cost:
        raise HTTPException(400, f"Insufficient points: has {member.total_points}, needs {reward.points_cost}")

    member.total_points -= reward.points_cost
    if reward.stock is not None:
        reward.stock -= 1

    apply_tier(db, member)

    tx = PointsTransaction(
        member_id=member.id,
        points=-reward.points_cost,
        type=TransactionType.spend,
        description=f"Redeemed: {reward.name}",
    )
    db.add(tx)

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


@router.post("/members/{member_id}/prizes/{reward_id}", response_model=RedemptionOut, status_code=201)
def assign_prize(member_id: UUID, reward_id: UUID, db: Session = Depends(get_db)):
    member = db.get(Member, member_id)
    if not member:
        raise HTTPException(404, "Member not found")

    reward = db.query(Reward).filter(Reward.id == reward_id).with_for_update().first()
    if not reward:
        raise HTTPException(404, "Reward not found")
    if not reward.is_active:
        raise HTTPException(400, "Reward is not active")
    if reward.stock is not None and reward.stock <= 0:
        raise HTTPException(400, "Reward is out of stock")

    if reward.stock is not None:
        reward.stock -= 1

    redemption = Redemption(
        member_id=member.id,
        reward_id=reward.id,
        points_spent=0,
        source=RedemptionSource.assigned,
    )
    db.add(redemption)
    db.commit()
    db.refresh(redemption)
    return redemption


@router.get("/members/{member_id}/prizes", response_model=list[RedemptionOut])
def list_member_prizes(
    member_id: UUID,
    source: Optional[RedemptionSource] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    if not db.get(Member, member_id):
        raise HTTPException(404, "Member not found")
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
):
    if not db.get(Member, member_id):
        raise HTTPException(404, "Member not found")
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
