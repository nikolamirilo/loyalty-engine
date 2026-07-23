import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from auth import verify_token
from database import Base, engine
from routers import challenges, members, points, rewards, redemptions, segments, tiers

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup. Don't let a transient DB error here crash the
    # whole (serverless) app on cold start — the tables are usually already
    # present, and letting the app boot means /health and later requests can
    # still succeed once the database is reachable again.
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:  # noqa: BLE001 - startup must be resilient
        logger.exception("Skipping create_all: database was unreachable at startup")
    yield


app = FastAPI(title="Loyalty Engine", version="1.0.0", lifespan=lifespan)

# All API routers require a valid bearer token.
protected = [Depends(verify_token)]

app.include_router(members.router, dependencies=protected)
app.include_router(points.router, dependencies=protected)
app.include_router(rewards.router, dependencies=protected)
app.include_router(redemptions.router, dependencies=protected)
app.include_router(challenges.router, dependencies=protected)
app.include_router(tiers.router, dependencies=protected)
app.include_router(segments.router, dependencies=protected)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
