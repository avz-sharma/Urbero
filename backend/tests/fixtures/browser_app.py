"""Run the real FastAPI browser flow against replayed or unavailable providers."""

import os
from unittest.mock import patch

import httpx
from fastapi import FastAPI

from backend.app.planner.grok import GrokPlannerClient
from backend.app.providers.openmeteo import OpenMeteoProvider
from backend.app.providers.pipeline import AirQualityPipeline
from backend.app.providers.waqi import WAQIProvider
from backend.tests.fixtures.providers import model_client


def _create_app(model_transport: httpx.AsyncClient) -> FastAPI:
    disabled_credentials = dict.fromkeys(
        (
            "SUPABASE_URL",
            "SUPABASE_SERVICE_ROLE_KEY",
            "GROK_API_KEY",
            "XAI_API_KEY",
            "GEMINI_API_KEY",
        ),
        "",
    )
    with patch.dict(os.environ, disabled_credentials):
        from backend.app.api import routes

        model = OpenMeteoProvider(model_transport)
        routes.openmeteo_provider = model
        routes.air_quality = AirQualityPipeline(WAQIProvider(token=""), model)
        routes.grok_client = GrokPlannerClient()
        return routes.create_app()


def create_replay_app() -> FastAPI:
    return _create_app(model_client())


def create_outage_app() -> FastAPI:
    transport = httpx.MockTransport(lambda request: httpx.Response(503))
    return _create_app(httpx.AsyncClient(transport=transport))
