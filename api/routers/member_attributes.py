from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import String, cast, literal
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

from custom_attributes import coerce, normalize_options, slugify
from database import get_db
from models import Member, MemberAttribute
from schemas import MemberAttributeCreate, MemberAttributeOut, MemberAttributeUpdate

# Mounted at its own prefix rather than under /members/... so the path can never
# be parsed as a member id (see the ordering comment in routers/members.py).
router = APIRouter(prefix="/member-attributes", tags=["Member attributes"])


def _get_attribute_or_404(db: Session, attribute_id: UUID) -> MemberAttribute:
    attribute = db.get(MemberAttribute, attribute_id)
    if not attribute:
        raise HTTPException(404, "Custom attribute not found")
    return attribute


def _merge_into_all_members(db: Session, patch: Dict[str, Any]) -> None:
    """Merge `patch` into every member's custom_attributes in one statement."""
    db.query(Member).update(
        {
            Member.custom_attributes: Member.custom_attributes.op("||", return_type=JSONB)(
                cast(patch, JSONB)
            )
        },
        synchronize_session=False,
    )


@router.post("", response_model=MemberAttributeOut, status_code=201)
def create_attribute(body: MemberAttributeCreate, db: Session = Depends(get_db)):
    key = slugify(body.label)
    if db.query(MemberAttribute).filter(MemberAttribute.key == key).first():
        raise HTTPException(400, f"A custom attribute with the key '{key}' already exists")

    attribute = MemberAttribute(
        key=key,
        label=body.label.strip(),
        type=body.type.value,
        options=normalize_options(body.type.value, body.options),
    )
    # coerce() reads .type/.options off the instance, so build it before validating.
    attribute.default_value = coerce(attribute, body.default_value)

    db.add(attribute)

    # Seed the default onto every existing member so the field is populated
    # program-wide. With no default there's nothing to write: the console renders
    # from the definitions list, so an absent key and a null value look identical.
    if attribute.default_value is not None:
        _merge_into_all_members(db, {attribute.key: attribute.default_value})

    db.commit()
    db.refresh(attribute)
    return attribute


@router.get("", response_model=list[MemberAttributeOut])
def list_attributes(db: Session = Depends(get_db)):
    return db.query(MemberAttribute).order_by(MemberAttribute.created_at).all()


@router.get("/{attribute_id}", response_model=MemberAttributeOut)
def get_attribute(attribute_id: UUID, db: Session = Depends(get_db)):
    return _get_attribute_or_404(db, attribute_id)


@router.patch("/{attribute_id}", response_model=MemberAttributeOut)
def update_attribute(
    attribute_id: UUID, body: MemberAttributeUpdate, db: Session = Depends(get_db)
):
    attribute = _get_attribute_or_404(db, attribute_id)
    data = body.model_dump(exclude_unset=True)

    if "label" in data and data["label"]:
        attribute.label = data["label"].strip()
    if "options" in data:
        attribute.options = normalize_options(attribute.type, data["options"])
    if "default_value" in data:
        # Editing the default deliberately does not re-run the backfill: defaults
        # apply when the attribute is created and when a member is created, so an
        # edit here can't silently overwrite values an admin has already set.
        attribute.default_value = coerce(attribute, data["default_value"])

    db.commit()
    db.refresh(attribute)
    return attribute


@router.delete("/{attribute_id}", status_code=204)
def delete_attribute(attribute_id: UUID, db: Session = Depends(get_db)):
    attribute = _get_attribute_or_404(db, attribute_id)
    # Strip the key from every member in the same transaction, so no orphaned
    # values are left behind that a re-created attribute would silently inherit.
    # The key is bound as text explicitly: `jsonb - jsonb` is not an operator,
    # only `jsonb - text`, and the default coercion would type it from the left.
    db.query(Member).update(
        {
            Member.custom_attributes: Member.custom_attributes.op("-", return_type=JSONB)(
                literal(attribute.key, String)
            )
        },
        synchronize_session=False,
    )
    db.delete(attribute)
    db.commit()
