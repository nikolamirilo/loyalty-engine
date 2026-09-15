from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import CamelModel

# Lowercase, digits and single hyphens. The slug is accepted in place of the
# id in the X-Program-Id header, so it has to survive a URL and a shell
# argument untouched.
SLUG_PATTERN = r"^[a-z0-9]+(-[a-z0-9]+)*$"


class ProgramCreate(CamelModel):
    name: str = Field(min_length=1)
    slug: str = Field(pattern=SLUG_PATTERN, max_length=64)
    description: Optional[str] = None
    is_default: bool = False


class ProgramUpdate(CamelModel):
    name: Optional[str] = Field(default=None, min_length=1)
    slug: Optional[str] = Field(default=None, pattern=SLUG_PATTERN, max_length=64)
    description: Optional[str] = None
    is_default: Optional[bool] = None


class ProgramOut(CamelModel):
    id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    is_default: bool
    created_at: datetime


class MemberProgramOut(ProgramOut):
    """A program as seen by one person.

    ``member_id`` is their membership in it, or null when they have not joined
    it yet - which is what lets the member app offer every program in one list
    and enrol them on the way in.
    """

    member_id: Optional[UUID] = None
