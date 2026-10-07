import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, OperationalError

from app.core.config import settings
from app.core.database import Base, engine
from app.core.errors import DomainError
from app.core.security import verify_token
from app.routers import (
    auth,
    challenges,
    doi,
    event_types,
    events,
    member_attributes,
    members,
    points,
    prize_claims,
    products,
    programs,
    purchases,
    redemptions,
    rewards,
    segments,
    tiers,
)

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup. Don't let a transient DB error here crash the
    # whole (serverless) app on cold start - the tables are usually already
    # present, and letting the app boot means /health and later requests can
    # still succeed once the database is reachable again.
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:  # noqa: BLE001 - startup must be resilient
        logger.exception("Skipping create_all: database was unreachable at startup")
    yield


# Rendered as Markdown at the top of the Swagger UI (/docs) and ReDoc (/redoc).
API_DESCRIPTION = """
## Authentication

Every endpoint except `/health` needs the service token:
`Authorization: Bearer <token>`. Press **Authorize** above to set it once for
every request on this page.

## Choosing a program: `X-Program-Id`

One API serves several loyalty programs. Each has its own rewards, tiers,
challenges, segments and products, and each member has their own points and
tier in each program. The `X-Program-Id` header says **which program a request
works on**. It takes a program's id (UUID) or its slug, e.g. `retail-demo`.
`GET /programs` lists them.

| Endpoints | `X-Program-Id` |
|---|---|
| Program data: members, points, rewards, redemptions, tiers, challenges, segments, products, purchases, events | Picks the program. If left out, the **default program** is used. |
| `/programs` | Not used. This is how you find the programs. |
| `/doi/*`, `/auth/*` | Not used. These are about the person, not a program. |
| `/prizes/claim/*` | Not used. The claim token names the prize, and the prize's program comes from it. |

**Every member belongs to every program.** Their name, email and email
verification are shared across all programs. Points, tier, rewards and
challenge progress are separate per program. So:

- **Email verification (DOI)** counts in every program. The member is found by
  `email`, or by a `memberId` from any program.
- **Sign in** always lands in the default program. The member switches program
  from there.
- A member has a different `memberId` in each program. On program endpoints,
  use the `memberId` that belongs to the program in `X-Program-Id`.
  `GET /members/{memberId}/programs` lists them all.
"""

app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    description=API_DESCRIPTION,
    lifespan=lifespan,
)

# All API routers require a valid bearer token.
protected = [Depends(verify_token)]

# Not program-scoped: this is how a caller finds out which programs exist.
app.include_router(programs.router, dependencies=protected)

app.include_router(members.router, dependencies=protected)
app.include_router(member_attributes.router, dependencies=protected)
app.include_router(points.router, dependencies=protected)
app.include_router(rewards.router, dependencies=protected)
app.include_router(redemptions.router, dependencies=protected)
app.include_router(prize_claims.router, dependencies=protected)
app.include_router(products.router, dependencies=protected)
app.include_router(purchases.router, dependencies=protected)
app.include_router(challenges.router, dependencies=protected)
app.include_router(tiers.router, dependencies=protected)
app.include_router(segments.router, dependencies=protected)
app.include_router(event_types.router, dependencies=protected)
app.include_router(events.router, dependencies=protected)
app.include_router(doi.router, dependencies=protected)
app.include_router(auth.router, dependencies=protected)


@app.exception_handler(DomainError)
async def domain_error(request: Request, exc: DomainError) -> JSONResponse:
    """Answer a service's error with its status and FastAPI's usual body.

    Services raise ``app.core.errors`` rather than ``HTTPException`` so they
    stay free of HTTP; this is the one place those errors become responses.
    The body matches ``HTTPException``'s, so callers can't tell them apart.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )


@app.exception_handler(OperationalError)
async def database_unavailable(request: Request, exc: OperationalError) -> JSONResponse:
    """Answer with a clean 503 when the database can't be reached.

    A saturated Supabase pooler or a paused project is not the caller's fault
    and is not a bug in the handler that happened to run. Without this the
    driver error escapes as an unhandled ASGI exception: no JSON body, a raw
    traceback in the logs, and nothing the client can act on.
    """
    logger.exception(
        "Database unavailable handling %s %s", request.method, request.url.path
    )
    return JSONResponse(
        status_code=503,
        content={"detail": "Database is temporarily unavailable. Please try again shortly."},
    )


@app.exception_handler(IntegrityError)
async def constraint_violation(request: Request, exc: IntegrityError) -> JSONResponse:
    """Answer with a clean 409 when a write violates a DB constraint (e.g. a
    unique index) that a route handler didn't check for up front.

    Without this the driver error escapes as an unhandled ASGI exception: no
    JSON body, a raw traceback in the logs, and nothing the client can act on.
    """
    logger.exception(
        "Constraint violation handling %s %s", request.method, request.url.path
    )
    return JSONResponse(
        status_code=409,
        content={"detail": "The request conflicts with existing data."},
    )


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
