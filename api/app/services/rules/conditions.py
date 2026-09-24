"""Rule conditions: checked once when a rule is saved, evaluated on every event.

A rule's conditions are all ANDed. There is no OR and no nesting: two rules
express an OR, and keep each one readable as a single sentence.
"""

import operator
from typing import Any, Dict, List
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Program, Tier
from app.schemas import RuleCondition
from app.services.rules.fields import SEGMENTS, TIER, FieldSpec, coerce_value
from app.services.scoping import get_scoped_or_404
from app.services.segments import get_segment_or_404

# Which operators make sense for each field type.
OPERATORS: Dict[str, set[str]] = {
    "number": {"eq", "neq", "gt", "gte", "lt", "lte"},
    "text": {"eq", "neq", "contains"},
    "select": {"eq", "neq"},
    "boolean": {"eq"},
    "date": {"eq", "gt", "lt"},
    TIER: {"eq", "neq"},
    SEGMENTS: {"contains"},
}

_COMPARISONS = {"gt": operator.gt, "gte": operator.ge, "lt": operator.lt, "lte": operator.le}


def _uuid(raw: Any, spec: FieldSpec) -> UUID:
    try:
        return UUID(str(raw))
    except ValueError:
        raise HTTPException(400, f"The condition on '{spec.label}' needs an id.")


def _value(db: Session, program: Program, spec: FieldSpec, raw: Any) -> Any:
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        raise HTTPException(400, f"The condition on '{spec.label}' needs a value.")
    if spec.type == TIER:
        return str(get_scoped_or_404(db, Tier, _uuid(raw, spec), program, "Tier").id)
    if spec.type == SEGMENTS:
        return str(get_segment_or_404(db, _uuid(raw, spec), program).id)
    return coerce_value(spec, raw)


def validate_conditions(
    db: Session,
    program: Program,
    fields: Dict[str, FieldSpec],
    conditions: List[RuleCondition],
) -> List[Dict[str, Any]]:
    """Check each condition against ``fields`` and return them ready to store,
    with values coerced to their field's type."""
    out = []
    for condition in conditions:
        spec = fields.get(condition.field)
        if spec is None:
            raise HTTPException(400, f"Unknown condition field '{condition.field}'.")
        if condition.operator not in OPERATORS[spec.type]:
            raise HTTPException(400, f"'{spec.label}' can't be compared with '{condition.operator}'.")
        out.append(
            {
                "field": condition.field,
                "operator": condition.operator,
                "value": _value(db, program, spec, condition.value),
            }
        )
    return out


def _holds(actual: Any, op: str, expected: Any) -> bool:
    if op == "contains":
        if isinstance(actual, list):
            return expected in actual
        return isinstance(actual, str) and str(expected).lower() in actual.lower()
    if op == "eq":
        return actual == expected
    if op == "neq":
        return actual != expected
    # A missing value is never more or less than anything.
    if actual is None:
        return False
    try:
        return _COMPARISONS[op](actual, expected)
    except TypeError:
        return False


def matches(conditions: List[Dict[str, Any]], context: Dict[str, Any]) -> bool:
    """True if every stored condition holds against ``context`` (see
    ``fields.build_context``). No conditions always match."""
    return all(_holds(context.get(c["field"]), c["operator"], c["value"]) for c in conditions)
