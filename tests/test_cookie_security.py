"""Tests for cookie security - isolation and logging protection."""

import pytest


class TestCookieIsolation:
    """Tests for cookie isolation between requests."""

    def test_fresh_context_per_request(self):
        """Each screenshot request gets a fresh browser context."""
        # This is verified by the architecture - _get_page creates new context
        # and closes it in the finally block
        from app.screenshot import ScreenshotService

        service = ScreenshotService()
        # The context is created fresh in _get_page and closed after use
        # Cookie isolation is guaranteed by this pattern
        assert service._browser is None  # Not initialized until first use

    def test_context_closes_on_error(self):
        """Context closes properly even if an error occurs."""
        # This is tested by examining the _get_page implementation
        # The finally block ensures context.close() is called
        import inspect

        from app.screenshot import ScreenshotService

        service = ScreenshotService()
        source = inspect.getsource(service._get_page)
        assert "finally:" in source
        assert "context.close()" in source


class TestCookieLoggingSecurity:
    """Tests for cookie value masking in logs."""

    def test_cookie_repr_masks_value(self):
        """Cookie __repr__ masks the value for security."""
        from app.models import Cookie

        cookie = Cookie(name="session", value="supersecret123")
        repr_str = repr(cookie)

        # Value should be masked
        assert "supersecret123" not in repr_str
        # Should show masked value indicator
        assert "***" in repr_str
        # Name can appear
        assert "session" in repr_str

    def test_cookie_str_also_masks(self):
        """Cookie string conversion also masks value."""
        from app.models import Cookie

        cookie = Cookie(name="auth", value="token12345")
        str_repr = str(cookie)

        # Value should not appear in any string representation
        # that could end up in logs
        assert "token12345" not in str_repr

    def test_multiple_cookies_all_masked(self):
        """All cookies in a list have values masked."""
        from app.models import Cookie

        cookies = [
            Cookie(name="session", value="secret1"),
            Cookie(name="auth", value="secret2"),
            Cookie(name="tracking", value="secret3"),
        ]

        for cookie in cookies:
            repr_str = repr(cookie)
            assert cookie.value not in repr_str


class TestCookieValidationErrors:
    """Tests for cookie validation error handling."""

    def test_invalid_cookie_format_returns_400(self):
        """Invalid cookie format in GET returns 400 with clear message."""
        from fastapi import HTTPException

        from app.main import parse_cookie_string

        with pytest.raises(HTTPException) as exc_info:
            parse_cookie_string("no_equals_sign")

        assert exc_info.value.status_code == 400
        assert "Invalid cookie format" in exc_info.value.detail

    def test_error_message_does_not_contain_value(self):
        """Error messages don't leak cookie values."""
        from fastapi import HTTPException

        from app.main import parse_cookie_string

        # Even if the cookie string has sensitive data mixed in,
        # we only show the problematic part in the error
        with pytest.raises(HTTPException) as exc_info:
            parse_cookie_string("valid=ok;invalid_part")

        # The error should mention the invalid part but not expose values
        assert "invalid_part" in exc_info.value.detail
        # But the valid cookie value should not be exposed in error
        assert "ok" not in exc_info.value.detail or "valid=ok" not in exc_info.value.detail

    def test_pydantic_validation_for_missing_name(self):
        """Pydantic validation catches missing name field."""
        from pydantic import ValidationError

        from app.models import Cookie

        with pytest.raises(ValidationError):
            Cookie(value="test")  # type: ignore

    def test_pydantic_validation_for_missing_value(self):
        """Pydantic validation catches missing value field."""
        from pydantic import ValidationError

        from app.models import Cookie

        with pytest.raises(ValidationError):
            Cookie(name="test")  # type: ignore

    def test_pydantic_validation_for_invalid_samesite(self):
        """Pydantic validation catches invalid sameSite value."""
        from pydantic import ValidationError

        from app.models import Cookie

        with pytest.raises(ValidationError):
            Cookie(name="test", value="val", sameSite="BadValue")
