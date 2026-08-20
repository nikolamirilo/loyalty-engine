import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

from app.core.config import settings
from app.core.database import Base, engine
from app.core.security import verify_token
from app.routers import (
    challenges,
    doi,
    member_attributes,
    members,
    points,
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


app = FastAPI(title=settings.project_name, version=settings.version, lifespan=lifespan)

# All API routers require a valid bearer token.
protected = [Depends(verify_token)]

app.include_router(members.router, dependencies=protected)
app.include_router(member_attributes.router, dependencies=protected)
app.include_router(points.router, dependencies=protected)
app.include_router(rewards.router, dependencies=protected)
app.include_router(redemptions.router, dependencies=protected)
app.include_router(challenges.router, dependencies=protected)
app.include_router(tiers.router, dependencies=protected)
app.include_router(segments.router, dependencies=protected)
app.include_router(doi.router, dependencies=protected)


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


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
