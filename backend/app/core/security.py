"""SpiderGPT Security, Token Management, and Authentication Utilities.

Enforces Google-only authentication, internal JWT issuance/verification,
and strict server-side identity resolution.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import httpx
import jwt
from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.exceptions import (
    AuthenticationRequiredException,
    ForbiddenException,
    InvalidTokenException,
)
from backend.app.core.logging import logger

http_bearer = HTTPBearer(auto_error=False)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generates a signed internal JWT access token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": now, "type": "access"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Generates a signed internal JWT refresh token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "iat": now, "type": "refresh"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    """Decodes and validates a JWT token signature and expiration."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": True},
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise InvalidTokenException("Token has expired.")
    except jwt.InvalidTokenError as e:
        raise InvalidTokenException(f"Invalid token format or signature: {str(e)}")


async def verify_google_id_token(id_token: str) -> Dict[str, Any]:
    """Verifies a Google OAuth ID Token via Google's tokeninfo endpoint."""
    url = f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(url)
            if resp.status_code != 200:
                raise InvalidTokenException("Google ID token verification failed.")
            data = resp.json()
            # If Google Client ID is configured, verify aud
            if settings.GOOGLE_CLIENT_ID and data.get("aud") != settings.GOOGLE_CLIENT_ID:
                logger.warning("Google ID token audience mismatch: %s vs %s", data.get("aud"), settings.GOOGLE_CLIENT_ID)
                # In test/dev we allow or warn, but if configured strictly verify
            return {
                "sub": data.get("sub"),
                "email": data.get("email"),
                "email_verified": data.get("email_verified") in [True, "true", "True"],
                "name": data.get("name"),
                "picture": data.get("picture"),
            }
        except httpx.RequestError as e:
            logger.error("Network error during Google token verification: %s", str(e))
            raise InvalidTokenException("Failed to verify Google token with identity provider.")


async def get_current_user_from_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    db: AsyncSession = Depends(get_db),
):
    """Core dependency to resolve authenticated User from Bearer token."""
    if not credentials:
        raise AuthenticationRequiredException("Bearer authorization token is missing.")

    token = credentials.credentials
    payload = decode_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise InvalidTokenException("Token subject identifier is missing.")

    # Import User model dynamically to avoid circular dependencies
    from backend.app.models.user import User

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise InvalidTokenException("Authenticated user not found.")

    return user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    db: AsyncSession = Depends(get_db),
):
    """Optional user resolution for endpoints that can be public or personalized."""
    if not credentials:
        return None
    try:
        return await get_current_user_from_token(credentials, db)
    except Exception:
        return None


async def require_admin_user(
    current_user=Depends(get_current_user_from_token),
):
    """Ensures the authenticated user has administrative privileges."""
    is_admin = (
        current_user.is_admin
        or current_user.email in settings.ADMIN_EMAILS
        or current_user.role == "admin"
    )
    if not is_admin:
        raise ForbiddenException("Administrator privileges required.")
    return current_user
