"""Reward availability and prize granting.

Availability (active + in stock) used to be re-checked inline in three places,
and the prize-granting block in the challenge-completion path was a hand-copied
version of the assign-prize endpoint. Both live here now, so the rules can only
be changed in one place.
"""

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Redemption, RedemptionSource, Reward


def get_reward_or_404(db: Session, reward_id: UUID, lock: bool = False) -> Reward:
    """Load a reward, optionally with ``SELECT ... FOR UPDATE``.

    Take the lock whenever stock will be decremented, so two concurrent
    redemptions can't both see the last unit.
    """
    if lock:
        reward = db.query(Reward).filter(Reward.id == reward_id).with_for_update().first()
    else:
        reward = db.get(Reward, reward_id)
    if not reward:
        raise HTTPException(404, "Reward not found")
    return reward


def is_available(reward: Reward) -> bool:
    """True if the reward can be handed out right now (active and in stock)."""
    if not reward.is_active:
        return False
    return not (reward.stock is not None and reward.stock <= 0)


def assert_available(reward: Reward) -> None:
    """Raise the caller-facing 400 for an unavailable reward."""
    if not reward.is_active:
        raise HTTPException(400, "Reward is not active")
    if reward.stock is not None and reward.stock <= 0:
        raise HTTPException(400, "Reward is out of stock")


def consume_stock(reward: Reward) -> None:
    """Decrement finite stock. A null stock means unlimited, so it's left alone."""
    if reward.stock is not None:
        reward.stock -= 1


def grant_prize(db: Session, member_id: UUID, reward: Reward) -> Redemption:
    """Hand a reward to a member for free (``points_spent=0``, source ``assigned``).

    Assumes availability has already been checked and, if stock is finite, that
    the reward row is locked. The caller commits.
    """
    consume_stock(reward)
    redemption = Redemption(
        member_id=member_id,
        reward_id=reward.id,
        points_spent=0,
        source=RedemptionSource.assigned,
    )
    db.add(redemption)
    return redemption
