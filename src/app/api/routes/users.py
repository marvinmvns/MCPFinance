from __future__ import annotations

import hashlib
import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Security
from starlette.responses import JSONResponse

from ...api.schemas import Page, UserIn, UserOut
from ...core.config import get_settings
from ...core.security import TokenData, require_scopes
from ...core.errors import AppError
from ...services.user_service import UserService
from ...core.deps import get_user_service


router = APIRouter(prefix="/users", tags=["users"])


def _etag_for(payload: object) -> str:
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(raw).hexdigest()


@router.get("")
async def list_users(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: UserService = Depends(get_user_service),
) -> JSONResponse:
    items, total = await service.list_users(limit=limit, offset=offset)
    payload: Page[UserOut] = Page(items=[UserOut.model_validate(i) for i in items], total=total)
    body = payload.model_dump()
    resp = JSONResponse(content=body)
    resp.headers["Cache-Control"] = "public, max-age=60"
    resp.headers["ETag"] = _etag_for(body)
    return resp


@router.get("/{user_id}")
async def get_user(user_id: int, service: UserService = Depends(get_user_service)) -> UserOut:
    user = await service.get_user(user_id)
    return UserOut.model_validate(user)


@router.post("", dependencies=[Security(require_scopes, scopes=["users:write"])])
async def create_user(
    body: UserIn,
    service: UserService = Depends(get_user_service),
) -> UserOut:
    try:
        user = await service.create_user(email=body.email, full_name=body.full_name)
        return UserOut.model_validate(user)
    except AppError as exc:  # covered by general error handler; kept for mypy
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.put("/{user_id}", dependencies=[Security(require_scopes, scopes=["users:write"])])
async def update_user(user_id: int, body: UserIn, service: UserService = Depends(get_user_service)) -> UserOut:
    user = await service.update_user(user_id=user_id, email=body.email, full_name=body.full_name)
    return UserOut.model_validate(user)


@router.delete("/{user_id}", status_code=204, response_model=None, dependencies=[Security(require_scopes, scopes=["users:write"])])
async def delete_user(user_id: int, service: UserService = Depends(get_user_service)) -> None:
    await service.delete_user(user_id)

