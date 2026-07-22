import os
import secrets

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

load_dotenv()

_api_token = os.getenv("API_TOKEN")
if not _api_token:
    raise RuntimeError(
        "API_TOKEN is not set. Add a secret bearer token to the environment or a .env file."
    )
API_TOKEN: str = _api_token

bearer_scheme = HTTPBearer(auto_error=True)


def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    if not secrets.compare_digest(credentials.credentials, API_TOKEN):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials
