from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.program import get_program
from app.models import Program, Reward
from app.schemas import RewardCreate, RewardOut, RewardUpdate
from app.services.scoping import get_scoped_or_404

router = APIRouter(prefix="/rewards", tags=["Rewards"])


def _get_reward_or_404(db: Session, reward_id: UUID, program: Program) -> Reward:
    return get_scoped_or_404(db, Reward, reward_id, program, "Reward")


@router.post("", response_model=RewardOut, status_code=201)
def create_reward(
    body: RewardCreate,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    reward = Reward(**body.model_dump(), program_id=program.id)
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
    program: Program = Depends(get_program),
):
    q = db.query(Reward).filter(Reward.program_id == program.id)
    if active_only:
        q = q.filter(Reward.is_active)
    return q.offset(skip).limit(limit).all()


@router.get("/{reward_id}", response_model=RewardOut)
def get_reward(
    reward_id: UUID,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    return _get_reward_or_404(db, reward_id, program)


@router.patch("/{reward_id}", response_model=RewardOut)
def update_reward(
    reward_id: UUID,
    body: RewardUpdate,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    reward = _get_reward_or_404(db, reward_id, program)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(reward, field, value)
    db.commit()
    db.refresh(reward)
    return reward


@router.delete("/{reward_id}", status_code=204)
def delete_reward(
    reward_id: UUID,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    reward = _get_reward_or_404(db, reward_id, program)
    db.delete(reward)
    db.commit()
