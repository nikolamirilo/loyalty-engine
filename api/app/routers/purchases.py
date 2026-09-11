from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models import Member, Purchase
from app.schemas import PurchaseCreate, PurchaseOut, PurchaseStatsOut
from app.services.products import assert_purchasable, get_product_or_404, get_purchase_stats, record_purchase

router = APIRouter(tags=["Purchases"])

DEFAULT_STATS_PERIOD_DAYS = 7


@router.post("/members/{member_id}/purchases", response_model=PurchaseOut, status_code=201)
def purchase_product(member_id: UUID, body: PurchaseCreate, db: Session = Depends(get_db)):
    if not db.get(Member, member_id):
        raise HTTPException(404, "Member not found")

    product = get_product_or_404(db, body.product_id)
    assert_purchasable(product)

    # No balance is checked and nothing is debited: members pay by "credit
    # card" with unlimited funds, so a purchase always succeeds once the
    # product itself is purchasable.
    purchase = record_purchase(db, member_id, product, body.quantity)
    db.commit()
    db.refresh(purchase)
    return purchase


@router.get("/members/{member_id}/purchases", response_model=list[PurchaseOut])
def list_member_purchases(
    member_id: UUID,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    if not db.get(Member, member_id):
        raise HTTPException(404, "Member not found")
    # joinedload the product so a deleted product (product_id set NULL) doesn't
    # trigger a lazy-load per row, and so an active product isn't N+1 either.
    return (
        db.query(Purchase)
        .options(joinedload(Purchase.product))
        .filter(Purchase.member_id == member_id)
        .order_by(Purchase.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/members/{member_id}/purchase-stats", response_model=PurchaseStatsOut)
def member_purchase_stats(
    member_id: UUID,
    # How many trailing days the period* fields cover (e.g. 7, 30, 90).
    days: int = Query(DEFAULT_STATS_PERIOD_DAYS, gt=0, le=365),
    db: Session = Depends(get_db),
):
    if not db.get(Member, member_id):
        raise HTTPException(404, "Member not found")
    return get_purchase_stats(db, member_id, days)
