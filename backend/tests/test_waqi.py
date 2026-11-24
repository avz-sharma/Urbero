"""WAQI inversion boundaries and station integrity, without live network access."""

from datetime import UTC, datetime

import httpx
import pytest

from backend.app.providers.waqi import WAQIProvider, invert_iaqi


@pytest.mark.parametrize(
    "parameter,index,expected",
    [
        ("PM2.5", 0, 0),
        ("PM2.5", 50, 12),
        ("PM2.5", 51, 12.1),
        ("PM2.5", 100, 35.4),
        ("PM2.5", 150, 55.4),
        ("PM2.5", 500, 500.4),
        ("PM10", 50, 54),
        ("PM10", 51, 55),
        ("PM10", 100, 154),
    ],
)
def test_inverse_golden(parameter: str, index: float, expected: float) -> None:
    assert invert_iaqi(parameter, index) == pytest.approx(expected)


@pytest.mark.parametrize("index", [-1, 501, float("nan"), float("inf")])
def test_inverse_rejects_invalid(index: float) -> None:
    with pytest.raises(ValueError):
        invert_iaqi("PM2.5", index)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "agency",
    [
        "Central Pollution Control Board",
        "Delhi Pollution Control Committee",
        "Maharashtra Pollution Control Board",
        "West Bengal Pollution Control Board",
    ],
)
async def test_station_metadata_and_inversion(agency: str) -> None:
    now = datetime.now(UTC)
    payload = {
        "status": "ok",
        "data": {
            "city": {"name": "Anand Vihar, Delhi, India", "geo": [28.6469, 77.316]},
            "attributions": [{"name": agency}],
            "time": {"iso": now.isoformat()},
            "iaqi": {"pm25": {"v": 150}, "pm10": {"v": 100}},
        },
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        assert "/feed/geo:28.65;77.32/" in request.url.path
        return httpx.Response(200, json=payload)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        readings = await WAQIProvider(token="test", client=client).get_latest_readings(28.65, 77.32)
    assert readings[0].value == 55.4
    assert 0 < readings[0].distance_km < 1
    assert readings[0].observed_at == now
    assert readings[0].status == "live"
    assert "inverse" in readings[0].conversion_note.lower()


@pytest.mark.asyncio
@pytest.mark.parametrize("change", ["distant", "old", "non_cpcb", "bad_value"])
async def test_unusable_station_rejected(change: str) -> None:
    payload = {
        "status": "ok",
        "data": {
            "city": {"name": "Delhi, India", "geo": [28.61, 77.21]},
            "attributions": [{"name": "CPCB", "url": "https://cpcb.nic.in"}],
            "time": {"iso": datetime.now(UTC).isoformat()},
            "iaqi": {"pm25": {"v": 150}},
        },
    }
    data = payload["data"]
    if change == "distant":
        data["city"]["geo"] = [19.07, 72.87]
    elif change == "old":
        data["time"]["iso"] = "2020-01-01T00:00:00+00:00"
    elif change == "non_cpcb":
        data["attributions"] = []
    else:
        data["iaqi"]["pm25"]["v"] = -10
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda r: httpx.Response(200, json=payload))
    ) as client:
        with pytest.raises(ValueError):
            await WAQIProvider(token="test", client=client).get_latest_readings(28.61, 77.21)
