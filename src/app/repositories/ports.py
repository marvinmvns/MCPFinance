from __future__ import annotations

from typing import Protocol

from ..domain.user import User


class UserRepository(Protocol):
    async def get(self, user_id: int) -> User | None:  # pragma: no cover - protocol
        ...

    async def get_by_email(self, email: str) -> User | None:  # pragma: no cover
        ...

    async def list(self, limit: int, offset: int) -> tuple[list[User], int]:  # pragma: no cover
        ...

    async def create(self, email: str, full_name: str) -> User:  # pragma: no cover
        ...

    async def update(self, user_id: int, email: str, full_name: str) -> User:  # pragma: no cover
        ...

    async def delete(self, user_id: int) -> None:  # pragma: no cover
        ...


class TokenRevocationStore(Protocol):
    async def is_revoked(self, jti: str) -> bool:  # pragma: no cover - protocol
        ...
