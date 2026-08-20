from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import EmailStr

from app.models.enums import DOIType
from app.schemas.base import CamelModel


class DOITriggerRequest(CamelModel):
    email: Optional[EmailStr] = None
    member_id: Optional[UUID] = None
    # Which email to send. Defaults to the original behaviour (a typed code) so
    # callers written before the page flow existed keep working unchanged.
    type: DOIType = DOIType.code


class DOITriggerResponse(CamelModel):
    message: str


class DOIVerifyRequest(CamelModel):
    email: Optional[EmailStr] = None
    member_id: Optional[UUID] = None
    code: str


class DOIVerifyResponse(CamelModel):
    verified: bool
    email_verified_at: datetime
