from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict

from ..domain.user import User
from .ports import UserRepository


class InMemoryUserRepository(UserRepository):
    def __init__(self) -> None:
        self._data: Dict[int, User] = {}
        self._by_email: Dict[str, int] = {}
        self._seq = 0

    async def get(self, user_id: int) -> User | None:
        return self._data.get(user_id)

    async def get_by_email(self, email: str) -> User | None:
        uid = self._by_email.get(email)
        return self._data.get(uid) if uid is not None else None

    async def list(self, limit: int, offset: int) -> tuple[list[User], int]:
        items = list(sorted(self._data.values(), key=lambda u: u.id))
        total = len(items)
        return items[offset : offset + limit], total

    async def create(self, email: str, full_name: str) -> User:
        if email in self._by_email:
            raise ValueError("email exists")
        self._seq += 1
        user = User(
            id=self._seq,
            email=email,
            full_name=full_name,
            created_at=datetime.now(timezone.utc),
        )
        self._data[user.id] = user
        self._by_email[email] = user.id
        return user

    async def update(self, user_id: int, email: str, full_name: str) -> User:
        if user_id not in self._data:
            raise KeyError("not found")
        # naive unique constraint
        existing = self._by_email.get(email)
        if existing is not None and existing != user_id:
            raise ValueError("email exists")
        user = self._data[user_id]
        new_user = User(id=user.id, email=email, full_name=full_name, created_at=user.created_at)
        self._data[user_id] = new_user
        self._by_email[email] = user_id
        return new_user

    async def delete(self, user_id: int) -> None:
        user = self._data.pop(user_id, None)
        if user is None:
            raise KeyError("not found")
        self._by_email.pop(user.email, None)

