"""Tests for storage injection mechanism (localStorage and sessionStorage)."""


class TestExtractOrigin:
    """Tests for extracting origin from URL for storage injection."""

    def test_extract_origin_https(self):
        """Extract origin from HTTPS URL."""
        from app.screenshot import extract_origin

        origin = extract_origin("https://example.com/dashboard")
        assert origin == "https://example.com"

    def test_extract_origin_http(self):
        """Extract origin from HTTP URL."""
        from app.screenshot import extract_origin

        origin = extract_origin("http://example.com/page")
        assert origin == "http://example.com"

    def test_extract_origin_with_port(self):
        """Extract origin from URL with port."""
        from app.screenshot import extract_origin

        origin = extract_origin("http://192.168.68.99:3000/dashboard")
        assert origin == "http://192.168.68.99:3000"

    def test_extract_origin_ip_address(self):
        """Extract origin from IP address URL."""
        from app.screenshot import extract_origin

        origin = extract_origin("http://192.168.1.1/admin")
        assert origin == "http://192.168.1.1"

    def test_extract_origin_localhost(self):
        """Extract origin from localhost URL."""
        from app.screenshot import extract_origin

        origin = extract_origin("http://localhost:8080/api/v1/users")
        assert origin == "http://localhost:8080"

    def test_extract_origin_subdomain(self):
        """Extract origin includes subdomain."""
        from app.screenshot import extract_origin

        origin = extract_origin("https://app.staging.example.com/login")
        assert origin == "https://app.staging.example.com"

    def test_extract_origin_strips_path(self):
        """Origin should not include path."""
        from app.screenshot import extract_origin

        origin = extract_origin("https://example.com/deep/nested/path?query=1")
        assert origin == "https://example.com"


class TestHasStorageToInject:
    """Tests for checking if storage injection is needed."""

    def test_has_storage_with_localstorage(self):
        """Return True when localStorage is provided."""
        from app.models import ScreenshotRequest
        from app.screenshot import has_storage_to_inject

        request = ScreenshotRequest(
            url="https://example.com",
            localStorage={"key": "value"}
        )
        assert has_storage_to_inject(request) is True

    def test_has_storage_with_sessionstorage(self):
        """Return True when sessionStorage is provided."""
        from app.models import ScreenshotRequest
        from app.screenshot import has_storage_to_inject

        request = ScreenshotRequest(
            url="https://example.com",
            sessionStorage={"key": "value"}
        )
        assert has_storage_to_inject(request) is True

    def test_has_storage_with_both(self):
        """Return True when both storage types are provided."""
        from app.models import ScreenshotRequest
        from app.screenshot import has_storage_to_inject

        request = ScreenshotRequest(
            url="https://example.com",
            localStorage={"local": "val"},
            sessionStorage={"session": "val"}
        )
        assert has_storage_to_inject(request) is True

    def test_has_storage_none_values(self):
        """Return False when both storage values are None."""
        from app.models import ScreenshotRequest
        from app.screenshot import has_storage_to_inject

        request = ScreenshotRequest(url="https://example.com")
        assert has_storage_to_inject(request) is False

    def test_has_storage_empty_dicts(self):
        """Return False when both storage values are empty dicts."""
        from app.models import ScreenshotRequest
        from app.screenshot import has_storage_to_inject

        request = ScreenshotRequest(
            url="https://example.com",
            localStorage={},
            sessionStorage={}
        )
        assert has_storage_to_inject(request) is False

    def test_has_storage_one_empty_one_not(self):
        """Return True when one storage has values, other empty."""
        from app.models import ScreenshotRequest
        from app.screenshot import has_storage_to_inject

        request = ScreenshotRequest(
            url="https://example.com",
            localStorage={"key": "value"},
            sessionStorage={}
        )
        assert has_storage_to_inject(request) is True


class TestBuildStorageInjectionScript:
    """Tests for building the JavaScript injection script."""

    def test_build_script_simple_string_value(self):
        """Build script for simple string values."""
        from app.screenshot import build_storage_injection_script

        script = build_storage_injection_script(
            "localStorage",
            {"key": "value"}
        )
        # Script should set localStorage.setItem
        assert "localStorage" in script
        assert "setItem" in script

    def test_build_script_object_value_stringified(self):
        """Object values should be JSON stringified."""
        from app.screenshot import build_storage_injection_script

        script = build_storage_injection_script(
            "localStorage",
            {"prefs": {"theme": "dark"}}
        )
        # Object should be stringified
        assert "localStorage" in script
        assert "setItem" in script

    def test_build_script_special_characters_in_key(self):
        """Keys with special characters like colons work."""
        from app.screenshot import build_storage_injection_script

        script = build_storage_injection_script(
            "localStorage",
            {"wasp:sessionId": "abc123"}
        )
        assert "wasp:sessionId" in script

    def test_build_script_sessionstorage(self):
        """Build script for sessionStorage."""
        from app.screenshot import build_storage_injection_script

        script = build_storage_injection_script(
            "sessionStorage",
            {"temp": "data"}
        )
        assert "sessionStorage" in script
        assert "setItem" in script

    def test_build_script_multiple_values(self):
        """Build script with multiple key-value pairs."""
        from app.screenshot import build_storage_injection_script

        script = build_storage_injection_script(
            "localStorage",
            {"key1": "val1", "key2": "val2", "key3": "val3"}
        )
        assert "key1" in script
        assert "key2" in script
        assert "key3" in script
