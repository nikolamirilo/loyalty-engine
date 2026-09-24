"""The condition mini-language shared by event rules and tier definitions.

A condition is one ``field <operator> value`` check. ``field`` is a path such
as ``event.attributes.<key>`` (event rules only), ``member.pointsBalance``,
``member.purchaseSpendCents``, ``member.tier`` (a tier id, event rules only),
``member.segments`` (a segment id, with ``contains``) or
``member.customAttributes.<key>``.

What a caller can actually reference is decided by its own field list
(``app.services.rules.fields.readable_fields`` for events, ``tier_fields`` for
tiers) and both are checked and evaluated by the same code
(``app.services.rules.conditions``), so an event rule's "if" and a tier's
eligibility rule read the same way and behave the same way.
"""

from typing import Any, Literal

from app.schemas.base import CamelModel

Operator = Literal["eq", "neq", "gt", "gte", "lt", "lte", "contains"]


class RuleCondition(CamelModel):
    field: str
    operator: Operator
    value: Any
