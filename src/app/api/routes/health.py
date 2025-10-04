from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from starlette.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, generate_latest
from sqlalchemy import text

from ...db.session import engine


router = APIRouter(tags=["health"])

_REGISTRY = CollectorRegistry()
REQUEST_COUNTER = Counter("app_requests_total", "Total requests", registry=_REGISTRY)


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def ready() -> dict[str, str]:
    # simple DB check
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return {"status": "ready"}


@router.get("/metrics")
async def metrics() -> Response:
    data = generate_latest(_REGISTRY)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
