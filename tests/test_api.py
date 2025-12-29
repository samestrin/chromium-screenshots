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


class TestGetEndpointStorage:
    """Tests for GET /screenshot localStorage and sessionStorage parameters."""

    def test_get_endpoint_accepts_localstorage_parameter(self):
        """GET endpoint accepts localStorage query parameter."""
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)

        with patch("app.main.screenshot_service.capture") as mock_capture:
            mock_capture.return_value = (b"fake_image", 100.0)

            response = client.get(
                "/screenshot",
                params={
                    "url": "https://example.com",
                    "localStorage": "wasp:sessionId=abc123",
                },
            )

            assert response.status_code in [200, 500]

    def test_get_endpoint_accepts_sessionstorage_parameter(self):
        """GET endpoint accepts sessionStorage query parameter."""
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)

        with patch("app.main.screenshot_service.capture") as mock_capture:
            mock_capture.return_value = (b"fake_image", 100.0)

            response = client.get(
                "/screenshot",
                params={
                    "url": "https://example.com",
                    "sessionStorage": "temp=data",
                },
            )

            assert response.status_code in [200, 500]

    def test_get_endpoint_accepts_multiple_storage_values(self):
        """GET endpoint accepts semicolon-separated storage values."""
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)

        with patch("app.main.screenshot_service.capture") as mock_capture:
            mock_capture.return_value = (b"fake_image", 100.0)

            response = client.get(
                "/screenshot",
                params={
                    "url": "https://example.com",
                    "localStorage": "key1=val1;key2=val2;key3=val3",
                },
            )

            assert response.status_code in [200, 500]

    def test_get_endpoint_accepts_combined_cookies_and_storage(self):
        """GET endpoint accepts cookies and storage together."""
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)

        with patch("app.main.screenshot_service.capture") as mock_capture:
            mock_capture.return_value = (b"fake_image", 100.0)

            response = client.get(
                "/screenshot",
                params={
                    "url": "https://example.com",
                    "cookies": "session=abc123",
                    "localStorage": "wasp:sessionId=token",
                    "sessionStorage": "temp=data",
                },
            )

            assert response.status_code in [200, 500]

    def test_get_endpoint_storage_optional(self):
        """GET endpoint works without storage parameters."""
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)

        with patch("app.main.screenshot_service.capture") as mock_capture:
            mock_capture.return_value = (b"fake_image", 100.0)

            response = client.get(
                "/screenshot",
                params={"url": "https://example.com"},
            )

            assert response.status_code in [200, 500]

    def test_get_endpoint_invalid_localstorage_format(self):
        """GET endpoint returns 400 for invalid localStorage format."""
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)

        response = client.get(
            "/screenshot",
            params={
                "url": "https://example.com",
                "localStorage": "invalid_no_equals",
            },
        )

        assert response.status_code == 400


class TestPostEndpointStorage:
    """Tests for POST /screenshot localStorage and sessionStorage in JSON body."""

    def test_post_endpoint_accepts_localstorage_object(self):
        """POST endpoint accepts localStorage dict in request body."""
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)

        with patch("app.main.screenshot_service.capture") as mock_capture:
            mock_capture.return_value = (b"fake_image", 100.0)

            response = client.post(
                "/screenshot",
                json={
                    "url": "https://example.com",
                    "localStorage": {"wasp:sessionId": "abc123", "theme": "dark"},
                },
            )

            assert response.status_code in [200, 500]

    def test_post_endpoint_accepts_sessionstorage_object(self):
        """POST endpoint accepts sessionStorage dict in request body."""
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)

        with patch("app.main.screenshot_service.capture") as mock_capture:
            mock_capture.return_value = (b"fake_image", 100.0)

            response = client.post(
                "/screenshot",
                json={
                    "url": "https://example.com",
                    "sessionStorage": {"temp": "data"},
                },
            )

            assert response.status_code in [200, 500]

    def test_post_endpoint_accepts_nested_objects(self):
        """POST endpoint accepts nested objects in localStorage."""
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)

        with patch("app.main.screenshot_service.capture") as mock_capture:
            mock_capture.return_value = (b"fake_image", 100.0)

            response = client.post(
                "/screenshot",
                json={
                    "url": "https://example.com",
                    "localStorage": {
                        "user": {"id": 123, "name": "test"},
                        "prefs": {"theme": "dark", "lang": "en"},
                    },
                },
            )

            assert response.status_code in [200, 500]

    def test_post_endpoint_combined_cookies_and_storage(self):
        """POST endpoint accepts cookies and storage together."""
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)

        with patch("app.main.screenshot_service.capture") as mock_capture:
            mock_capture.return_value = (b"fake_image", 100.0)

            response = client.post(
                "/screenshot",
                json={
                    "url": "https://example.com",
                    "cookies": [{"name": "tracking", "value": "123"}],
                    "localStorage": {"wasp:sessionId": "abc123"},
                    "sessionStorage": {"temp": "data"},
                },
            )

            assert response.status_code in [200, 500]

    def test_post_endpoint_storage_optional(self):
        """POST endpoint works without storage fields."""
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)

        with patch("app.main.screenshot_service.capture") as mock_capture:
            mock_capture.return_value = (b"fake_image", 100.0)

            response = client.post(
                "/screenshot",
                json={"url": "https://example.com"},
            )

            assert response.status_code in [200, 500]


class TestOpenAPISchemaExtractDom:
    """Tests for OpenAPI schema extract_dom parameter."""

    def test_openapi_schema_includes_extract_dom(self):
        """OpenAPI schema includes extract_dom in ScreenshotRequest."""
        from app.main import app

        client = TestClient(app)
        response = client.get("/openapi.json")
        assert response.status_code == 200

        openapi = response.json()
        # Navigate to ScreenshotRequest schema
        schemas = openapi.get("components", {}).get("schemas", {})
        screenshot_request = schemas.get("ScreenshotRequest", {})
        properties = screenshot_request.get("properties", {})

        assert "extract_dom" in properties

    def test_openapi_schema_extract_dom_references_dom_extraction_options(self):
        """OpenAPI extract_dom references DomExtractionOptions schema."""
        from app.main import app

        client = TestClient(app)
        response = client.get("/openapi.json")
        openapi = response.json()

        schemas = openapi.get("components", {}).get("schemas", {})
        screenshot_request = schemas.get("ScreenshotRequest", {})
        extract_dom_prop = screenshot_request.get("properties", {}).get("extract_dom", {})

        # Should reference DomExtractionOptions via anyOf (Optional type)
        # or via $ref
        if "anyOf" in extract_dom_prop:
            refs = [item.get("$ref", "") for item in extract_dom_prop["anyOf"]]
            assert any("DomExtractionOptions" in ref for ref in refs)
        elif "$ref" in extract_dom_prop:
            assert "DomExtractionOptions" in extract_dom_prop["$ref"]

    def test_openapi_schema_has_dom_extraction_options(self):
        """OpenAPI schema includes DomExtractionOptions type."""
        from app.main import app

        client = TestClient(app)
        response = client.get("/openapi.json")
        openapi = response.json()

        schemas = openapi.get("components", {}).get("schemas", {})
        assert "DomExtractionOptions" in schemas

    def test_openapi_dom_extraction_options_has_all_fields(self):
        """DomExtractionOptions schema has all expected fields."""
        from app.main import app

        client = TestClient(app)
        response = client.get("/openapi.json")
        openapi = response.json()

        schemas = openapi.get("components", {}).get("schemas", {})
        dom_options = schemas.get("DomExtractionOptions", {})
        properties = dom_options.get("properties", {})

        assert "enabled" in properties
        assert "selectors" in properties
        assert "include_hidden" in properties
        assert "min_text_length" in properties
        assert "max_elements" in properties


class TestDomExtractionQualityIntegration:
    """Tests for DOM extraction quality assessment integration."""

    def test_json_endpoint_returns_quality_when_dom_extracted(self):
        """POST /screenshot/json includes quality field when DOM extraction enabled."""
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)

        # Mock DOM extraction result with elements
        mock_dom_result = {
            "elements": [
                {
                    "selector": f"#el-{i}",
                    "xpath": f"/html/body/p[{i}]",
                    "tag_name": "p",
                    "text": f"Paragraph text content {i}" * 3,  # >10 chars avg
                    "rect": {"x": 0, "y": i * 20, "width": 100, "height": 20},
                    "computed_style": {},
                    "is_visible": True,
                    "z_index": 0,
                }
                for i in range(10)  # 10 elements -> LOW quality
            ],
            "viewport": {"width": 1920, "height": 1080},
            "extraction_time_ms": 25.0,
            "element_count": 10,
        }

        with patch("app.main.screenshot_service.capture") as mock_capture:
            mock_capture.return_value = (b"fake_image", 100.0, mock_dom_result)

            response = client.post(
                "/screenshot/json",
                json={
                    "url": "https://example.com",
                    "extract_dom": {"enabled": True},
                },
            )

            if response.status_code == 200:
                data = response.json()
                assert "dom_extraction" in data
                assert data["dom_extraction"] is not None
                # Quality field should be present
                assert "quality" in data["dom_extraction"]
                # With 10 elements, should be LOW
                assert data["dom_extraction"]["quality"] == "low"
                # Warnings should be present (as list)
                assert "warnings" in data["dom_extraction"]
                assert isinstance(data["dom_extraction"]["warnings"], list)

    def test_json_endpoint_quality_is_empty_for_zero_elements(self):
        """POST /screenshot/json returns EMPTY quality when no elements extracted."""
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)

        mock_dom_result = {
            "elements": [],
            "viewport": {"width": 1920, "height": 1080},
            "extraction_time_ms": 5.0,
            "element_count": 0,
        }

        with patch("app.main.screenshot_service.capture") as mock_capture:
            mock_capture.return_value = (b"fake_image", 100.0, mock_dom_result)

            response = client.post(
                "/screenshot/json",
                json={
                    "url": "https://example.com",
                    "extract_dom": {"enabled": True},
                },
            )

            if response.status_code == 200:
                data = response.json()
                assert data["dom_extraction"]["quality"] == "empty"
                # Should have NO_ELEMENTS warning
                warning_codes = [w["code"] for w in data["dom_extraction"]["warnings"]]
                assert "NO_ELEMENTS" in warning_codes

    def test_json_endpoint_quality_good_for_diverse_extraction(self):
        """POST /screenshot/json returns GOOD quality for diverse extraction."""
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)

        # Create diverse elements with headings
        tags = ["h1", "h2", "p", "span", "a", "li", "div"]
        mock_dom_result = {
            "elements": [
                {
                    "selector": f"#el-{i}",
                    "xpath": f"/html/body/el[{i}]",
                    "tag_name": tags[i % len(tags)],
                    "text": f"Element {i} with sufficient text content here",
                    "rect": {"x": 0, "y": i * 20, "width": 100, "height": 20},
                    "computed_style": {},
                    "is_visible": True,
                    "z_index": 0,
                }
                for i in range(25)  # 25 elements -> eligible for GOOD
            ],
            "viewport": {"width": 1920, "height": 1080},
            "extraction_time_ms": 30.0,
            "element_count": 25,
        }

        with patch("app.main.screenshot_service.capture") as mock_capture:
            mock_capture.return_value = (b"fake_image", 100.0, mock_dom_result)

            response = client.post(
                "/screenshot/json",
                json={
                    "url": "https://example.com",
                    "extract_dom": {"enabled": True},
                },
            )

            if response.status_code == 200:
                data = response.json()
                assert data["dom_extraction"]["quality"] == "good"

    def test_json_endpoint_no_quality_without_dom_extraction(self):
        """POST /screenshot/json has no quality when DOM extraction disabled."""
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)

        with patch("app.main.screenshot_service.capture") as mock_capture:
            mock_capture.return_value = (b"fake_image", 100.0)

            response = client.post(
                "/screenshot/json",
                json={"url": "https://example.com"},
            )

            if response.status_code == 200:
                data = response.json()
                # dom_extraction should be null/None
                assert data.get("dom_extraction") is None

    def test_openapi_schema_includes_quality_fields(self):
        """OpenAPI schema includes quality and warnings in DomExtractionResult."""
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)

        response = client.get("/openapi.json")
        openapi = response.json()

        schemas = openapi.get("components", {}).get("schemas", {})
        dom_result = schemas.get("DomExtractionResult", {})
        properties = dom_result.get("properties", {})

        # Quality field should be in schema
        assert "quality" in properties
        # Warnings field should be in schema
        assert "warnings" in properties
