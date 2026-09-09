from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
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
def signup(body: AuthSignupRequest, db: Session = Depends(get_db)):
    trigger_signup(db, body.email, body.name, body.phone)
    return {"message": "Login code sent"}


@router.post("/login", response_model=AuthTriggerResponse)
def login(body: AuthLoginRequest, db: Session = Depends(get_db)):
    trigger_login(db, body.email)
    return {"message": "Login code sent"}


@router.post("/verify", response_model=AuthVerifyResponse)
def verify(body: AuthVerifyRequest, db: Session = Depends(get_db)):
    member = verify_login_code(db, body.email, body.code)
    return {"member": member}
