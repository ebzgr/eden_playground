"""Basic auth for admin routes (optional via ADMIN_AUTH_ENABLED)."""

import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from playground.config import get_settings

security = HTTPBasic(auto_error=False)


def verify_admin(
    credentials: HTTPBasicCredentials | None = Depends(security),
) -> str:
    settings = get_settings()
    if not settings.admin_auth_enabled:
        return "dev"

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Basic"},
        )
    user_ok = secrets.compare_digest(
        credentials.username.encode(), settings.admin_username.encode()
    )
    pass_ok = secrets.compare_digest(
        credentials.password.encode(), settings.admin_password.encode()
    )
    if not (user_ok and pass_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
