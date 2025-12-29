"""Tests for Pydantic models - Cookie model validation."""

import pytest
from pydantic import ValidationError


class TestExtractionQualityEnum:
    """Tests for ExtractionQuality enum."""

    def test_extraction_quality_enum_exists(self):
        """ExtractionQuality enum exists with 4 values."""
        from app.models import ExtractionQuality

        assert hasattr(ExtractionQuality, "GOOD")
        assert hasattr(ExtractionQuality, "LOW")
        assert hasattr(ExtractionQuality, "POOR")
        assert hasattr(ExtractionQuality, "EMPTY")
        # Verify exactly 4 values
        assert len(ExtractionQuality) == 4

    def test_extraction_quality_string_values(self):
        """ExtractionQuality enum values serialize to lowercase strings."""
        from app.models import ExtractionQuality

        assert ExtractionQuality.GOOD.value == "good"
        assert ExtractionQuality.LOW.value == "low"
        assert ExtractionQuality.POOR.value == "poor"
        assert ExtractionQuality.EMPTY.value == "empty"

    def test_extraction_quality_is_str_enum(self):
        """ExtractionQuality inherits from str for JSON serialization."""
        from app.models import ExtractionQuality
        from enum import Enum

        # Should inherit from both str and Enum
        assert issubclass(ExtractionQuality, str)
        assert issubclass(ExtractionQuality, Enum)
        # Value access works correctly
        assert ExtractionQuality.GOOD.value == "good"
        assert ExtractionQuality.LOW.value == "low"

    def test_extraction_quality_json_serialization(self):
        """ExtractionQuality serializes correctly in Pydantic model."""
        from app.models import ExtractionQuality

        # Create a simple test to verify JSON serialization
        import json
        quality = ExtractionQuality.GOOD
        # str(Enum) with str base should work directly
        assert json.dumps({"quality": quality}) == '{"quality": "good"}'

    def test_extraction_quality_comparison(self):
        """ExtractionQuality values can be compared."""
        from app.models import ExtractionQuality

        assert ExtractionQuality.GOOD == ExtractionQuality.GOOD
        assert ExtractionQuality.GOOD != ExtractionQuality.LOW
        # String comparison works due to str base
        assert ExtractionQuality.GOOD == "good"


class TestQualityWarningModel:
    """Tests for QualityWarning Pydantic model."""

    def test_quality_warning_creation_with_all_fields(self):
        """QualityWarning model accepts code, message, suggestion fields."""
        from app.models import QualityWarning

        warning = QualityWarning(
            code="low_element_count",
            message="Page has very few elements",
            suggestion="Check if page fully loaded"
        )
        assert warning.code == "low_element_count"
        assert warning.message == "Page has very few elements"
        assert warning.suggestion == "Check if page fully loaded"

    def test_quality_warning_json_serialization(self):
        """QualityWarning serializes to JSON correctly."""
        from app.models import QualityWarning

        warning = QualityWarning(
            code="no_headings",
            message="No heading elements found",
            suggestion="Consider adding h1-h6 elements"
        )
        json_str = warning.model_dump_json()
        assert "no_headings" in json_str
        assert "No heading elements found" in json_str
        assert "Consider adding h1-h6 elements" in json_str

    def test_quality_warning_json_deserialization(self):
        """QualityWarning deserializes from JSON correctly."""
        from app.models import QualityWarning
        import json

        json_str = '{"code": "many_hidden", "message": "Many hidden elements", "suggestion": "Review visibility"}'
        warning = QualityWarning.model_validate_json(json_str)
        assert warning.code == "many_hidden"
        assert warning.message == "Many hidden elements"
        assert warning.suggestion == "Review visibility"

    def test_quality_warning_model_dump(self):
        """QualityWarning model_dump returns dict."""
        from app.models import QualityWarning

        warning = QualityWarning(
            code="test",
            message="Test message",
            suggestion="Test suggestion"
        )
        data = warning.model_dump()
        assert isinstance(data, dict)
        assert data["code"] == "test"
        assert data["message"] == "Test message"
        assert data["suggestion"] == "Test suggestion"

    def test_quality_warning_missing_code_raises_error(self):
        """QualityWarning without code raises ValidationError."""
        from app.models import QualityWarning

        with pytest.raises(ValidationError) as exc_info:
            QualityWarning(message="msg", suggestion="sug")  # type: ignore
        assert "code" in str(exc_info.value)

    def test_quality_warning_missing_message_raises_error(self):
        """QualityWarning without message raises ValidationError."""
        from app.models import QualityWarning

        with pytest.raises(ValidationError) as exc_info:
            QualityWarning(code="test", suggestion="sug")  # type: ignore
        assert "message" in str(exc_info.value)

    def test_quality_warning_missing_suggestion_raises_error(self):
        """QualityWarning without suggestion raises ValidationError."""
        from app.models import QualityWarning

        with pytest.raises(ValidationError) as exc_info:
            QualityWarning(code="test", message="msg")  # type: ignore
        assert "suggestion" in str(exc_info.value)

    def test_quality_warning_wrong_type_raises_error(self):
        """QualityWarning with non-string field raises ValidationError."""
        from app.models import QualityWarning

        with pytest.raises(ValidationError):
            QualityWarning(code=123, message="msg", suggestion="sug")  # type: ignore

    def test_quality_warning_special_characters(self):
        """QualityWarning handles special characters in strings."""
        from app.models import QualityWarning

        warning = QualityWarning(
            code="test_code",
            message='Message with "quotes" and newline\n',
            suggestion="Suggestion with unicode: café"
        )
        # Round-trip via JSON
        json_str = warning.model_dump_json()
        restored = QualityWarning.model_validate_json(json_str)
        assert restored.message == 'Message with "quotes" and newline\n'
        assert restored.suggestion == "Suggestion with unicode: café"

    def test_quality_warning_has_field_descriptions(self):
        """QualityWarning fields have descriptions for OpenAPI."""
        from app.models import QualityWarning

        schema = QualityWarning.model_json_schema()
        properties = schema.get("properties", {})

        assert "description" in properties.get("code", {})
        assert "description" in properties.get("message", {})
        assert "description" in properties.get("suggestion", {})


class TestDomExtractionOptionsModel:
    """Tests for DomExtractionOptions Pydantic model."""

    def test_dom_extraction_options_default_values(self):
        """DomExtractionOptions has correct default values."""
        from app.models import DomExtractionOptions

        options = DomExtractionOptions()
        assert options.enabled is False
        assert isinstance(options.selectors, list)
        assert "h1" in options.selectors
        assert "p" in options.selectors
        assert options.include_hidden is False
        assert options.min_text_length == 1
        assert options.max_elements == 500

    def test_dom_extraction_options_enabled_true(self):
        """DomExtractionOptions accepts enabled=True."""
        from app.models import DomExtractionOptions

        options = DomExtractionOptions(enabled=True)
        assert options.enabled is True

    def test_dom_extraction_options_custom_selectors(self):
        """DomExtractionOptions accepts custom selectors list."""
        from app.models import DomExtractionOptions

        custom_selectors = ["h1", "h2", "p", "span"]
        options = DomExtractionOptions(selectors=custom_selectors)
        assert options.selectors == custom_selectors

    def test_dom_extraction_options_include_hidden(self):
        """DomExtractionOptions accepts include_hidden=True."""
        from app.models import DomExtractionOptions

        options = DomExtractionOptions(include_hidden=True)
        assert options.include_hidden is True

    def test_dom_extraction_options_min_text_length(self):
        """DomExtractionOptions accepts custom min_text_length."""
        from app.models import DomExtractionOptions

        options = DomExtractionOptions(min_text_length=3)
        assert options.min_text_length == 3

    def test_dom_extraction_options_max_elements(self):
        """DomExtractionOptions accepts custom max_elements."""
        from app.models import DomExtractionOptions

        options = DomExtractionOptions(max_elements=200)
        assert options.max_elements == 200

    def test_dom_extraction_options_has_field_descriptions(self):
        """DomExtractionOptions fields have descriptions for OpenAPI."""
        from app.models import DomExtractionOptions

        schema = DomExtractionOptions.model_json_schema()
        properties = schema.get("properties", {})

        # Check that key fields have descriptions
        assert "description" in properties.get("selectors", {})
        assert "description" in properties.get("include_hidden", {})
        assert "description" in properties.get("min_text_length", {})
        assert "description" in properties.get("max_elements", {})


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


class TestScreenshotRequestExtractDom:
    """Tests for ScreenshotRequest extract_dom field."""

    def test_screenshot_request_has_extract_dom_field(self):
        """ScreenshotRequest has extract_dom optional field."""
        from app.models import ScreenshotRequest

        request = ScreenshotRequest(url="https://example.com")
        assert hasattr(request, "extract_dom")

    def test_screenshot_request_extract_dom_defaults_to_none(self):
        """ScreenshotRequest extract_dom defaults to None."""
        from app.models import ScreenshotRequest

        request = ScreenshotRequest(url="https://example.com")
        assert request.extract_dom is None

    def test_screenshot_request_accepts_dom_extraction_options(self):
        """ScreenshotRequest accepts DomExtractionOptions object."""
        from app.models import DomExtractionOptions, ScreenshotRequest

        options = DomExtractionOptions(enabled=True)
        request = ScreenshotRequest(url="https://example.com", extract_dom=options)
        assert request.extract_dom is not None
        assert request.extract_dom.enabled is True

    def test_screenshot_request_extract_dom_with_custom_selectors(self):
        """ScreenshotRequest accepts DomExtractionOptions with custom selectors."""
        from app.models import DomExtractionOptions, ScreenshotRequest

        options = DomExtractionOptions(
            enabled=True,
            selectors=["h1", "p"],
            max_elements=100
        )
        request = ScreenshotRequest(url="https://example.com", extract_dom=options)
        assert request.extract_dom.selectors == ["h1", "p"]
        assert request.extract_dom.max_elements == 100


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


class TestBoundingRectModel:
    """Tests for BoundingRect Pydantic model."""

    def test_bounding_rect_accepts_all_fields(self):
        """BoundingRect accepts x, y, width, height as floats."""
        from app.models import BoundingRect

        rect = BoundingRect(x=10.5, y=20.3, width=100.0, height=50.7)
        assert rect.x == 10.5
        assert rect.y == 20.3
        assert rect.width == 100.0
        assert rect.height == 50.7

    def test_bounding_rect_requires_all_fields(self):
        """BoundingRect requires all four fields."""
        from app.models import BoundingRect

        with pytest.raises(ValidationError):
            BoundingRect(x=10.0)  # type: ignore

    def test_bounding_rect_accepts_integers(self):
        """BoundingRect accepts integers (coerced to float)."""
        from app.models import BoundingRect

        rect = BoundingRect(x=10, y=20, width=100, height=50)
        assert isinstance(rect.x, float)
        assert isinstance(rect.y, float)

    def test_bounding_rect_zero_values(self):
        """BoundingRect accepts zero values."""
        from app.models import BoundingRect

        rect = BoundingRect(x=0, y=0, width=0, height=0)
        assert rect.x == 0
        assert rect.width == 0

    def test_bounding_rect_has_field_descriptions(self):
        """BoundingRect fields have descriptions for OpenAPI."""
        from app.models import BoundingRect

        schema = BoundingRect.model_json_schema()
        properties = schema.get("properties", {})

        assert "description" in properties.get("x", {})
        assert "description" in properties.get("y", {})
        assert "description" in properties.get("width", {})
        assert "description" in properties.get("height", {})


class TestDomElementModel:
    """Tests for DomElement Pydantic model."""

    def test_dom_element_accepts_all_fields(self):
        """DomElement accepts all 8 required fields."""
        from app.models import BoundingRect, DomElement

        rect = BoundingRect(x=10, y=20, width=100, height=50)
        element = DomElement(
            selector="#main-title",
            xpath="/html/body/div/h1",
            tag_name="h1",
            text="Welcome",
            rect=rect,
            computed_style={"color": "rgb(0, 0, 0)"},
            is_visible=True,
            z_index=0,
        )
        assert element.selector == "#main-title"
        assert element.xpath == "/html/body/div/h1"
        assert element.tag_name == "h1"
        assert element.text == "Welcome"
        assert element.rect.x == 10
        assert element.is_visible is True
        assert element.z_index == 0

    def test_dom_element_requires_all_fields(self):
        """DomElement requires all fields."""
        from app.models import DomElement

        with pytest.raises(ValidationError):
            DomElement(selector="#id")  # type: ignore

    def test_dom_element_rect_is_bounding_rect(self):
        """DomElement rect field accepts BoundingRect."""
        from app.models import BoundingRect, DomElement

        rect = BoundingRect(x=0, y=0, width=200, height=100)
        element = DomElement(
            selector=".content",
            xpath="/html/body/p",
            tag_name="p",
            text="Some text",
            rect=rect,
            computed_style={},
            is_visible=True,
            z_index=1,
        )
        assert isinstance(element.rect, BoundingRect)

    def test_dom_element_computed_style_is_dict(self):
        """DomElement computed_style accepts dict."""
        from app.models import BoundingRect, DomElement

        rect = BoundingRect(x=0, y=0, width=50, height=20)
        element = DomElement(
            selector="span",
            xpath="/html/body/span",
            tag_name="span",
            text="Test",
            rect=rect,
            computed_style={"font-size": "16px", "color": "blue"},
            is_visible=True,
            z_index=0,
        )
        assert element.computed_style["font-size"] == "16px"

    def test_dom_element_empty_text(self):
        """DomElement accepts empty text string."""
        from app.models import BoundingRect, DomElement

        rect = BoundingRect(x=0, y=0, width=10, height=10)
        element = DomElement(
            selector="button",
            xpath="/html/body/button",
            tag_name="button",
            text="",
            rect=rect,
            computed_style={},
            is_visible=True,
            z_index=0,
        )
        assert element.text == ""

    def test_dom_element_negative_z_index(self):
        """DomElement accepts negative z-index values."""
        from app.models import BoundingRect, DomElement

        rect = BoundingRect(x=0, y=0, width=10, height=10)
        element = DomElement(
            selector="div",
            xpath="/html/body/div",
            tag_name="div",
            text="Background",
            rect=rect,
            computed_style={},
            is_visible=True,
            z_index=-1,
        )
        assert element.z_index == -1

    def test_dom_element_has_field_descriptions(self):
        """DomElement fields have descriptions for OpenAPI."""
        from app.models import DomElement

        schema = DomElement.model_json_schema()
        properties = schema.get("properties", {})

        assert "description" in properties.get("selector", {})
        assert "description" in properties.get("xpath", {})
        assert "description" in properties.get("tag_name", {})
        assert "description" in properties.get("text", {})
        assert "description" in properties.get("is_visible", {})
        assert "description" in properties.get("z_index", {})


class TestDomExtractionResultModel:
    """Tests for DomExtractionResult Pydantic model."""

    def test_dom_extraction_result_accepts_all_fields(self):
        """DomExtractionResult accepts elements, viewport, extraction_time_ms, element_count."""
        from app.models import BoundingRect, DomElement, DomExtractionResult

        rect = BoundingRect(x=0, y=0, width=100, height=50)
        element = DomElement(
            selector="h1",
            xpath="/html/body/h1",
            tag_name="h1",
            text="Title",
            rect=rect,
            computed_style={},
            is_visible=True,
            z_index=0,
        )
        result = DomExtractionResult(
            elements=[element],
            viewport={"width": 1920, "height": 1080},
            extraction_time_ms=25.5,
            element_count=1,
        )
        assert len(result.elements) == 1
        assert result.viewport["width"] == 1920
        assert result.extraction_time_ms == 25.5
        assert result.element_count == 1

    def test_dom_extraction_result_empty_elements(self):
        """DomExtractionResult accepts empty elements list."""
        from app.models import DomExtractionResult

        result = DomExtractionResult(
            elements=[],
            viewport={"width": 1920, "height": 1080},
            extraction_time_ms=10.0,
            element_count=0,
        )
        assert result.elements == []
        assert result.element_count == 0

    def test_dom_extraction_result_requires_all_fields(self):
        """DomExtractionResult requires all fields."""
        from app.models import DomExtractionResult

        with pytest.raises(ValidationError):
            DomExtractionResult(elements=[])  # type: ignore

    def test_dom_extraction_result_viewport_dict(self):
        """DomExtractionResult viewport is a dict with dimensions."""
        from app.models import DomExtractionResult

        result = DomExtractionResult(
            elements=[],
            viewport={"width": 1280, "height": 720, "deviceScaleFactor": 2},
            extraction_time_ms=5.0,
            element_count=0,
        )
        assert result.viewport["width"] == 1280
        assert result.viewport["deviceScaleFactor"] == 2

    def test_dom_extraction_result_has_field_descriptions(self):
        """DomExtractionResult fields have descriptions for OpenAPI."""
        from app.models import DomExtractionResult

        schema = DomExtractionResult.model_json_schema()
        properties = schema.get("properties", {})

        assert "description" in properties.get("elements", {})
        assert "description" in properties.get("viewport", {})
        assert "description" in properties.get("extraction_time_ms", {})
        assert "description" in properties.get("element_count", {})


class TestScreenshotResponseDomExtraction:
    """Tests for ScreenshotResponse dom_extraction field."""

    def test_screenshot_response_has_dom_extraction_field(self):
        """ScreenshotResponse has optional dom_extraction field."""
        from app.models import ScreenshotResponse

        response = ScreenshotResponse(
            url="https://example.com",
            screenshot_type="viewport",
            format="png",
            width=1920,
            height=1080,
            file_size_bytes=12345,
            capture_time_ms=150.0,
        )
        assert hasattr(response, "dom_extraction")

    def test_screenshot_response_dom_extraction_defaults_to_none(self):
        """ScreenshotResponse dom_extraction defaults to None."""
        from app.models import ScreenshotResponse

        response = ScreenshotResponse(
            url="https://example.com",
            screenshot_type="viewport",
            format="png",
            width=1920,
            height=1080,
            file_size_bytes=12345,
            capture_time_ms=150.0,
        )
        assert response.dom_extraction is None

    def test_screenshot_response_accepts_dom_extraction_result(self):
        """ScreenshotResponse accepts DomExtractionResult."""
        from app.models import DomExtractionResult, ScreenshotResponse

        dom_result = DomExtractionResult(
            elements=[],
            viewport={"width": 1920, "height": 1080},
            extraction_time_ms=20.0,
            element_count=0,
        )
        response = ScreenshotResponse(
            url="https://example.com",
            screenshot_type="viewport",
            format="png",
            width=1920,
            height=1080,
            file_size_bytes=12345,
            capture_time_ms=150.0,
            dom_extraction=dom_result,
        )
        assert response.dom_extraction is not None
        assert response.dom_extraction.element_count == 0


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
