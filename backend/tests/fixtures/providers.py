"""Network-free replay helpers. Recorded CAMS values, timestamps rebased for freshness tests."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx


def model_payload() -> dict:
    data = json.loads(Path(__file__).with_name("openmeteo_delhi.json").read_text())
    start = datetime.now(UTC).replace(minute=0, second=0, microsecond=0) - timedelta(hours=72)
    data["hourly"]["time"] = [
        (start + timedelta(hours=i)).isoformat() for i in range(len(data["hourly"]["time"]))
    ]
    return data


def model_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=model_payload()))
    )
