"""Tests for Pydantic models - Cookie model validation."""

import pytest
from pydantic import ValidationError


class TestCookieModel:
    """Tests for Cookie Pydantic model."""

    def test_cookie_minimal_required_fields(self):
        """Cookie model accepts minimal required fields (name and value)."""
        from app.models import Cookie

        cookie = Cookie(name="session", value="abc123")
        assert cookie.name == "session"
        assert cookie.value == "abc123"

    def test_cookie_all_fields(self):
        """Cookie model accepts all 8 fields."""
        from app.models import Cookie

        cookie = Cookie(
            name="session",
            value="abc123",
            domain="example.com",
            path="/app",
            httpOnly=True,
            secure=True,
            sameSite="Strict",
            expires=1735689600,  # Unix timestamp
        )
        assert cookie.name == "session"
        assert cookie.value == "abc123"
        assert cookie.domain == "example.com"
        assert cookie.path == "/app"
        assert cookie.httpOnly is True
        assert cookie.secure is True
        assert cookie.sameSite == "Strict"
        assert cookie.expires == 1735689600

    def test_cookie_optional_fields_default_to_none(self):
        """Optional fields default to None when not provided."""
        from app.models import Cookie

        cookie = Cookie(name="test", value="value")
        assert cookie.domain is None
        assert cookie.path is None
        assert cookie.httpOnly is None
        assert cookie.secure is None
        assert cookie.sameSite is None
        assert cookie.expires is None

    def test_cookie_missing_name_raises_validation_error(self):
        """Cookie without name raises ValidationError."""
        from app.models import Cookie

        with pytest.raises(ValidationError) as exc_info:
            Cookie(value="abc123")  # type: ignore
        assert "name" in str(exc_info.value)

    def test_cookie_missing_value_raises_validation_error(self):
        """Cookie without value raises ValidationError."""
        from app.models import Cookie

        with pytest.raises(ValidationError) as exc_info:
            Cookie(name="session")  # type: ignore
        assert "value" in str(exc_info.value)

    def test_cookie_invalid_samesite_raises_validation_error(self):
        """Cookie with invalid sameSite value raises ValidationError."""
        from app.models import Cookie

        with pytest.raises(ValidationError) as exc_info:
            Cookie(name="session", value="abc", sameSite="Invalid")
        assert "sameSite" in str(exc_info.value).lower() or "same" in str(exc_info.value).lower()

    def test_cookie_valid_samesite_values(self):
        """Cookie accepts valid sameSite values: Strict, Lax, None."""
        from app.models import Cookie

        for same_site in ["Strict", "Lax", "None"]:
            cookie = Cookie(name="test", value="val", sameSite=same_site)
            assert cookie.sameSite == same_site

    def test_cookie_repr_masks_value(self):
        """Cookie __repr__ should mask the value for security."""
        from app.models import Cookie

        cookie = Cookie(name="session", value="supersecret123")
        repr_str = repr(cookie)
        # Value should not appear in repr
        assert "supersecret123" not in repr_str
        # Name can appear
        assert "session" in repr_str

    def test_cookie_path_defaults_behavior(self):
        """Cookie with path specified."""
        from app.models import Cookie

        cookie = Cookie(name="test", value="val", path="/api")
        assert cookie.path == "/api"

    def test_cookie_expires_as_integer(self):
        """Cookie expires field accepts integer (Unix timestamp)."""
        from app.models import Cookie

        cookie = Cookie(name="test", value="val", expires=1735689600)
        assert cookie.expires == 1735689600


class TestScreenshotRequestCookies:
    """Tests for ScreenshotRequest cookies field."""

    def test_screenshot_request_accepts_cookies(self):
        """ScreenshotRequest accepts optional cookies field."""
        from app.models import Cookie, ScreenshotRequest

        cookies = [
            Cookie(name="session", value="abc123"),
            Cookie(name="user_id", value="456"),
        ]
        request = ScreenshotRequest(url="https://example.com", cookies=cookies)
        assert request.cookies is not None
        assert len(request.cookies) == 2

    def test_screenshot_request_cookies_default_none(self):
        """ScreenshotRequest cookies defaults to None."""
        from app.models import ScreenshotRequest

        request = ScreenshotRequest(url="https://example.com")
        assert request.cookies is None

    def test_screenshot_request_empty_cookies_list(self):
        """ScreenshotRequest accepts empty cookies list."""
        from app.models import ScreenshotRequest

        request = ScreenshotRequest(url="https://example.com", cookies=[])
        assert request.cookies == []

    def test_screenshot_request_validates_cookie_objects(self):
        """ScreenshotRequest validates cookie objects in list."""
        from app.models import ScreenshotRequest

        with pytest.raises(ValidationError):
            # Invalid cookie - missing required fields
            ScreenshotRequest(
                url="https://example.com",
                cookies=[{"invalid": "cookie"}],  # type: ignore
            )


class TestScreenshotRequestStorage:
    """Tests for ScreenshotRequest localStorage and sessionStorage fields."""

    def test_screenshot_request_has_localstorage_field(self):
        """ScreenshotRequest has localStorage field of type dict[str, Any]."""
        from app.models import ScreenshotRequest

        request = ScreenshotRequest(
            url="https://example.com",
            localStorage={"wasp:sessionId": "abc123"}
        )
        assert request.localStorage is not None
        assert request.localStorage == {"wasp:sessionId": "abc123"}

    def test_screenshot_request_has_sessionstorage_field(self):
        """ScreenshotRequest has sessionStorage field of type dict[str, Any]."""
        from app.models import ScreenshotRequest

        request = ScreenshotRequest(
            url="https://example.com",
            sessionStorage={"temp-data": "xyz"}
        )
        assert request.sessionStorage is not None
        assert request.sessionStorage == {"temp-data": "xyz"}

    def test_screenshot_request_storage_defaults_to_none(self):
        """localStorage and sessionStorage default to None when not provided."""
        from app.models import ScreenshotRequest

        request = ScreenshotRequest(url="https://example.com")
        assert request.localStorage is None
        assert request.sessionStorage is None

    def test_screenshot_request_accepts_empty_storage_dict(self):
        """ScreenshotRequest accepts empty dicts for storage fields."""
        from app.models import ScreenshotRequest

        request = ScreenshotRequest(
            url="https://example.com",
            localStorage={},
            sessionStorage={}
        )
        assert request.localStorage == {}
        assert request.sessionStorage == {}

    def test_screenshot_request_storage_accepts_nested_objects(self):
        """Storage fields accept nested objects as values (will be JSON-stringified later)."""
        from app.models import ScreenshotRequest

        request = ScreenshotRequest(
            url="https://example.com",
            localStorage={
                "user-preferences": {"theme": "dark", "lang": "en"},
                "simple": "value"
            }
        )
        assert request.localStorage["user-preferences"] == {"theme": "dark", "lang": "en"}
        assert request.localStorage["simple"] == "value"

    def test_screenshot_request_storage_special_characters_in_keys(self):
        """Storage fields accept special characters like colons in keys."""
        from app.models import ScreenshotRequest

        request = ScreenshotRequest(
            url="https://example.com",
            localStorage={"wasp:sessionId": "token123", "color-theme": "light"}
        )
        assert "wasp:sessionId" in request.localStorage
        assert "color-theme" in request.localStorage

    def test_screenshot_request_combined_cookies_and_storage(self):
        """ScreenshotRequest accepts cookies and storage together."""
        from app.models import Cookie, ScreenshotRequest

        request = ScreenshotRequest(
            url="https://example.com",
            cookies=[Cookie(name="tracking", value="123")],
            localStorage={"wasp:sessionId": "abc123"},
            sessionStorage={"temp": "data"}
        )
        assert request.cookies is not None
        assert len(request.cookies) == 1
        assert request.localStorage == {"wasp:sessionId": "abc123"}
        assert request.sessionStorage == {"temp": "data"}
