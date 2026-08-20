from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import EmailStr

from app.schemas.base import CamelModel


class DOITriggerRequest(CamelModel):
    email: Optional[EmailStr] = None
    member_id: Optional[UUID] = None


class DOITriggerResponse(CamelModel):
    message: str


class DOIVerifyRequest(CamelModel):
    email: Optional[EmailStr] = None
    member_id: Optional[UUID] = None
    code: str


class DOIVerifyResponse(CamelModel):
    verified: bool
    email_verified_at: datetime
