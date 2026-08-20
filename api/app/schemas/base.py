"""Shared base for every request/response schema.

JSON keys are always camelCase, while Python attribute names and ORM/DB column
names stay snake_case - `alias_generator` does that rewrite once here instead
of every field needing its own `Field(serialization_alias=...)`. FastAPI
serializes responses by alias by default, so a plain `response_model=SomeOut`
is enough to get camelCase output with no per-route configuration.

`populate_by_name=True` means a field can still be populated by its original
snake_case Python name (in addition to the camelCase alias), so:
  - `from_attributes=True` reads still work directly off ORM objects, whose
    columns are snake_case (e.g. `Member.email_verified_at`).
  - existing request payloads sent in snake_case keep validating; the alias
    is additive, not a replacement.
"""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )
