"""One-off data migration: give every person a membership in every program.

Members are global (app/services/memberships.py): a person belongs to every
program, holding one `members` row each, which is where their points, tier and
progress live. Rows written before that rule existed only cover the programs
someone actually signed into, so this fills the gaps.

Creates nothing but empty memberships - zero points, the program's own lowest
tier and attribute defaults. No existing membership is read or modified, so a
member's standing in a program they already belong to cannot change.

Dry-run by default - prints what it would create and exits without writing.
Pass --commit to actually apply it.

Run from `api/`:
    ./venv/bin/python -m scripts.enrol_members_in_all_programs
    ./venv/bin/python -m scripts.enrol_members_in_all_programs --commit
"""

import argparse

from app.core.database import SessionLocal
from app.models import Member, MemberIdentity, Program
from app.services.memberships import backfill


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", action="store_true", help="apply the changes")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        identities = db.query(MemberIdentity).count()
        programs = db.query(Program).order_by(Program.created_at.asc()).all()
        existing = db.query(Member).count()
        expected = identities * len(programs)

        print(f"people:    {identities}")
        print(f"programs:  {len(programs)}")
        print(f"memberships now: {existing}  ->  expected when total: {expected}")
        print()
        for p in programs:
            have = db.query(Member).filter(Member.program_id == p.id).count()
            print(f"  {p.name:20} {have}/{identities}  (missing {identities - have})")
        print()

        created = backfill(db)
        if not args.commit:
            db.rollback()
            print(f"DRY RUN: would create {created} membership(s). Re-run with --commit.")
            return

        db.commit()
        print(f"created {created} membership(s).")
        for p in programs:
            have = db.query(Member).filter(Member.program_id == p.id).count()
            print(f"  {p.name:20} {have}/{identities}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
