"""Server-side Gemini transport for validated planner narratives."""

import asyncio
import logging
import os
import re
from collections.abc import Callable
from typing import TypeVar

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class GeminiClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.model = os.getenv("GEMINI_MODEL", "")
        if self.api_key and not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]*", self.model):
            raise ValueError("Set GEMINI_MODEL to a valid model ID when Gemini is enabled.")

    async def generate(
        self, prompt: str, response_type: type[T], *, accept: Callable[[T], bool] | None = None
    ) -> T | None:
        if not self.api_key:
            return None
        async with httpx.AsyncClient(timeout=httpx.Timeout(12.0, connect=3.0)) as client:
            for attempt in range(2):
                try:
                    response = await client.post(
                        f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent",
                        headers={"x-goog-api-key": self.api_key},
                        json={
                            "contents": [{"parts": [{"text": prompt}]}],
                            "generationConfig": {
                                "responseMimeType": "application/json",
                                "responseJsonSchema": response_type.model_json_schema(),
                            },
                        },
                    )
                    response.raise_for_status()
                    candidate = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                    result = response_type.model_validate_json(candidate, strict=True)
                    if accept is not None and not accept(result):
                        raise ValueError("Gemini response does not satisfy request constraints")
                    return result
                except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError) as error:
                    logger.warning(
                        "gemini_generation_failed attempt=%s error_type=%s",
                        attempt + 1,
                        type(error).__name__,
                    )
                    if attempt == 0:
                        await asyncio.sleep(0.2)
        return None
