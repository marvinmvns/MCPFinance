from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Security
from fastapi.security import OAuth2AuthorizationCodeBearer, SecurityScopes
from jwt import InvalidTokenError

from .config import Settings, get_settings
from .errors import ForbiddenError, UnauthorizedError
from ..repositories.ports import TokenRevocationStore


@dataclass(slots=True, frozen=True)
class TokenData:
    sub: str
    scopes: frozenset[str]
    jti: str | None


def create_jwt(sub: str, scopes: list[str], settings: Settings) -> str:
    now = int(time.time())
    payload = {
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "iat": now,
        "exp": now + settings.JWT_EXPIRE_SECONDS,
        "nbf": now - 5,  # small clock skew
        "jti": f"jti-{now}-{sub}",
        "sub": sub,
        "scope": " ".join(scopes),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="/auth/authorize", tokenUrl="/auth/token", auto_error=False
)


async def parse_token(token: str, settings: Settings) -> TokenData:
    try:
        decoded = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            options={"require": ["exp", "iat", "nbf", "iss", "aud"]},
            issuer=settings.JWT_ISSUER,
        )
    except InvalidTokenError as exc:  # pragma: no cover - exercised via API
        raise UnauthorizedError("invalid_token") from exc
    scopes = frozenset(str(decoded.get("scope", "")).split()) if decoded.get("scope") else frozenset()
    return TokenData(sub=str(decoded.get("sub", "")), scopes=scopes, jti=decoded.get("jti"))


async def require_scopes(
    security_scopes: SecurityScopes,
    token: Annotated[str | None, Depends(oauth2_scheme)],
    settings: Annotated[Settings, Depends(get_settings)],
    revocation_store: Annotated[TokenRevocationStore | None, Depends(lambda: None)] = None,
) -> TokenData:
    if not token:
        raise UnauthorizedError("missing_token")
    data = await parse_token(token, settings)
    if data.jti and revocation_store is not None:
        if await revocation_store.is_revoked(data.jti):
            raise UnauthorizedError("token_revoked")
    required = set(security_scopes.scopes)
    if not required.issubset(data.scopes):
        raise ForbiddenError("insufficient_scope")
    return data
