from typing import Optional

from pydantic import EmailStr

from app.schemas.base import CamelModel
from app.schemas.member import MemberOut


class AuthSignupRequest(CamelModel):
    email: EmailStr
    name: str
    phone: Optional[str] = None


class AuthLoginRequest(CamelModel):
    email: EmailStr


class AuthTriggerResponse(CamelModel):
    message: str


class AuthVerifyRequest(CamelModel):
    email: EmailStr
    code: str


class AuthVerifyResponse(CamelModel):
    member: MemberOut
