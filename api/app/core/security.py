"""Bearer-token authentication.

A single shared static token, compared in constant time. Applied globally in
``app.main`` rather than per-router, so a new router can't accidentally ship
unauthenticated.
"""

import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

bearer_scheme = HTTPBearer(auto_error=True)


def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    if not secrets.compare_digest(credentials.credentials, settings.api_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials
