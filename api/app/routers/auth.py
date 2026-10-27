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

# No X-Program-Id here: every member belongs to every program, and signing in
# always lands in the default program - the member switches from there. A
# header sent anyway is ignored.
router = APIRouter(prefix="/auth", tags=["Auth"])

# One answer for signup and login, whether or not the email has an account (or
# a code went out moments ago), so it never reveals which addresses are
# registered. See app/services/member_auth.py.
SENT = "If this email has an account, a login code is on its way."


@router.post("/signup", response_model=AuthTriggerResponse)
def signup(
    body: AuthSignupRequest,
    db: Session = Depends(get_db),
):
    trigger_signup(db, body.email, body.name, body.phone)
    return {"message": SENT}


@router.post("/login", response_model=AuthTriggerResponse)
def login(
    body: AuthLoginRequest,
    db: Session = Depends(get_db),
):
    trigger_login(db, body.email)
    return {"message": SENT}


@router.post("/verify", response_model=AuthVerifyResponse)
def verify(
    body: AuthVerifyRequest,
    db: Session = Depends(get_db),
):
    member = verify_login_code(db, body.email, body.code)
    return {"member": member}
