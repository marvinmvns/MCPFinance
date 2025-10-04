from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus


class AppError(Exception):
    code: str
    message: str
    http_status: int

    def __init__(self, code: str, message: str, http_status: int) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = http_status


class NotFoundError(AppError):
    def __init__(self, message: str = "Not found") -> None:
        super().__init__("not_found", message, HTTPStatus.NOT_FOUND)


class ConflictError(AppError):
    def __init__(self, message: str = "Conflict") -> None:
        super().__init__("conflict", message, HTTPStatus.CONFLICT)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Unauthorized") -> None:
        super().__init__("unauthorized", message, HTTPStatus.UNAUTHORIZED)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden") -> None:
        super().__init__("forbidden", message, HTTPStatus.FORBIDDEN)


@dataclass(slots=True, frozen=True)
class ErrorPayload:
    error: str
    message: str
    correlation_id: str

