from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Reward
from app.schemas import RewardCreate, RewardOut, RewardUpdate

router = APIRouter(prefix="/rewards", tags=["Rewards"])


def _get_reward_or_404(db: Session, reward_id: UUID) -> Reward:
    reward = db.get(Reward, reward_id)
    if not reward:
        raise HTTPException(404, "Reward not found")
    return reward


@router.post("", response_model=RewardOut, status_code=201)
def create_reward(body: RewardCreate, db: Session = Depends(get_db)):
    reward = Reward(**body.model_dump())
    db.add(reward)
    db.commit()
    db.refresh(reward)
    return reward


@router.get("", response_model=list[RewardOut])
def list_rewards(
    # Aliased so the wire-level query key is camelCase like every other JSON
    # key in the API; the Python parameter stays snake_case.
    active_only: bool = Query(False, alias="activeOnly"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(Reward)
    if active_only:
        q = q.filter(Reward.is_active)
    return q.offset(skip).limit(limit).all()


@router.get("/{reward_id}", response_model=RewardOut)
def get_reward(reward_id: UUID, db: Session = Depends(get_db)):
    return _get_reward_or_404(db, reward_id)


@router.patch("/{reward_id}", response_model=RewardOut)
def update_reward(reward_id: UUID, body: RewardUpdate, db: Session = Depends(get_db)):
    reward = _get_reward_or_404(db, reward_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(reward, field, value)
    db.commit()
    db.refresh(reward)
    return reward


@router.delete("/{reward_id}", status_code=204)
def delete_reward(reward_id: UUID, db: Session = Depends(get_db)):
    reward = _get_reward_or_404(db, reward_id)
    db.delete(reward)
    db.commit()
