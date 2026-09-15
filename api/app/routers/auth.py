from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.program import get_program
from app.models import Program
from app.schemas import (
    AuthLoginRequest,
    AuthSignupRequest,
    AuthTriggerResponse,
    AuthVerifyRequest,
    AuthVerifyResponse,
)
from app.services.member_auth import trigger_login, trigger_signup, verify_login_code

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup", response_model=AuthTriggerResponse)
def signup(
    body: AuthSignupRequest,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    trigger_signup(db, program, body.email, body.name, body.phone)
    return {"message": "Login code sent"}


@router.post("/login", response_model=AuthTriggerResponse)
def login(
    body: AuthLoginRequest,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    trigger_login(db, program, body.email)
    return {"message": "Login code sent"}


@router.post("/verify", response_model=AuthVerifyResponse)
def verify(
    body: AuthVerifyRequest,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    member = verify_login_code(db, program, body.email, body.code)
    return {"member": member}
