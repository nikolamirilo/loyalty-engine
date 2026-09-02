"""One-off data migration: rename existing snake_case custom-attribute keys to
camelCase, to match `slugify()`'s new convention (app/services/custom_attributes.py).

Only the *key format* changes (e.g. "weekly_score" -> "weeklyScore"); values,
labels, types, and options are untouched. Renames both:
  - `member_attributes.key` (the definition)
  - every matching key inside every member's `custom_attributes` JSONB

Dry-run by default - prints the rename plan and exits without writing. Pass
--commit to actually apply it.

Run from `api/`:
    ./venv/bin/python -m scripts.migrate_custom_attribute_keys_to_camel
    ./venv/bin/python -m scripts.migrate_custom_attribute_keys_to_camel --commit
"""

import argparse
import re

from app.core.database import SessionLocal
from app.models import Member, MemberAttribute

_WORD_RE = re.compile(r"[A-Za-z0-9]+")


def to_camel(key: str) -> str:
    """Convert an existing snake_case key to camelCase.

    A key with no separator left (already camelCase, or a single word) is
    returned unchanged - splitting it further would just lowercase the whole
    thing and destroy the existing camel humps. That also makes this
    idempotent: re-running the migration on already-converted keys is a no-op.
    """
    if "_" not in key:
        return key
    words = _WORD_RE.findall(key)
    if not words:
        return key
    return words[0].lower() + "".join(w.capitalize() for w in words[1:])


def build_plan(db) -> dict[str, str]:
    """Map old key -> new key for every attribute whose key actually changes."""
    attributes = db.query(MemberAttribute).all()
    plan: dict[str, str] = {}
    seen_new_keys: dict[str, str] = {}

    for attribute in attributes:
        new_key = to_camel(attribute.key)
        final_new_key = attribute.key if new_key == attribute.key else new_key
        if final_new_key in seen_new_keys and seen_new_keys[final_new_key] != attribute.key:
            raise RuntimeError(
                f"Key collision: both '{attribute.key}' and "
                f"'{seen_new_keys[final_new_key]}' would map to '{final_new_key}'. "
                "Resolve manually before re-running."
            )
        seen_new_keys[final_new_key] = attribute.key
        if new_key != attribute.key:
            plan[attribute.key] = new_key

    return plan


def apply_plan(db, plan: dict[str, str]) -> int:
    members_touched = 0

    for attribute in db.query(MemberAttribute).filter(MemberAttribute.key.in_(plan.keys())).all():
        attribute.key = plan[attribute.key]

    for member in db.query(Member).all():
        attrs = member.custom_attributes or {}
        if not any(old_key in attrs for old_key in plan):
            continue
        new_attrs = dict(attrs)
        for old_key, new_key in plan.items():
            if old_key in new_attrs:
                new_attrs[new_key] = new_attrs.pop(old_key)
        member.custom_attributes = new_attrs  # reassign - JSONB isn't change-tracked in place
        members_touched += 1

    return members_touched


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--commit", action="store_true", help="Actually write the changes (default: dry-run)."
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        plan = build_plan(db)
        if not plan:
            print("Nothing to do - every attribute key is already camelCase.")
            return

        print(f"{len(plan)} attribute key(s) to rename:")
        for old_key, new_key in plan.items():
            print(f"  {old_key!r} -> {new_key!r}")

        if not args.commit:
            print("\nDry run only - re-run with --commit to apply.")
            return

        members_touched = apply_plan(db, plan)
        db.commit()
        print(f"\nDone: {len(plan)} attribute definition(s), {members_touched} member(s) updated.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
