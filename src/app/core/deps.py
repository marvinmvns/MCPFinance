from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends

from .config import Settings, get_settings
from ..repositories.user_repo_sql import SQLUserRepository
from ..repositories.user_repo_memory import InMemoryUserRepository
from ..services.user_service import UserService
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.session import async_session


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:  # type: ignore[call-arg]
        yield session


async def get_user_repo(
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    # For tests or local env you may swap to InMemory repo
    del settings  # not used now, kept for DI extensibility
    return SQLUserRepository(session)


def get_user_service(repo=Depends(get_user_repo)) -> UserService:
    return UserService(user_repo=repo)
