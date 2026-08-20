from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import DOIType
from app.schemas import DOITriggerRequest, DOITriggerResponse, DOIVerifyRequest, DOIVerifyResponse
from app.services.email_verification import resolve_member, trigger_verification, verify_code

router = APIRouter(prefix="/doi", tags=["DOI"])

# What the member was actually sent, so the caller can tell them what to look
# for without having to re-derive it from the request.
MESSAGES = {
    DOIType.code: "Verification code sent",
    DOIType.page: "Verification link sent",
}


@router.post("/trigger", response_model=DOITriggerResponse)
def trigger(body: DOITriggerRequest, db: Session = Depends(get_db)):
    member = resolve_member(db, body.email, body.member_id)
    # Whether this issued a new code or left a still-valid one in place, the
    # caller's request is satisfied the same way: there's an email in that inbox.
    trigger_verification(db, member, body.type)
    return {"message": MESSAGES[body.type]}


@router.post("/verify", response_model=DOIVerifyResponse)
def verify(body: DOIVerifyRequest, db: Session = Depends(get_db)):
    member = resolve_member(db, body.email, body.member_id)
    member = verify_code(db, member, body.code)
    return {"verified": True, "email_verified_at": member.email_verified_at}
