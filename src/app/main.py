from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any, Callable, Coroutine

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from .api.routes import health, users, openfinance
from .core.config import Settings, get_settings
from .core.errors import AppError, ErrorPayload
from .core.logging import configure_logging
from .core.observability import init_tracing, instrument_app


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Coroutine[Any, Any, Response]]) -> Response:  # type: ignore[override]
        cid = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        request.state.correlation_id = cid
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = cid
        return response


class IdempotencyStore:
    def __init__(self) -> None:
        self._store: dict[str, tuple[float, bytes, int, dict[str, str]]] = {}
        self._ttl = 600.0
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Response | None:
        async with self._lock:
            item = self._store.get(key)
            if not item:
                return None
            ts, body, status, headers = item
            if time.time() - ts > self._ttl:
                self._store.pop(key, None)
                return None
            return Response(content=body, status_code=status, headers=headers)

    async def set(self, key: str, response: Response) -> None:
        async with self._lock:
            self._store[key] = (time.time(), response.body, response.status_code, dict(response.headers))


_IDEMPOTENCY = IdempotencyStore()


class IdempotencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Coroutine[Any, Any, Response]]) -> Response:  # type: ignore[override]
        if request.method.upper() == "POST":
            key = request.headers.get("Idempotency-Key")
            if key:
                cached = await _IDEMPOTENCY.get(key)
                if cached:
                    return cached
                response = await call_next(request)
                await _IDEMPOTENCY.set(key, response)
                return response
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Coroutine[Any, Any, Response]]) -> Response:  # type: ignore[override]
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-XSS-Protection", "1; mode=block")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        return response


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging()
    init_tracing(settings)
    app = FastAPI(title=settings.OPENAPI_TITLE, version=settings.OPENAPI_VERSION, openapi_url="/openapi.json")
    instrument_app(app)

    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(IdempotencyMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def _app_error_handler(request: Request, exc: AppError) -> JSONResponse:  # type: ignore[no-redef]
        cid = str(getattr(request.state, "correlation_id", ""))
        payload = ErrorPayload(error=exc.code, message=exc.message, correlation_id=cid)
        return JSONResponse(status_code=exc.http_status, content=payload.__dict__)

    app.include_router(health.router, prefix="/v1")
    app.include_router(users.router, prefix="/v1")
    app.include_router(openfinance.router, prefix="/v1")
    return app


app = create_app()
