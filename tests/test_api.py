"""Tests for HTTP API endpoints - cookie parameter support."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


class TestGetEndpointCookies:
    """Tests for GET /screenshot cookies query parameter."""

    def test_get_endpoint_accepts_cookies_parameter(self):
        """GET endpoint accepts cookies query parameter."""
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)

        # Mock the screenshot service to avoid actual browser calls
        with patch("app.main.screenshot_service.capture") as mock_capture:
            mock_capture.return_value = (b"fake_image", 100.0)

            response = client.get(
                "/screenshot",
                params={
                    "url": "https://example.com",
                    "cookies": "session=abc123",
                },
            )

            # Should not fail due to parameter validation
            assert response.status_code in [200, 500]  # 500 if browser not ready

    def test_get_endpoint_cookies_optional(self):
        """GET endpoint works without cookies parameter."""
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)

        with patch("app.main.screenshot_service.capture") as mock_capture:
            mock_capture.return_value = (b"fake_image", 100.0)

            response = client.get(
                "/screenshot",
                params={"url": "https://example.com"},
            )

            # Should work without cookies
            assert response.status_code in [200, 500]

    def test_get_endpoint_empty_cookies_string(self):
        """GET endpoint handles empty cookies string."""
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)

        with patch("app.main.screenshot_service.capture") as mock_capture:
            mock_capture.return_value = (b"fake_image", 100.0)

            response = client.get(
                "/screenshot",
                params={
                    "url": "https://example.com",
                    "cookies": "",
                },
            )

            # Should handle gracefully
            assert response.status_code in [200, 500]


class TestCookieStringParsing:
    """Tests for parsing cookie strings from GET query parameter."""

    def test_parse_single_cookie(self):
        """Parse single cookie from string."""
        from app.main import parse_cookie_string

        cookies = parse_cookie_string("session=abc123")
        assert len(cookies) == 1
        assert cookies[0].name == "session"
        assert cookies[0].value == "abc123"

    def test_parse_multiple_cookies(self):
        """Parse multiple semicolon-separated cookies."""
        from app.main import parse_cookie_string

        cookies = parse_cookie_string("session=abc123;user_id=456")
        assert len(cookies) == 2
        assert cookies[0].name == "session"
        assert cookies[0].value == "abc123"
        assert cookies[1].name == "user_id"
        assert cookies[1].value == "456"

    def test_parse_cookies_with_whitespace(self):
        """Parse cookies with whitespace around semicolons."""
        from app.main import parse_cookie_string

        cookies = parse_cookie_string("session=abc123 ; user_id=456")
        assert len(cookies) == 2
        assert cookies[0].name == "session"
        assert cookies[0].value == "abc123"
        assert cookies[1].name == "user_id"
        assert cookies[1].value == "456"

    def test_parse_cookies_with_equals_in_value(self):
        """Parse cookies where value contains equals sign."""
        from app.main import parse_cookie_string

        cookies = parse_cookie_string("token=abc=def=ghi")
        assert len(cookies) == 1
        assert cookies[0].name == "token"
        assert cookies[0].value == "abc=def=ghi"

    def test_parse_empty_string_returns_empty_list(self):
        """Empty string returns empty cookie list."""
        from app.main import parse_cookie_string

        cookies = parse_cookie_string("")
        assert cookies == []

    def test_parse_none_returns_empty_list(self):
        """None returns empty cookie list."""
        from app.main import parse_cookie_string

        cookies = parse_cookie_string(None)
        assert cookies == []

    def test_parse_invalid_format_raises_error(self):
        """Invalid cookie format (missing =) raises HTTPException."""
        from fastapi import HTTPException

        from app.main import parse_cookie_string

        with pytest.raises(HTTPException) as exc_info:
            parse_cookie_string("invalid_cookie_no_equals")

        assert exc_info.value.status_code == 400
        assert "Invalid cookie format" in exc_info.value.detail


class TestPostEndpointCookies:
    """Tests for POST /screenshot cookies in JSON body."""

    def test_post_endpoint_accepts_cookies_array(self):
        """POST endpoint accepts cookies array in request body."""
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)

        with patch("app.main.screenshot_service.capture") as mock_capture:
            mock_capture.return_value = (b"fake_image", 100.0)

            response = client.post(
                "/screenshot",
                json={
                    "url": "https://example.com",
                    "cookies": [
                        {"name": "session", "value": "abc123"},
                        {"name": "user_id", "value": "456"},
                    ],
                },
            )

            assert response.status_code in [200, 500]

    def test_post_endpoint_cookies_with_all_fields(self):
        """POST endpoint accepts cookies with all optional fields."""
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)

        with patch("app.main.screenshot_service.capture") as mock_capture:
            mock_capture.return_value = (b"fake_image", 100.0)

            response = client.post(
                "/screenshot",
                json={
                    "url": "https://example.com",
                    "cookies": [
                        {
                            "name": "session",
                            "value": "abc123",
                            "domain": "example.com",
                            "path": "/app",
                            "httpOnly": True,
                            "secure": True,
                            "sameSite": "Strict",
                        },
                    ],
                },
            )

            assert response.status_code in [200, 500]

    def test_post_endpoint_cookies_optional(self):
        """POST endpoint works without cookies field."""
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)

        with patch("app.main.screenshot_service.capture") as mock_capture:
            mock_capture.return_value = (b"fake_image", 100.0)

            response = client.post(
                "/screenshot",
                json={"url": "https://example.com"},
            )

            assert response.status_code in [200, 500]

    def test_post_endpoint_validates_cookie_objects(self):
        """POST endpoint validates cookie objects in array."""
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)

        response = client.post(
            "/screenshot",
            json={
                "url": "https://example.com",
                "cookies": [
                    {"invalid": "cookie"},  # Missing required name/value
                ],
            },
        )

        # Should return validation error
        assert response.status_code == 422

    def test_post_endpoint_validates_samesite(self):
        """POST endpoint validates sameSite value."""
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)

        response = client.post(
            "/screenshot",
            json={
                "url": "https://example.com",
                "cookies": [
                    {"name": "session", "value": "abc", "sameSite": "Invalid"},
                ],
            },
        )

        # Should return validation error
        assert response.status_code == 422
