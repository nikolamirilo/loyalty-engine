"""Product availability and purchase recording.

Mirrors ``app.services.rewards``: the rules a purchase must satisfy live here
once, rather than being re-checked inline in the router.
"""

from datetime import datetime, timedelta, timezone
from typing import Collection, Dict, Tuple
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Product, Program, Purchase
from app.schemas.purchase import PurchaseStatsOut
from app.services.scoping import get_scoped_or_404


def get_product_or_404(db: Session, product_id: UUID, program: Program) -> Product:
    return get_scoped_or_404(db, Product, product_id, program, "Product")


def get_purchase_totals(db: Session, member_id: UUID) -> Tuple[int, int]:
    """Lifetime `(purchase count, total spend in cents)` for one member.

    Used by `app.services.tiers` to check a tier's spend/count conditions;
    kept separate from `get_purchase_stats` below, which computes more than a
    tier ever needs to read.
    """
    count, total_cents = (
        db.query(func.count(Purchase.id), func.coalesce(func.sum(Purchase.total_cents), 0))
        .filter(Purchase.member_id == member_id)
        .one()
    )
    return count, total_cents


def get_purchase_totals_by_member(db: Session, member_ids: Collection[UUID]) -> Dict[UUID, Tuple[int, int]]:
    """`get_purchase_totals` for many members in one query, keyed by member id.

    A member with no purchases is simply absent - callers default to `(0, 0)`.
    Used when re-checking tiers for a whole program or a batch of members, so
    that doesn't cost one purchase query per member.
    """
    if not member_ids:
        return {}
    rows = (
        db.query(Purchase.member_id, func.count(Purchase.id), func.coalesce(func.sum(Purchase.total_cents), 0))
        .filter(Purchase.member_id.in_(member_ids))
        .group_by(Purchase.member_id)
        .all()
    )
    return {member_id: (count, total_cents) for member_id, count, total_cents in rows}


def assert_purchasable(product: Product) -> None:
    """Raise the caller-facing 400 for a product that can't be bought right now."""
    if not product.is_active:
        raise HTTPException(400, "Product is not available")


def record_purchase(db: Session, member_id: UUID, product: Product, quantity: int) -> Purchase:
    """Create a purchase, snapshotting the product's current name and price.

    No balance is checked and none is debited: members pay with unlimited
    "credit card" funds, so a purchase always succeeds once the product itself
    is purchasable. The caller commits.
    """
    purchase = Purchase(
        member_id=member_id,
        product_id=product.id,
        product_name=product.name,
        quantity=quantity,
        unit_price_cents=product.price_cents,
        total_cents=product.price_cents * quantity,
        currency=product.currency,
    )
    db.add(purchase)
    return purchase


def get_purchase_stats(db: Session, member_id: UUID, period_days: int) -> PurchaseStatsOut:
    """Lifetime spend/frequency totals plus the same over the trailing
    ``period_days`` window - the input gamification campaigns personalise on.
    """
    lifetime = (
        db.query(
            func.count(Purchase.id),
            func.coalesce(func.sum(Purchase.total_cents), 0),
            func.min(Purchase.created_at),
            func.max(Purchase.created_at),
        )
        .filter(Purchase.member_id == member_id)
        .one()
    )
    count, total_cents, first_at, last_at = lifetime

    period_start = datetime.now(timezone.utc) - timedelta(days=period_days)
    period = (
        db.query(
            func.count(Purchase.id),
            func.coalesce(func.sum(Purchase.total_cents), 0),
        )
        .filter(Purchase.member_id == member_id, Purchase.created_at >= period_start)
        .one()
    )
    period_count, period_total_cents = period

    days_since_last = None
    if last_at is not None:
        last_at_utc = last_at if last_at.tzinfo else last_at.replace(tzinfo=timezone.utc)
        days_since_last = (datetime.now(timezone.utc) - last_at_utc).days

    # Currency is assumed uniform across a member's purchases (single-currency
    # catalog today); fall back to the default when there is no purchase yet.
    currency = (
        db.query(Purchase.currency)
        .filter(Purchase.member_id == member_id)
        .limit(1)
        .scalar()
        or "EUR"
    )

    return PurchaseStatsOut(
        member_id=member_id,
        currency=currency,
        purchase_count=count,
        total_spend_cents=total_cents,
        average_order_value_cents=round(total_cents / count) if count else 0,
        first_purchase_at=first_at,
        last_purchase_at=last_at,
        days_since_last_purchase=days_since_last,
        period_days=period_days,
        period_purchase_count=period_count,
        period_spend_cents=period_total_cents,
    )
