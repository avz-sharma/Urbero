"""Bounded retries and cooldown for transient upstream GET failures."""

import asyncio
from collections.abc import Awaitable, Callable
from time import monotonic

import httpx


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
