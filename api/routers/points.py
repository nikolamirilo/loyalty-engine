from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Member, PointsTransaction, TransactionType
from routers.tiers import apply_tier
from schemas import (
    AdjustPointsRequest,
    BalanceOut,
    EarnPointsRequest,
    PointsTransactionOut,
    SpendPointsRequest,
)

router = APIRouter(prefix="/members/{member_id}", tags=["Points"])


def _get_member_or_404(db: Session, member_id: UUID, lock: bool = False) -> Member:
    q = db.query(Member).filter(Member.id == member_id)
    if lock:
        q = q.with_for_update()
    member = q.first()
    if not member:
        raise HTTPException(404, "Member not found")
    return member


def _record(db: Session, member: Member, points: int, tx_type: TransactionType, description: str | None) -> PointsTransaction:
    tx = PointsTransaction(
        member_id=member.id,
        points=points,
        type=tx_type,
        description=description,
    )
    db.add(tx)
    member.total_points += points
    apply_tier(db, member)
    return tx


@router.get("/balance", response_model=BalanceOut)
def get_balance(member_id: UUID, db: Session = Depends(get_db)):
    member = _get_member_or_404(db, member_id)
    return BalanceOut(member_id=member.id, pointsBalance=member.total_points)


@router.post("/points/earn", response_model=PointsTransactionOut, status_code=201)
def earn_points(member_id: UUID, body: EarnPointsRequest, db: Session = Depends(get_db)):
    member = _get_member_or_404(db, member_id, lock=True)
    multiplier = member.tier.multiplier if member.tier else 1.0
    awarded = round(body.points * multiplier)
    tx = _record(db, member, awarded, TransactionType.earn, None)
    db.commit()
    db.refresh(tx)
    return tx


@router.post("/points/burn", response_model=PointsTransactionOut, status_code=201)
def burn_points(member_id: UUID, body: SpendPointsRequest, db: Session = Depends(get_db)):
    member = _get_member_or_404(db, member_id, lock=True)
    if member.total_points < body.points:
        raise HTTPException(400, f"Insufficient points: has {member.total_points}, needs {body.points}")
    tx = _record(db, member, -body.points, TransactionType.spend, None)
    db.commit()
    db.refresh(tx)
    return tx


@router.post("/points/adjust", response_model=PointsTransactionOut, status_code=201)
def adjust_points(member_id: UUID, body: AdjustPointsRequest, db: Session = Depends(get_db)):
    member = _get_member_or_404(db, member_id, lock=True)
    if member.total_points + body.points < 0:
        raise HTTPException(400, "Adjustment would result in negative balance")
    tx = _record(db, member, body.points, TransactionType.adjust, body.description)
    db.commit()
    db.refresh(tx)
    return tx


@router.get("/transactions", response_model=list[PointsTransactionOut])
def list_transactions(
    member_id: UUID,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    _get_member_or_404(db, member_id)
    return (
        db.query(PointsTransaction)
        .filter(PointsTransaction.member_id == member_id)
        .order_by(PointsTransaction.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
