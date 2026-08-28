"""Reusable async retry helper for temporary collection failures."""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TypeVar

from app.collectors.errors import CollectionError

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    max_attempts: int = 3
    delay_seconds: float = 1.0

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1.")
        if self.delay_seconds < 0:
            raise ValueError("delay_seconds cannot be negative.")


async def retry_async(
    operation: Callable[[], Awaitable[T]],
    *,
    policy: RetryPolicy,
    operation_name: str = "operation",
) -> T:
    last_error: Exception | None = None

    for attempt in range(1, policy.max_attempts + 1):
        try:
            return await operation()
        except CollectionError as exc:
            last_error = exc
            if not exc.retryable or attempt >= policy.max_attempts:
                raise
            logger.info(
                "Retrying %s after %s (attempt %s/%s)",
                operation_name,
                exc.error_type.value,
                attempt,
                policy.max_attempts,
            )
            await asyncio.sleep(policy.delay_seconds)
        except Exception as exc:
            last_error = exc
            raise

    assert last_error is not None
    raise last_error
