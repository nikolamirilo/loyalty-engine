"""Program resolution for a request.

Authentication (``app.core.security``) answers *who* may call. This answers
*which program* the call belongs to, and the two are deliberately separate:
one shared bearer token keeps working, and a caller switches program per
request rather than per deployment. That is what lets the admin console's
program switcher work without a token per program.

Every program-scoped router takes ``program: Program = Depends(get_program)``
and filters by ``program.id``. Two kinds of router do not:

  * ``/programs`` itself - it is how a caller discovers which programs exist.
  * Person-level flows (``/doi/*``, ``/auth/*``). Every member belongs to every
    program and their email verification is global, so there is no program to
    pick: DOI never needs one, and sign-in always lands in the default program
    (``default_program``), from where the member switches.
"""

import logging
from uuid import UUID

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.monitoring import tag_program
from app.models import Program

logger = logging.getLogger("uvicorn.error")

PROGRAM_HEADER = "X-Program-Id"


def _by_id_or_slug(db: Session, value: str) -> Program | None:
    try:
        return db.get(Program, UUID(value))
    except ValueError:
        # Not a UUID, so treat it as a slug. Slugs keep curl examples and MCP
        # calls readable ("retail-demo" rather than a random UUID).
        return db.query(Program).filter(Program.slug == value).first()


def default_program(db: Session) -> Program:
    """The program flagged ``is_default``."""
    program = db.query(Program).filter(Program.is_default.is_(True)).first()
    if program is None:
        raise HTTPException(400, "No default program is configured.")
    return program


def get_program(
    x_program_id: str | None = Header(
        default=None,
        alias=PROGRAM_HEADER,
        description=(
            "Which program this request works on: a program id (UUID) or slug, "
            "from `GET /programs`. Leave it out to use the default program."
        ),
    ),
    db: Session = Depends(get_db),
) -> Program:
    """The program this request addresses.

    Falls back to the program flagged ``is_default`` when the header is
    absent, so a caller that predates this header (an external integration,
    an older MCP deployment) keeps working instead of breaking on deploy.
    """
    if x_program_id:
        program = _by_id_or_slug(db, x_program_id)
        if program is None:
            raise HTTPException(404, f"Program not found: {x_program_id}")
        tag_program(program.slug)
        return program

    program = db.query(Program).filter(Program.is_default.is_(True)).first()
    if program is None:
        raise HTTPException(
            400,
            f"No {PROGRAM_HEADER} header was sent and no default program is configured.",
        )
    # A caller that forgot the header still writes somewhere, which looks like
    # success. Leave a trace so it is findable after the fact.
    logger.warning(
        "Request without %s fell back to the default program %r",
        PROGRAM_HEADER,
        program.slug,
    )
    tag_program(program.slug)
    return program
