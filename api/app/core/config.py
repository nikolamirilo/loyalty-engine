"""Application configuration.

The single place environment variables are read. Everything else imports
``settings`` rather than calling ``os.getenv``, so required config fails loudly at
import time in one spot instead of at the first request that happens to need it.
"""

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

# Called once here rather than in each module that needs a variable.
load_dotenv()


def _required(name: str, hint: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is not set. {hint}")
    return value


@dataclass(frozen=True)
class Settings:
    """Validated runtime configuration."""

    database_url: str
    api_token: str
    resend_api_key: str
    doi_from_email: str

    project_name: str = "Loyalty Engine"
    version: str = "1.0.0"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        database_url=_required(
            "DATABASE_URL",
            "Add your Supabase Postgres connection string to the environment "
            "or a .env file (see .env.example).",
        ),
        api_token=_required(
            "API_TOKEN",
            "Add a secret bearer token to the environment or a .env file.",
        ),
        resend_api_key=_required(
            "RESEND_API_KEY",
            "Add the Resend API key used to send DOI verification emails.",
        ),
        doi_from_email=_required(
            "DOI_FROM_EMAIL",
            "Add the verified Resend sender address for DOI verification emails.",
        ),
    )


settings = get_settings()
