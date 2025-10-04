from __future__ import annotations

from datetime import datetime
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ErrorOut(BaseModel):
    error: str
    message: str
    correlation_id: str


class UserIn(BaseModel):
    email: EmailStr = Field(examples=["user@example.com"])
    full_name: str = Field(min_length=1, max_length=200, examples=["Fulano de Tal"])


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    created_at: datetime


T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int

