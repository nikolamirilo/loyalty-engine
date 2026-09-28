from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import DOIType
from app.schemas import DOITriggerRequest, DOITriggerResponse, DOIVerifyRequest, DOIVerifyResponse
from app.services.email_verification import resolve_member, trigger_verification, verify_code

# No X-Program-Id here: every member belongs to every program and their email
# verification is global, so which program a caller addresses changes nothing.
# A header sent anyway is ignored.
router = APIRouter(prefix="/doi", tags=["DOI"])

# What the member was actually sent, so the caller can tell them what to look
# for without having to re-derive it from the request.
MESSAGES = {
    DOIType.code: "Verification code sent",
    DOIType.link: "Verification link sent",
}


@router.post("/trigger", response_model=DOITriggerResponse)
def trigger(body: DOITriggerRequest, db: Session = Depends(get_db)):
    member = resolve_member(db, body.email, body.member_id)
    # Always a fresh email, or a 429 if the last one went out moments ago.
    trigger_verification(db, member, body.type)
    return {"message": MESSAGES[body.type]}


@router.post("/verify", response_model=DOIVerifyResponse)
def verify(body: DOIVerifyRequest, db: Session = Depends(get_db)):
    member = resolve_member(db, body.email, body.member_id)
    member = verify_code(db, member, body.code)
    return {"verified": True, "email_verified_at": member.email_verified_at}
