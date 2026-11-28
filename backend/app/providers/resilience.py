"""Bounded retries and coalescing for upstream requests."""

import asyncio
from collections.abc import Awaitable, Callable, Coroutine
from time import monotonic
from typing import Any, TypeVar

import httpx

K = TypeVar("K")
T = TypeVar("T")


async def coalesce(
    tasks: dict[K, asyncio.Task[T]], key: K, fetch: Callable[[], Coroutine[Any, Any, T]]
) -> T:
    """Share an in-flight fetch without tying it to any individual caller."""
    task = tasks.get(key)
    if task is None:
        task = asyncio.create_task(fetch())
        tasks[key] = task

        def clear_task(completed: asyncio.Task[T]) -> None:
            tasks.pop(key, None)
            if not completed.cancelled():
                completed.exception()  # Observe failures even when all callers cancelled.

        task.add_done_callback(clear_task)
    return await asyncio.shield(task)


class UpstreamUnavailable(RuntimeError):
    """A provider is temporarily in cooldown."""


class ResilientGet:
    def __init__(self) -> None:
        self._failures = 0
        self._open_until = 0.0

    async def request(self, send: Callable[[], Awaitable[httpx.Response]]) -> httpx.Response:
        if monotonic() < self._open_until:
            raise UpstreamUnavailable("Upstream request cooldown is active")
        for attempt in range(3):
            try:
                response = await send()
                if response.status_code == 429 or response.status_code >= 500:
                    response.raise_for_status()
                self._failures = 0
                return response
            except (httpx.TransportError, httpx.HTTPStatusError):
                if attempt == 2:
                    self._failures += 1
                    if self._failures >= 3:
                        self._open_until = monotonic() + 30
                    raise
                await asyncio.sleep(0.2 * 2**attempt)
        raise AssertionError("Retry loop must return or raise")
