from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, Integer, String, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base
from ..domain.user import User
from ..core.errors import ConflictError, NotFoundError


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


def _to_domain(m: UserModel) -> User:
    return User(id=m.id, email=m.email, full_name=m.full_name, created_at=m.created_at)


class SQLUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, user_id: int) -> User | None:
        row = await self.session.get(UserModel, user_id)
        return _to_domain(row) if row else None

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(UserModel).where(UserModel.email == email)
        res = await self.session.execute(stmt)
        row = res.scalar_one_or_none()
        return _to_domain(row) if row else None

    async def list(self, limit: int, offset: int) -> tuple[list[User], int]:
        total_stmt = select(func.count()).select_from(UserModel)
        total = (await self.session.execute(total_stmt)).scalar_one()
        stmt = select(UserModel).order_by(UserModel.id).limit(limit).offset(offset)
        res = await self.session.execute(stmt)
        items = [_to_domain(r) for r in res.scalars().all()]
        return items, int(total)

    async def create(self, email: str, full_name: str) -> User:
        model = UserModel(email=email, full_name=full_name)
        self.session.add(model)
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("email_already_exists") from exc
        await self.session.refresh(model)
        return _to_domain(model)

    async def update(self, user_id: int, email: str, full_name: str) -> User:
        model = await self.session.get(UserModel, user_id)
        if not model:
            raise NotFoundError("user_not_found")
        model.email = email
        model.full_name = full_name
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("email_already_exists") from exc
        await self.session.refresh(model)
        return _to_domain(model)

    async def delete(self, user_id: int) -> None:
        model = await self.session.get(UserModel, user_id)
        if not model:
            raise NotFoundError("user_not_found")
        await self.session.delete(model)
        await self.session.commit()

