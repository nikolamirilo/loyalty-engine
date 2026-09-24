"""The event rule engine.

A rule reads as one sentence: when an event of this type arrives, if all of
these conditions hold, do all of these effects. ``fields`` says what a rule can
reference, ``conditions`` checks and evaluates the "if", and ``effects`` holds
one handler per "do". ``app.services.events`` runs them for each event.
"""

from typing import Any, Dict, List, Tuple

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models import EventType, Program
from app.schemas import RuleCondition
from app.services.rules.conditions import validate_conditions
from app.services.rules.effects import validate_effects
from app.services.rules.fields import readable_fields


def validate_rule(
    db: Session,
    program: Program,
    event_type: EventType,
    conditions: List[RuleCondition],
    effects: List[BaseModel],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Check a rule before it is saved and return its conditions and effects
    ready to store. Raises a 400 naming the first problem found."""
    return (
        validate_conditions(db, program, readable_fields(db, program, event_type), conditions),
        validate_effects(db, program, event_type, effects),
    )
