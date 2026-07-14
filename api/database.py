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


# Serverless (Vercel) tuning:
#  - NullPool: no persistent connections. Each request opens one and closes it
#    so we never leak connections between short-lived function invocations.
#  - pool_pre_ping: sanity-check a connection before using it in case the
#    pooler (Supavisor) closed an idle socket between requests.
#  - sslmode=require: Supabase requires TLS; only skip if the URL already sets it.
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
