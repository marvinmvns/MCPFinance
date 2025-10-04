from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncGenerator, Generator
from typing import Any

# Set test database before any imports
os.environ["DB_DSN"] = "sqlite+aiosqlite:///:memory:"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.main import create_app
from app.db import session as db_session
from app.db.base import Base
from app.repositories.user_repo_sql import UserModel  # noqa: F401 - ensure models are registered


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def app(_setup_db: None) -> Any:
    return create_app()


@pytest.fixture(scope="session")
def client(app: Any) -> TestClient:
    return TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def _setup_db(event_loop: asyncio.AbstractEventLoop) -> Generator[None, None, None]:
    # Create tables in the test database
    async def create_all() -> None:
        async with db_session.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    event_loop.run_until_complete(create_all())
    yield
