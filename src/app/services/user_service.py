from __future__ import annotations

from typing import Protocol

from ..repositories.ports import UserRepository
from ..domain.user import User
from ..core.errors import ConflictError, NotFoundError


class UserService:
    def __init__(self, user_repo: UserRepository) -> None:
        self.user_repo = user_repo

    async def list_users(self, limit: int, offset: int) -> tuple[list[User], int]:
        return await self.user_repo.list(limit=limit, offset=offset)

    async def get_user(self, user_id: int) -> User:
        user = await self.user_repo.get(user_id)
        if not user:
            raise NotFoundError("user_not_found")
        return user

    async def create_user(self, email: str, full_name: str) -> User:
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise ConflictError("email_already_exists")
        return await self.user_repo.create(email=email, full_name=full_name)

    async def update_user(self, user_id: int, email: str, full_name: str) -> User:
        # Ensure unique email (cross-entity validation)
        existing = await self.user_repo.get_by_email(email)
        if existing and existing.id != user_id:
            raise ConflictError("email_already_exists")
        return await self.user_repo.update(user_id=user_id, email=email, full_name=full_name)

    async def delete_user(self, user_id: int) -> None:
        await self.user_repo.delete(user_id)

