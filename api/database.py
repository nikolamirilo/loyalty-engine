import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

# Supabase / Postgres connection string, e.g.
#   postgresql://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Add your Supabase Postgres connection string "
        "to the environment or a .env file (see .env.example)."
    )


# Connection-pool tuning for a long-lived server (uvicorn):
#  - A pool of warm connections is reused across requests. Opening a fresh TLS
#    connection to the remote Supabase pooler costs hundreds of ms, so reusing
#    connections is the single biggest latency win for the console. (The old
#    NullPool opened + closed a connection on *every* request.)
#  - pool_size / max_overflow: keep a handful hot, allow a few extra under burst
#    (each page issues several parallel API calls).
#  - pool_pre_ping: cheap liveness check before handing out a pooled connection,
#    in case the pooler (Supavisor) closed an idle socket between requests.
#  - pool_recycle: proactively drop connections older than this so we never hand
#    out one the pooler is about to close.
#  - sslmode=require: Supabase requires TLS; only skip if the URL already sets it.
connect_args = {} if "sslmode=" in DATABASE_URL else {"sslmode": "require"}
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=1800,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
