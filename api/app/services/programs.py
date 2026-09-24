"""Program slugs: the readable handle a program can be addressed by.

The console only asks for a name, so the slug is derived from it here. It is
fixed once the program exists - renaming the program leaves it alone - because
``MEMBER_PROGRAM``, the MCP server's default program, MCP calls and curl
examples may already refer to it.
"""

import re
import unicodedata

from sqlalchemy.orm import Session

from app.models import Program

_MAX_SLUG_LENGTH = 64  # ProgramCreate.slug's max_length
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


def slug_from_name(name: str) -> str:
    """``"Café Club Rewards!"`` -> ``"cafe-club-rewards"``.

    Falls back to ``"program"`` for a name with nothing ASCII to keep.
    """
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    slug = _NON_ALNUM_RE.sub("-", ascii_name.lower()).strip("-")
    return slug[:_MAX_SLUG_LENGTH].rstrip("-") or "program"


def unique_slug(db: Session, name: str) -> str:
    """A slug for a new program named ``name`` that no program holds yet.

    A taken slug gets the first free numeric suffix: ``coffee-club-2``, ``-3``…
    Reading every slug is fine at the handful of programs a deployment has.
    """
    base = slug_from_name(name)
    taken = {slug for (slug,) in db.query(Program.slug).all()}
    candidate, n = base, 2
    while candidate in taken:
        suffix = f"-{n}"
        candidate = base[: _MAX_SLUG_LENGTH - len(suffix)].rstrip("-") + suffix
        n += 1
    return candidate
