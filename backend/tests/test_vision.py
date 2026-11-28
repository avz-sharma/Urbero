"""Tests for Phase 6 Room Vision analysis and security guardrails."""

import base64
import io

import pytest
from PIL import Image

from backend.app.planner.schemas import RoomVisionExtraction
from backend.app.planner.vision import (
    MAX_IMAGE_BYTES,
    analyze_room_photo,
    validate_and_strip_exif,
)


def _create_test_image(format_name: str = "JPEG", size: tuple[int, int] = (100, 100)) -> bytes:
    """Helper to generate in-memory dummy image bytes."""
    buf = io.BytesIO()
    img = Image.new("RGB", size, color="blue")
    img.save(buf, format=format_name)
    return buf.getvalue()


def test_validate_and_strip_exif_valid_jpeg() -> None:
    """Verify clean JPEG passes validation and returns valid bytes."""
    raw = _create_test_image("JPEG")
    cleaned = validate_and_strip_exif(raw, "image/jpeg")
    assert len(cleaned) > 0

    # Ensure output is a readable image
    with Image.open(io.BytesIO(cleaned)) as img:
        assert img.size == (100, 100)
        assert img.format == "JPEG"


def test_validate_and_strip_exif_valid_png() -> None:
    """Verify clean PNG passes validation."""
    raw = _create_test_image("PNG")
    cleaned = validate_and_strip_exif(raw, "image/png")
    assert len(cleaned) > 0


def test_validate_rejects_unsupported_mime() -> None:
    """Verify rejection of forbidden MIME types (PDF, GIF, SVG)."""
    raw = _create_test_image("JPEG")
    with pytest.raises(ValueError, match="Unsupported image MIME type"):
        validate_and_strip_exif(raw, "image/gif")

    with pytest.raises(ValueError, match="Unsupported image MIME type"):
        validate_and_strip_exif(raw, "application/pdf")


def test_validate_rejects_oversized_file() -> None:
    """Verify rejection of images exceeding MAX_IMAGE_BYTES (5MB)."""
    oversized = b"0" * (MAX_IMAGE_BYTES + 1024)
    with pytest.raises(ValueError, match="exceeds 5MB limit"):
        validate_and_strip_exif(oversized, "image/jpeg")


def test_validate_rejects_corrupted_bytes() -> None:
    """Verify rejection of corrupt or malformed image data."""
    corrupted = b"NOT_A_REAL_IMAGE_BYTES"
    with pytest.raises(ValueError, match="Invalid or corrupted image data"):
        validate_and_strip_exif(corrupted, "image/jpeg")


def test_analyze_room_photo_deterministic_fallback() -> None:
    """Verify deterministic fallback pre-fill when Grok client is None."""
    raw = _create_test_image("JPEG")
    res = analyze_room_photo(raw, "image/jpeg", grok_client=None)

    assert isinstance(res, RoomVisionExtraction)
    assert res.is_valid_room is False
    assert res.confidence_score == 0
    assert "manually" in res.rejection_reason


@pytest.mark.parametrize(("image_format", "mime"), [("JPEG", "image/jpeg"), ("WEBP", "image/webp")])
def test_analyze_room_photo_mock_grok(image_format: str, mime: str) -> None:
    """Verify Grok client structured output extraction with prompt injection defense."""

    class MockMessage:
        content = (
            '{"is_valid_room": true, "rejection_reason": null, '
            '"estimated_length_m": 5.5, "estimated_width_m": 4.2, "estimated_height_m": 2.8, '
            '"has_kitchen_chimney": true, "burns_incense_agarbatti": false, '
            '"has_unsealed_balcony": true, "confidence_score": 0.9, '
            '"explanation": "Identified master bedroom with balcony door."}'
        )

    class MockChoice:
        message = MockMessage()

    class MockResponse:
        choices = [MockChoice()]

    class MockCompletions:
        def create(self, model: str, messages: list, response_format: dict) -> object:
            # Verify system prompt instructs injection defense
            prompt_text = messages[0]["content"][0]["text"]
            assert "UNTRUSTED CONTENT" in prompt_text
            image_url = messages[0]["content"][1]["image_url"]["url"]
            prefix, encoded = image_url.split(",", 1)
            assert prefix == f"data:{mime};base64"
            with Image.open(io.BytesIO(base64.b64decode(encoded))) as image:
                assert image.format == image_format
                assert not image.getexif()
            return MockResponse()

    class MockChat:
        completions = MockCompletions()

    class MockGrokClient:
        chat = MockChat()
        vision_model = "grok-2-vision-1212"

    raw = io.BytesIO()
    with Image.new("RGB", (100, 100), color="blue") as image:
        exif = image.getexif()
        exif[270] = "Example room photo"
        image.save(raw, format=image_format, exif=exif)
    res = analyze_room_photo(raw.getvalue(), mime, grok_client=MockGrokClient())
    assert res.is_valid_room is True
    assert res.estimated_length_m == 5.5
    assert res.has_kitchen_chimney is True
    assert res.has_unsealed_balcony is True
    assert res.confidence_score == 0.9
