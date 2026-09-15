"""Program-scoped row lookup.

``db.get(Model, id)`` bypasses every filter, so using it on a program-owned
table would let one program read and edit another's rows by id. This is the
replacement, and routers should reach for it rather than writing the filter
by hand each time.
"""

from typing import TypeVar
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.database import Base
from app.models import Program

T = TypeVar("T", bound=Base)


def get_scoped_or_404(
    db: Session, model: type[T], obj_id: UUID, program: Program, label: str
) -> T:
    """Fetch ``obj_id`` from ``model``, but only inside ``program``.

    A row that exists in another program answers 404 rather than 403: the
    caller has no business learning that it exists at all.
    """
    obj = (
        db.query(model)
        .filter(model.id == obj_id, model.program_id == program.id)
        .first()
    )
    if obj is None:
        raise HTTPException(404, f"{label} not found")
    return obj
