from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base import CamelModel

# Lowercase, digits and single hyphens. The slug is accepted in place of the
# id in the X-Program-Id header, so it has to survive a URL and a shell
# argument untouched. Optional on create: left out, it is derived from the name
# (app.services.programs).
SLUG_PATTERN = r"^[a-z0-9]+(-[a-z0-9]+)*$"

# "#rrggbb" only - no names, no shorthand, no alpha. The client derives the
# hover, tint and dark-mode shades from it, and the value is written into a
# stylesheet, so it has to be exactly one well-understood shape.
HEX_COLOR_PATTERN = r"^#[0-9a-fA-F]{6}$"


class _BrandColors(CamelModel):
    """Optional brand colours. ``None`` means "the stock theme"."""

    primary_color: Optional[str] = Field(default=None, pattern=HEX_COLOR_PATTERN)
    secondary_color: Optional[str] = Field(default=None, pattern=HEX_COLOR_PATTERN)

    @field_validator("primary_color", "secondary_color")
    @classmethod
    def _lowercase(cls, value: Optional[str]) -> Optional[str]:
        return value.lower() if value else value


class ProgramCreate(_BrandColors):
    name: str = Field(min_length=1)
    slug: Optional[str] = Field(default=None, pattern=SLUG_PATTERN, max_length=64)
    description: Optional[str] = None
    is_default: bool = False


class ProgramUpdate(_BrandColors):
    """Only the fields sent are changed. ``description`` and the colours can be
    cleared with an explicit null; a null anywhere else is ignored."""

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
    # Set through PUT /programs/{id}/logo, never in a create or update body.
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    created_at: datetime


class MemberProgramOut(ProgramOut):
    """A program as seen by one person.

    ``member_id`` is their membership in it, or null when they have not joined
    it yet - which is what lets the member app offer every program in one list
    and enrol them on the way in.
    """

    member_id: Optional[UUID] = None
