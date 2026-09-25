"""Program administration.

The only router that is not program-scoped: it is how a caller discovers
which programs exist and creates new ones, so it cannot itself require an
``X-Program-Id``.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Program
from app.schemas import ProgramCreate, ProgramOut, ProgramUpdate
from app.services.memberships import enrol_all_identities
from app.services.program_branding import detect_logo_type, logo_path
from app.services.programs import unique_slug
from app.services.storage import ObjectStorage, get_optional_storage, get_storage

router = APIRouter(prefix="/programs", tags=["Programs"])

# Nullable columns a PATCH may clear by sending an explicit null. Any other
# null (name, slug, isDefault) means "leave unchanged", as it always has.
_CLEARABLE_FIELDS = {"description", "primary_color", "secondary_color"}

# The logo upload takes the raw image as the request body, so document that
# rather than leaving the endpoint looking body-less in /docs.
_LOGO_BODY = {
    "requestBody": {
        "required": True,
        "content": {
            media_type: {"schema": {"type": "string", "format": "binary"}}
            for media_type in ("image/png", "image/jpeg", "image/webp", "image/svg+xml")
        },
    }
}


def _get_program_or_404(db: Session, program_id: UUID) -> Program:
    program = db.get(Program, program_id)
    if not program:
        raise HTTPException(404, "Program not found")
    return program


def _clear_existing_default(db: Session, keep_id: UUID | None = None) -> None:
    """Demote whichever program is currently the default.

    Only one program may carry the flag (a partial unique index enforces it),
    so promoting one has to demote the other in the same transaction.
    """
    query = db.query(Program).filter(Program.is_default.is_(True))
    if keep_id is not None:
        query = query.filter(Program.id != keep_id)
    for program in query.all():
        program.is_default = False


@router.post("", response_model=ProgramOut, status_code=201)
def create_program(body: ProgramCreate, db: Session = Depends(get_db)):
    # The console sends only a name; API callers may still choose their own slug.
    if body.slug is None:
        slug = unique_slug(db, body.name)
    elif db.query(Program).filter(Program.slug == body.slug).first():
        raise HTTPException(400, f"A program with the slug {body.slug!r} already exists")
    else:
        slug = body.slug
    if body.is_default:
        _clear_existing_default(db)
    program = Program(**{**body.model_dump(), "slug": slug})
    db.add(program)
    db.flush()
    # Members are global, so a new program opens holding everyone already - each
    # at zero, with this program's own attribute defaults and lowest tier.
    enrol_all_identities(db, program)
    db.commit()
    db.refresh(program)
    return program


@router.get("", response_model=list[ProgramOut])
def list_programs(db: Session = Depends(get_db)):
    return db.query(Program).order_by(Program.created_at.asc()).all()


@router.get("/{program_id}", response_model=ProgramOut)
def get_program_by_id(program_id: UUID, db: Session = Depends(get_db)):
    return _get_program_or_404(db, program_id)


@router.patch("/{program_id}", response_model=ProgramOut)
def update_program(program_id: UUID, body: ProgramUpdate, db: Session = Depends(get_db)):
    program = _get_program_or_404(db, program_id)
    if body.slug is not None and body.slug != program.slug:
        if db.query(Program).filter(Program.slug == body.slug, Program.id != program_id).first():
            raise HTTPException(400, f"A program with the slug {body.slug!r} already exists")
    if body.is_default:
        _clear_existing_default(db, keep_id=program_id)
    elif body.is_default is False and program.is_default:
        # Clearing the last default leaves every header-less request with
        # nothing to resolve to - a 400 on a route that worked a moment ago,
        # from an edit that looked unrelated. Promote a replacement instead,
        # which is the same rule DELETE enforces.
        raise HTTPException(
            400,
            "Cannot unset the default program. Make another program the default instead.",
        )
    for field, value in body.model_dump(exclude_unset=True).items():
        if value is None and field not in _CLEARABLE_FIELDS:
            continue
        setattr(program, field, value)
    db.commit()
    db.refresh(program)
    return program


@router.put("/{program_id}/logo", response_model=ProgramOut, openapi_extra=_LOGO_BODY)
async def upload_program_logo(
    program_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    storage: ObjectStorage = Depends(get_storage),
):
    """Replace the program's logo with the image sent as the raw request body.

    PNG, JPEG, WebP or SVG, up to 2 MB. The file goes to the public Supabase
    Storage bucket and ``logoUrl`` points at it; the previous logo is removed.
    """
    program = _get_program_or_404(db, program_id)
    data = await request.body()
    content_type = detect_logo_type(data)

    new_url = await run_in_threadpool(
        storage.upload, logo_path(program.id, content_type), data, content_type
    )
    old_url = program.logo_url
    program.logo_url = new_url
    db.commit()
    db.refresh(program)
    # Only once the program points at the new file, so a failure in between
    # never leaves it pointing at nothing.
    if old_url:
        await run_in_threadpool(storage.delete_url, old_url)
    return program


@router.delete("/{program_id}/logo", response_model=ProgramOut)
def remove_program_logo(
    program_id: UUID,
    db: Session = Depends(get_db),
    storage: ObjectStorage | None = Depends(get_optional_storage),
):
    """Go back to the stock logo. The stored file is deleted too."""
    program = _get_program_or_404(db, program_id)
    old_url = program.logo_url
    program.logo_url = None
    db.commit()
    db.refresh(program)
    if old_url and storage is not None:
        storage.delete_url(old_url)
    return program


@router.delete("/{program_id}", status_code=204)
def delete_program(
    program_id: UUID,
    db: Session = Depends(get_db),
    storage: ObjectStorage | None = Depends(get_optional_storage),
):
    """Delete a program and everything inside it.

    Every program-owned table cascades, which is the fast way to reset after
    a demo. Member identities survive: the person keeps their other
    memberships, and their email stays registered.
    """
    program = _get_program_or_404(db, program_id)
    if program.is_default:
        raise HTTPException(
            400,
            "Cannot delete the default program. Make another program the default first.",
        )
    logo_url = program.logo_url
    db.delete(program)
    db.commit()
    if logo_url and storage is not None:
        storage.delete_url(logo_url)
