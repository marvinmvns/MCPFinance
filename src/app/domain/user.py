from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar

from pydantic import EmailStr, TypeAdapter


@dataclass(slots=True, frozen=True)
class User:
    id: int
    email: str
    full_name: str
    created_at: datetime

    EMAIL_MAX: ClassVar[int] = 320
    NAME_MAX: ClassVar[int] = 200

    def __post_init__(self) -> None:  # type: ignore[override]
        # Validate email via Pydantic type to reuse robust validation
        TypeAdapter(EmailStr).validate_python(self.email)
        if len(self.email) > self.EMAIL_MAX:
            raise ValueError("email too long")
        if not self.full_name or len(self.full_name) > self.NAME_MAX:
            raise ValueError("invalid full_name")

