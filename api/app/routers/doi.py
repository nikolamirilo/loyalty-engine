from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import DOITriggerRequest, DOITriggerResponse, DOIVerifyRequest, DOIVerifyResponse
from app.services.email_verification import resolve_member, trigger_verification, verify_code

router = APIRouter(prefix="/doi", tags=["DOI"])


@router.post("/trigger", response_model=DOITriggerResponse)
def trigger(body: DOITriggerRequest, db: Session = Depends(get_db)):
    member = resolve_member(db, body.email, body.member_id)
    trigger_verification(db, member)
    return {"message": "Verification code sent"}


@router.post("/verify", response_model=DOIVerifyResponse)
def verify(body: DOIVerifyRequest, db: Session = Depends(get_db)):
    member = resolve_member(db, body.email, body.member_id)
    member = verify_code(db, member, body.code)
    return {"verified": True, "email_verified_at": member.email_verified_at}
