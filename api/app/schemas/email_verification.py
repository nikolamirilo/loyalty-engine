from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


class DOITriggerRequest(BaseModel):
    email: Optional[EmailStr] = None
    member_id: Optional[UUID] = None


class DOITriggerResponse(BaseModel):
    message: str


class DOIVerifyRequest(BaseModel):
    email: Optional[EmailStr] = None
    member_id: Optional[UUID] = None
    code: str


class DOIVerifyResponse(BaseModel):
    verified: bool
    email_verified_at: datetime
