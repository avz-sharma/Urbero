"""Check security directives on the app document and API documentation."""

from pathlib import Path

import pytest
from fastapi.staticfiles import StaticFiles
from starlette.testclient import TestClient

from backend.app.api.routes import create_app


def _directives(policy: str) -> dict[str, list[str]]:
    directives = {}
    for directive in policy.split(";"):
        name, *sources = directive.split()
        directives[name] = sources
    return directives


def test_app_document_uses_local_scripts_and_fonts() -> None:
    app = create_app()
    frontend = Path(__file__).resolve().parents[2] / "frontend"
    # The Python-only CI job has the HTML source but skips building JavaScript assets.
    if not (frontend / "dist").is_dir():
        app.mount("/", StaticFiles(directory=frontend, html=True), name="frontend")

    response = TestClient(app).get("/")

    assert response.status_code == 200
    policy = _directives(response.headers["Content-Security-Policy"])
    assert policy["script-src"] == ["'self'"]
    assert policy["style-src"] == ["'self'", "'unsafe-inline'"]
    assert policy["font-src"] == ["'self'"]
    assert policy["frame-ancestors"] == ["'none'"]
    assert "fonts.googleapis.com" not in response.text
    assert "fonts.gstatic.com" not in response.text


@pytest.mark.parametrize("path", ["/docs", "/docs/oauth2-redirect", "/redoc"])
def test_openapi_docs_keep_their_script_exception(path: str) -> None:
    response = TestClient(create_app()).get(path)

    assert response.status_code == 200
    policy = _directives(response.headers["Content-Security-Policy"])
    assert policy["script-src"] == ["'self'", "https://cdn.jsdelivr.net", "'unsafe-inline'"]
    assert policy["frame-ancestors"] == ["'none'"]
    if path == "/redoc":
        assert "https://fonts.googleapis.com" in policy["style-src"]
        assert "https://fonts.gstatic.com" in policy["font-src"]
