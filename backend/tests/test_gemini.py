"""Exercise Gemini's real request format without contacting the external API."""

import json

import httpx
import pytest

from backend.app.planner.gemini import GeminiClient
from backend.app.planner.schemas import TravelChoice


@pytest.mark.asyncio
@pytest.mark.parametrize("second", ['{"mode":"bus_public","priority":"balance"}', "{}"])
async def test_gemini_retries_invalid_json_then_returns_typed_result_or_fallback(
    monkeypatch: pytest.MonkeyPatch, second: str
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test")
    monkeypatch.setenv("GEMINI_MODEL", "test-model")
    candidates = iter(("invalid json", second))
    requests = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "candidates": [{"content": {"parts": [{"text": next(candidates)}]}}],
            },
        )

    transport_client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: transport_client)
    result = await GeminiClient().generate(
        "<untrusted_input>Travel</untrusted_input>", TravelChoice
    )
    assert len(requests) == 2
    assert requests[0].headers["x-goog-api-key"] == "test"
    config = json.loads(requests[0].content)["generationConfig"]
    assert config["responseJsonSchema"] == TravelChoice.model_json_schema()
    if second == "{}":
        assert result is None
    else:
        assert result == TravelChoice(mode="bus_public", priority="balance")
