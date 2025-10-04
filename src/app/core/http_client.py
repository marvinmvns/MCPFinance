from __future__ import annotations

from typing import Any, Callable

import httpx
from pybreaker import CircuitBreaker
from tenacity import RetryCallState, retry, stop_after_attempt, wait_exponential


def default_client(timeout: float = 5.0) -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=httpx.Timeout(timeout))


_breaker = CircuitBreaker(fail_max=5, reset_timeout=30)


def _retry_after(result: RetryCallState) -> float:  # pragma: no cover - behavior validated indirectly
    return 0.0


def with_retry(func: Callable[..., Any]) -> Callable[..., Any]:  # pragma: no cover - utility
    return retry(wait=wait_exponential(multiplier=0.2, min=0.2, max=2), stop=stop_after_attempt(3))(func)


def with_circuit_breaker(func: Callable[..., Any]) -> Callable[..., Any]:  # pragma: no cover - utility
    return _breaker.call(func)

