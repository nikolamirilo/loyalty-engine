"""SQLAlchemy engine, session factory, declarative base, and the request-scoped
session dependency.
"""

import logging
from collections.abc import Generator
from urllib.parse import urlsplit, urlunsplit

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings

logger = logging.getLogger("uvicorn.error")

# Supabase exposes two poolers on the same host. Session mode (5432) hands each
# client a dedicated Postgres backend out of a fixed, small budget; transaction
# mode (6543) hands out a connection per statement batch and is the mode built
# for many short-lived serverless invocations. A session-mode URL here is always
# a misconfiguration, and production showed exactly what it costs:
#     FATAL: (EMAXCONNSESSION) max clients reached in session mode
#            - max clients are limited to pool_size: 15
# So redirect to the transaction pooler instead of serving 500s until somebody
# reads the logs - and say loudly that the environment still needs fixing.
SESSION_POOLER_PORT = 5432
TRANSACTION_POOLER_PORT = 6543
SUPABASE_POOLER_SUFFIX = ".pooler.supabase.com"

# A saturated or unreachable pooler should fail fast; without this libpq waits
# far longer than the serverless function is allowed to live.
CONNECT_TIMEOUT_SECONDS = 10


def _prefer_transaction_pooler(url: str) -> str:
    """Point a Supabase *session* pooler URL at the transaction pooler."""
    parts = urlsplit(url)
    try:
        port = parts.port
    except ValueError:  # unparseable port - leave the URL exactly as given
        return url

    host = (parts.hostname or "").lower()
    if port != SESSION_POOLER_PORT or not host.endswith(SUPABASE_POOLER_SUFFIX):
        return url

    logger.warning(
        "DATABASE_URL points at the Supabase session pooler (port %d), which "
        "allows only a handful of clients and fails with EMAXCONNSESSION under "
        "serverless load. Connecting via the transaction pooler (port %d) "
        "instead - update DATABASE_URL to the transaction-mode connection "
        "string (see api/README.md).",
        SESSION_POOLER_PORT,
        TRANSACTION_POOLER_PORT,
    )
    credentials, _, _ = parts.netloc.rpartition("@")
    netloc = f"{host}:{TRANSACTION_POOLER_PORT}"
    if credentials:
        netloc = f"{credentials}@{netloc}"
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


DATABASE_URL = _prefer_transaction_pooler(settings.database_url)

# Serverless (Vercel) connection handling:
#  - NullPool: do NOT keep a client-side pool of warm connections. Every
#    function instance would otherwise hold its own pool open, and with many
#    concurrent short-lived invocations those connections pile up against the
#    Supabase pooler until it rejects new ones with:
#        FATAL: (EMAXCONNSESSION) max clients reached in session mode
#    (a persistent pool_size/max_overflow pool is what caused that outage).
#    With NullPool each request opens exactly one connection and closes it, so
#    connections are never leaked between invocations.
#  - pool_pre_ping: sanity-check a connection before using it in case the
#    pooler (Supavisor) closed an idle socket between requests.
#  - sslmode=require: Supabase requires TLS; only skip if the URL already sets it.
#
# NOTE: DATABASE_URL should already point at the Supabase *transaction* pooler
# (port 6543); _prefer_transaction_pooler above is a safety net, not a licence
# to configure the session pooler. See api/README.md.
connect_args: dict[str, object] = {"connect_timeout": CONNECT_TIMEOUT_SECONDS}
if "sslmode=" not in DATABASE_URL:
    connect_args["sslmode"] = "require"

engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,
    pool_pre_ping=True,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a session that is always closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
