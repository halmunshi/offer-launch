import time
from typing import Any

import httpx
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User

security = HTTPBearer(auto_error=True)
_JWKS_CACHE_SECONDS = 300
_jwks_cache: dict[str, Any] | None = None
_jwks_cached_at: float = 0.0


async def _get_jwks(force_refresh: bool = False) -> dict[str, Any]:
    global _jwks_cache, _jwks_cached_at

    if not settings.CLERK_JWKS_URL:
        raise HTTPException(status_code=500, detail="CLERK_JWKS_URL is not configured")

    now = time.time()
    if not force_refresh and _jwks_cache and (now - _jwks_cached_at) < _JWKS_CACHE_SECONDS:
        return _jwks_cache

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(settings.CLERK_JWKS_URL)
        response.raise_for_status()
        jwks = response.json()

    if not isinstance(jwks, dict) or not isinstance(jwks.get("keys"), list):
        raise HTTPException(status_code=500, detail="Invalid Clerk JWKS response")

    _jwks_cache = jwks
    _jwks_cached_at = now
    return jwks


def _find_signing_key(jwks: dict[str, Any], kid: str | None) -> dict[str, Any] | None:
    if not kid:
        return None

    keys = jwks.get("keys") or []
    for key in keys:
        if key.get("kid") == kid:
            return key

    return None


async def _decode_clerk_token(token: str) -> dict[str, Any]:
    try:
        headers = jwt.get_unverified_header(token)
    except JWTError as error:
        raise HTTPException(status_code=401, detail="Invalid authentication token") from error

    kid = headers.get("kid")
    algorithm = headers.get("alg", "RS256")

    jwks = await _get_jwks()
    key = _find_signing_key(jwks, kid)

    if key is None:
        jwks = await _get_jwks(force_refresh=True)
        key = _find_signing_key(jwks, kid)

    if key is None:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    try:
        return jwt.decode(
            token,
            key,
            algorithms=[algorithm],
            options={"verify_aud": False},
        )
    except JWTError as error:
        raise HTTPException(status_code=401, detail="Invalid authentication token") from error


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = await _decode_clerk_token(credentials.credentials)
    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    result = await db.execute(select(User).where(User.clerk_id == clerk_id))
    user = result.scalar_one_or_none()
    if user is None:
        email = payload.get("email") or payload.get("email_address")
        if not email:
            raise HTTPException(status_code=401, detail="User not found")

        user = User(
            clerk_id=clerk_id,
            email=email,
            full_name=payload.get("name") or payload.get("full_name"),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    request.state.user_id = str(user.id)
    return user
