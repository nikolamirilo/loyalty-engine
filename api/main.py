from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from auth import verify_token
from database import Base, engine
from routers import challenges, members, points, rewards, redemptions, tiers


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
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


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
