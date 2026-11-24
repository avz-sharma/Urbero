"""API security layer: rate limiting, CORS, security headers, and request validation."""

import logging
import os
import re

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp, Message, Receive, Scope, Send

MAX_PAYLOAD_BYTES: int = 1_048_576  # 1 MB

# Global rate limiter (in-memory)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[os.getenv("RATE_LIMIT_DEFAULT", "60/minute")],
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enforces defensive HTTP response headers across all API endpoints."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        raw_response = await call_next(request)
        assert isinstance(raw_response, Response)
        raw_response.headers["X-Content-Type-Options"] = "nosniff"
        raw_response.headers["X-Frame-Options"] = "DENY"
        raw_response.headers["X-XSS-Protection"] = "1; mode=block"
        raw_response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        raw_response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        docs = request.url.path in {"/docs", "/docs/oauth2-redirect", "/redoc"}
        script_sources = "'self' https://cdn.jsdelivr.net 'unsafe-inline'" if docs else "'self'"
        raw_response.headers["Content-Security-Policy"] = (
            f"default-src 'self'; script-src {script_sources}; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
            "font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https://fastapi.tiangolo.com; "
            "object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
        )
        return raw_response


class ContentLengthLimitMiddleware:
    """Bound actual streamed body bytes, including requests without Content-Length."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["method"] not in {"POST", "PUT", "PATCH"}:
            await self.app(scope, receive, send)
            return
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body.extend(message.get("body", b""))
            if len(body) > MAX_PAYLOAD_BYTES:
                response = JSONResponse(
                    status_code=413,
                    content={"detail": "Request entity too large. Maximum payload size is 1MB."},
                )
                await response(scope, receive, send)
                return
            if not message.get("more_body", False):
                break
        delivered = False

        async def replay() -> Message:
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        await self.app(scope, replay, send)


def setup_security(app: FastAPI) -> None:
    """Register all security middleware, CORS allowlist, and rate limit handlers."""
    # HTTP access logs include query strings (GPS/token). Keep application event logs only.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").disabled = True
    # SlowAPI includes the raw client address in its rate-limit warning.
    logging.getLogger("slowapi").setLevel(logging.ERROR)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
    origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000")
    origins = [origin for o in origins_str.split(",") if (origin := o.strip()) and origin != "*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    app.add_middleware(ContentLengthLimitMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)


def sanitize_user_input(text: str) -> str:
    """Strip dangerous characters and script injections from free text."""
    if not text:
        return ""
    # Strip HTML tags and null bytes
    cleaned = re.sub(r"<[^>]*>", "", text)
    cleaned = cleaned.replace("\x00", "")
    return cleaned.strip()
