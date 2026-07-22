import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool

load_dotenv()

# Supabase / Postgres connection string, e.g.
#   postgresql://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Add your Supabase Postgres connection string "
        "to the environment or a .env file (see .env.example)."
    )


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
# NOTE: point DATABASE_URL at the Supabase *transaction* pooler (port 6543),
# not the session pooler (port 5432). Transaction mode is the mode designed for
# many short-lived serverless connections; see api/README.md.
connect_args = {} if "sslmode=" in DATABASE_URL else {"sslmode": "require"}
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,
    pool_pre_ping=True,
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
