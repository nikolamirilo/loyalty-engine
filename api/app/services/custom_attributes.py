"""Type rules for admin-defined member custom attributes.

Values live in a JSONB column, which enforces nothing on its own - so this
module is the single place a value is checked against its definition. Every
write path (member create, member update, attribute default) goes through
``coerce`` or ``validate_payload``.
"""

import re
from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import MemberAttribute, MemberAttributeType

# The pragmatic intersection of what HubSpot, Braze and Bloomreach offer.
ATTRIBUTE_TYPES = tuple(t.value for t in MemberAttributeType)

_WORD_RE = re.compile(r"[A-Za-z0-9]+")
_MAX_KEY_LENGTH = 63  # Postgres identifier limit; keeps keys promotable to columns later.
_MAX_TEXT_LENGTH = 500


def slugify(label: str) -> str:
    """Derive a stable internal key from a human label.

    ``"Favourite colour!"`` -> ``"favouriteColour"`` - camelCase, matching the
    camelCase convention every other JSON key in the API uses. The result is
    immutable once the attribute exists, which is why it must not depend on
    anything editable beyond the label the admin first typed.
    """
    words = _WORD_RE.findall(label)
    key = (words[0].lower() + "".join(w.capitalize() for w in words[1:]))[:_MAX_KEY_LENGTH] if words else ""
    if not key or not key[0].isalpha():
        raise HTTPException(
            400,
            "Label must contain at least one letter and start with one, "
            "so a valid internal key can be derived from it.",
        )
    return key


def normalize_options(type_: str, options: Optional[List[str]]) -> Optional[List[str]]:
    """Validate the choice list for a `select` attribute; ignored for other types."""
    if type_ != MemberAttributeType.select.value:
        return None
    cleaned = [o.strip() for o in (options or []) if o and o.strip()]
    # dict.fromkeys dedupes while preserving the admin's ordering.
    cleaned = list(dict.fromkeys(cleaned))
    if not cleaned:
        raise HTTPException(400, "A dropdown attribute needs at least one option.")
    return cleaned


def coerce(attribute: MemberAttribute, raw: Any) -> Any:
    """Coerce and validate one value against its definition.

    ``None`` is always allowed - no custom attribute is mandatory. Returns a
    JSON-serializable value ready to store.
    """
    if raw is None:
        return None

    label = attribute.label
    type_ = attribute.type

    if type_ == MemberAttributeType.boolean.value:
        if isinstance(raw, bool):
            return raw
        if isinstance(raw, str) and raw.strip().lower() in ("true", "false"):
            return raw.strip().lower() == "true"
        raise HTTPException(400, f"'{label}' must be true or false.")

    if type_ == MemberAttributeType.number.value:
        # bool is a subclass of int, so reject it explicitly rather than storing 1/0.
        if isinstance(raw, bool):
            raise HTTPException(400, f"'{label}' must be a number.")
        if isinstance(raw, (int, float)):
            return raw
        try:
            return float(str(raw).strip())
        except (TypeError, ValueError):
            raise HTTPException(400, f"'{label}' must be a number.")

    if type_ == MemberAttributeType.date.value:
        try:
            return date.fromisoformat(str(raw).strip()).isoformat()
        except (TypeError, ValueError):
            raise HTTPException(400, f"'{label}' must be a date in YYYY-MM-DD format.")

    if type_ == MemberAttributeType.select.value:
        value = str(raw).strip()
        if value not in (attribute.options or []):
            allowed = ", ".join(attribute.options or []) or "none"
            raise HTTPException(400, f"'{label}' must be one of: {allowed}.")
        return value

    # text
    value = str(raw).strip()
    if len(value) > _MAX_TEXT_LENGTH:
        raise HTTPException(400, f"'{label}' must be {_MAX_TEXT_LENGTH} characters or fewer.")
    return value or None


def validate_payload(db: Session, payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Coerce a ``{key: value}`` map against the current definitions.

    Unknown keys are rejected rather than stored, so the column can't drift into
    a junk drawer and typos surface immediately instead of vanishing.
    """
    if not payload:
        return {}

    attributes = {a.key: a for a in db.query(MemberAttribute).all()}
    unknown = [key for key in payload if key not in attributes]
    if unknown:
        raise HTTPException(400, f"Unknown custom attribute(s): {', '.join(sorted(unknown))}")

    return {key: coerce(attributes[key], value) for key, value in payload.items()}


def defaults_for_new_member(db: Session) -> Dict[str, Any]:
    """The default values to seed on a member created without explicit values."""
    return {
        a.key: a.default_value
        for a in db.query(MemberAttribute).all()
        if a.default_value is not None
    }
