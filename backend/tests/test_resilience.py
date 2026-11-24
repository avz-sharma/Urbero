import httpx
import pytest

from backend.app.providers.resilience import ResilientGet, UpstreamUnavailable


@pytest.mark.asyncio
async def test_transient_outage_opens_cooldown_without_extra_provider_calls(monkeypatch):
    pauses = []
    attempts = 0

    async def sleep(seconds):
        pauses.append(seconds)

    async def failing():
        nonlocal attempts
        attempts += 1
        raise httpx.ConnectError("offline")

    monkeypatch.setattr("backend.app.providers.resilience.asyncio.sleep", sleep)
    resilience = ResilientGet()
    for _ in range(3):
        with pytest.raises(httpx.ConnectError):
            await resilience.request(failing)
    with pytest.raises(UpstreamUnavailable):
        await resilience.request(failing)
    assert attempts == 9
    assert pauses == [0.2, 0.4] * 3
