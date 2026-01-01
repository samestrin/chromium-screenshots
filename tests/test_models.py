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
        from enum import Enum

        from app.models import ExtractionQuality

        # Should inherit from both str and Enum
        assert issubclass(ExtractionQuality, str)
        assert issubclass(ExtractionQuality, Enum)
        # Value access works correctly
        assert ExtractionQuality.GOOD.value == "good"
        assert ExtractionQuality.LOW.value == "low"

    def test_extraction_quality_json_serialization(self):
        """ExtractionQuality serializes correctly in Pydantic model."""
        # Create a simple test to verify JSON serialization
        import json

        from app.models import ExtractionQuality
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

        json_str = (
            '{"code": "many_hidden", "message": "Many hidden elements", '
            '"suggestion": "Review visibility"}'
        )
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
            suggestion="Suggestion with unicode: cafe"
        )
        # Round-trip via JSON
        json_str = warning.model_dump_json()
        restored = QualityWarning.model_validate_json(json_str)
        assert restored.message == 'Message with "quotes" and newline\n'
        assert restored.suggestion == "Suggestion with unicode: cafe"

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

    # Sprint 6.0: DOM Element Tile Enrichment Tests

    def test_dom_element_tile_index_optional(self):
        """DomElement accepts optional tile_index field."""
        from app.models import BoundingRect, DomElement

        rect = BoundingRect(x=10, y=20, width=100, height=50)
        element = DomElement(
            selector="#main",
            xpath="/html/body/div",
            tag_name="div",
            text="Content",
            rect=rect,
            computed_style={},
            is_visible=True,
            z_index=0,
            tile_index=2,
        )
        assert element.tile_index == 2

    def test_dom_element_tile_index_defaults_to_none(self):
        """DomElement tile_index defaults to None."""
        from app.models import BoundingRect, DomElement

        rect = BoundingRect(x=10, y=20, width=100, height=50)
        element = DomElement(
            selector="#main",
            xpath="/html/body/div",
            tag_name="div",
            text="Content",
            rect=rect,
            computed_style={},
            is_visible=True,
            z_index=0,
        )
        assert element.tile_index is None

    def test_dom_element_tile_relative_rect_optional(self):
        """DomElement accepts optional tile_relative_rect field."""
        from app.models import BoundingRect, DomElement

        rect = BoundingRect(x=100, y=950, width=100, height=50)
        tile_rect = BoundingRect(x=100, y=200, width=100, height=50)
        element = DomElement(
            selector="#main",
            xpath="/html/body/div",
            tag_name="div",
            text="Content",
            rect=rect,
            computed_style={},
            is_visible=True,
            z_index=0,
            tile_relative_rect=tile_rect,
        )
        assert element.tile_relative_rect is not None
        assert element.tile_relative_rect.y == 200

    def test_dom_element_tile_relative_rect_defaults_to_none(self):
        """DomElement tile_relative_rect defaults to None."""
        from app.models import BoundingRect, DomElement

        rect = BoundingRect(x=10, y=20, width=100, height=50)
        element = DomElement(
            selector="#main",
            xpath="/html/body/div",
            tag_name="div",
            text="Content",
            rect=rect,
            computed_style={},
            is_visible=True,
            z_index=0,
        )
        assert element.tile_relative_rect is None

    def test_dom_element_is_fixed_optional(self):
        """DomElement accepts optional is_fixed field."""
        from app.models import BoundingRect, DomElement

        rect = BoundingRect(x=0, y=0, width=100, height=50)
        element = DomElement(
            selector="#header",
            xpath="/html/body/header",
            tag_name="header",
            text="Fixed Header",
            rect=rect,
            computed_style={"position": "fixed"},
            is_visible=True,
            z_index=100,
            is_fixed=True,
        )
        assert element.is_fixed is True

    def test_dom_element_is_fixed_defaults_to_false(self):
        """DomElement is_fixed defaults to False."""
        from app.models import BoundingRect, DomElement

        rect = BoundingRect(x=10, y=20, width=100, height=50)
        element = DomElement(
            selector="#main",
            xpath="/html/body/div",
            tag_name="div",
            text="Content",
            rect=rect,
            computed_style={},
            is_visible=True,
            z_index=0,
        )
        assert element.is_fixed is False


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


class TestDomExtractionResultQuality:
    """Tests for DomExtractionResult quality extension fields."""

    def test_dom_extraction_result_with_quality_and_warnings(self):
        """DomExtractionResult accepts quality and warnings fields."""
        from app.models import DomExtractionResult, ExtractionQuality, QualityWarning

        warning = QualityWarning(
            code="low_element_count",
            message="Only 3 elements extracted",
            suggestion="Check if page fully loaded"
        )
        result = DomExtractionResult(
            elements=[],
            viewport={"width": 1920, "height": 1080},
            extraction_time_ms=10.0,
            element_count=3,
            quality=ExtractionQuality.POOR,
            warnings=[warning],
        )
        assert result.quality == ExtractionQuality.POOR
        assert len(result.warnings) == 1
        assert result.warnings[0].code == "low_element_count"

    def test_dom_extraction_result_backward_compatibility(self):
        """DomExtractionResult works without quality/warnings (backward compat)."""
        from app.models import DomExtractionResult

        result = DomExtractionResult(
            elements=[],
            viewport={"width": 1920, "height": 1080},
            extraction_time_ms=10.0,
            element_count=0,
        )
        # New fields should have defaults
        assert result.quality is None
        assert result.warnings == []

    def test_dom_extraction_result_quality_defaults_to_none(self):
        """DomExtractionResult quality defaults to None."""
        from app.models import DomExtractionResult

        result = DomExtractionResult(
            elements=[],
            viewport={"width": 1920, "height": 1080},
            extraction_time_ms=10.0,
            element_count=0,
        )
        assert result.quality is None

    def test_dom_extraction_result_warnings_defaults_to_empty_list(self):
        """DomExtractionResult warnings defaults to empty list."""
        from app.models import DomExtractionResult

        result = DomExtractionResult(
            elements=[],
            viewport={"width": 1920, "height": 1080},
            extraction_time_ms=10.0,
            element_count=0,
        )
        assert result.warnings == []
        assert isinstance(result.warnings, list)

    def test_dom_extraction_result_json_round_trip_with_quality(self):
        """DomExtractionResult with quality serializes and deserializes correctly."""
        from app.models import DomExtractionResult, ExtractionQuality, QualityWarning

        warning = QualityWarning(
            code="no_headings",
            message="No heading elements found",
            suggestion="Add h1-h6 elements"
        )
        result = DomExtractionResult(
            elements=[],
            viewport={"width": 1920, "height": 1080},
            extraction_time_ms=10.0,
            element_count=0,
            quality=ExtractionQuality.GOOD,
            warnings=[warning],
        )
        json_str = result.model_dump_json()
        restored = DomExtractionResult.model_validate_json(json_str)
        assert restored.quality == ExtractionQuality.GOOD
        assert len(restored.warnings) == 1
        assert restored.warnings[0].code == "no_headings"

    def test_dom_extraction_result_json_round_trip_legacy_format(self):
        """DomExtractionResult deserializes legacy JSON (without quality)."""
        from app.models import DomExtractionResult

        legacy_json = (
            '{"elements": [], "viewport": {"width": 1920, "height": 1080}, '
            '"extraction_time_ms": 10.0, "element_count": 0}'
        )
        result = DomExtractionResult.model_validate_json(legacy_json)
        assert result.quality is None
        assert result.warnings == []

    def test_dom_extraction_result_multiple_warnings(self):
        """DomExtractionResult handles multiple warnings."""
        from app.models import DomExtractionResult, ExtractionQuality, QualityWarning

        warnings = [
            QualityWarning(code="code1", message="msg1", suggestion="sug1"),
            QualityWarning(code="code2", message="msg2", suggestion="sug2"),
            QualityWarning(code="code3", message="msg3", suggestion="sug3"),
        ]
        result = DomExtractionResult(
            elements=[],
            viewport={"width": 1920, "height": 1080},
            extraction_time_ms=10.0,
            element_count=0,
            quality=ExtractionQuality.POOR,
            warnings=warnings,
        )
        assert len(result.warnings) == 3
        assert result.warnings[0].code == "code1"
        assert result.warnings[2].code == "code3"

    def test_dom_extraction_result_empty_quality_with_warnings(self):
        """DomExtractionResult allows EMPTY quality with warnings."""
        from app.models import DomExtractionResult, ExtractionQuality, QualityWarning

        warning = QualityWarning(
            code="no_elements",
            message="No elements extracted",
            suggestion="Check if page content exists"
        )
        result = DomExtractionResult(
            elements=[],
            viewport={"width": 1920, "height": 1080},
            extraction_time_ms=10.0,
            element_count=0,
            quality=ExtractionQuality.EMPTY,
            warnings=[warning],
        )
        assert result.quality == ExtractionQuality.EMPTY
        assert len(result.warnings) == 1

    def test_dom_extraction_result_good_quality_no_warnings(self):
        """DomExtractionResult allows GOOD quality with no warnings."""
        from app.models import DomExtractionResult, ExtractionQuality

        result = DomExtractionResult(
            elements=[],
            viewport={"width": 1920, "height": 1080},
            extraction_time_ms=10.0,
            element_count=25,
            quality=ExtractionQuality.GOOD,
            warnings=[],
        )
        assert result.quality == ExtractionQuality.GOOD
        assert result.warnings == []

    def test_dom_extraction_result_invalid_quality_raises_error(self):
        """DomExtractionResult rejects invalid quality value."""
        from app.models import DomExtractionResult

        with pytest.raises(ValidationError):
            DomExtractionResult(
                elements=[],
                viewport={"width": 1920, "height": 1080},
                extraction_time_ms=10.0,
                element_count=0,
                quality="invalid",  # type: ignore
            )

    def test_dom_extraction_result_quality_field_has_description(self):
        """DomExtractionResult quality field has OpenAPI description."""
        from app.models import DomExtractionResult

        schema = DomExtractionResult.model_json_schema()
        properties = schema.get("properties", {})

        assert "quality" in properties
        # Quality field should be documented
        assert "description" in properties.get("quality", {})

    def test_dom_extraction_result_warnings_field_has_description(self):
        """DomExtractionResult warnings field has OpenAPI description."""
        from app.models import DomExtractionResult

        schema = DomExtractionResult.model_json_schema()
        properties = schema.get("properties", {})

        assert "warnings" in properties
        # Warnings field should be documented
        assert "description" in properties.get("warnings", {})


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
            image_base64="dGVzdA==",
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
            image_base64="dGVzdA==",
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
            image_base64="dGVzdA==",
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


class TestDomExtractionOptionsMetricsFields:
    """Tests for DomExtractionOptions opt-in metrics/vision hint fields."""

    def test_dom_extraction_options_has_include_metrics_field(self):
        """DomExtractionOptions has include_metrics field."""
        from app.models import DomExtractionOptions

        options = DomExtractionOptions()
        assert hasattr(options, "include_metrics")

    def test_dom_extraction_options_include_metrics_defaults_false(self):
        """DomExtractionOptions include_metrics defaults to False."""
        from app.models import DomExtractionOptions

        options = DomExtractionOptions()
        assert options.include_metrics is False

    def test_dom_extraction_options_include_metrics_accepts_true(self):
        """DomExtractionOptions include_metrics accepts True."""
        from app.models import DomExtractionOptions

        options = DomExtractionOptions(include_metrics=True)
        assert options.include_metrics is True

    def test_dom_extraction_options_has_include_vision_hints_field(self):
        """DomExtractionOptions has include_vision_hints field."""
        from app.models import DomExtractionOptions

        options = DomExtractionOptions()
        assert hasattr(options, "include_vision_hints")

    def test_dom_extraction_options_include_vision_hints_defaults_false(self):
        """DomExtractionOptions include_vision_hints defaults to False."""
        from app.models import DomExtractionOptions

        options = DomExtractionOptions()
        assert options.include_vision_hints is False

    def test_dom_extraction_options_include_vision_hints_accepts_true(self):
        """DomExtractionOptions include_vision_hints accepts True."""
        from app.models import DomExtractionOptions

        options = DomExtractionOptions(include_vision_hints=True)
        assert options.include_vision_hints is True

    def test_dom_extraction_options_has_target_vision_model_field(self):
        """DomExtractionOptions has target_vision_model field."""
        from app.models import DomExtractionOptions

        options = DomExtractionOptions()
        assert hasattr(options, "target_vision_model")

    def test_dom_extraction_options_target_vision_model_defaults_none(self):
        """DomExtractionOptions target_vision_model defaults to None."""
        from app.models import DomExtractionOptions

        options = DomExtractionOptions()
        assert options.target_vision_model is None

    def test_dom_extraction_options_target_vision_model_accepts_claude(self):
        """DomExtractionOptions target_vision_model accepts 'claude'."""
        from app.models import DomExtractionOptions

        options = DomExtractionOptions(target_vision_model="claude")
        assert options.target_vision_model == "claude"

    def test_dom_extraction_options_target_vision_model_accepts_gemini(self):
        """DomExtractionOptions target_vision_model accepts 'gemini'."""
        from app.models import DomExtractionOptions

        options = DomExtractionOptions(target_vision_model="gemini")
        assert options.target_vision_model == "gemini"

    def test_dom_extraction_options_target_vision_model_accepts_gpt4v(self):
        """DomExtractionOptions target_vision_model accepts 'gpt4v'."""
        from app.models import DomExtractionOptions

        options = DomExtractionOptions(target_vision_model="gpt4v")
        assert options.target_vision_model == "gpt4v"

    def test_dom_extraction_options_target_vision_model_accepts_qwen(self):
        """DomExtractionOptions target_vision_model accepts 'qwen-vl-max'."""
        from app.models import DomExtractionOptions

        options = DomExtractionOptions(target_vision_model="qwen-vl-max")
        assert options.target_vision_model == "qwen-vl-max"

    def test_dom_extraction_options_target_vision_model_invalid_raises_error(self):
        """DomExtractionOptions target_vision_model rejects invalid values."""
        from app.models import DomExtractionOptions

        with pytest.raises(ValidationError) as exc_info:
            DomExtractionOptions(target_vision_model="invalid_model")
        assert "target_vision_model" in str(exc_info.value).lower()

    def test_dom_extraction_options_backward_compatibility(self):
        """DomExtractionOptions works without new fields (backward compat)."""
        from app.models import DomExtractionOptions

        # Existing usage should still work
        options = DomExtractionOptions(
            enabled=True,
            selectors=["h1", "p"],
            include_hidden=False,
            min_text_length=1,
            max_elements=500
        )
        # Original fields work
        assert options.enabled is True
        assert options.selectors == ["h1", "p"]
        # New fields have defaults
        assert options.include_metrics is False
        assert options.include_vision_hints is False
        assert options.target_vision_model is None

    def test_dom_extraction_options_all_new_fields_together(self):
        """DomExtractionOptions accepts all new fields together."""
        from app.models import DomExtractionOptions

        options = DomExtractionOptions(
            enabled=True,
            include_metrics=True,
            include_vision_hints=True,
            target_vision_model="claude"
        )
        assert options.include_metrics is True
        assert options.include_vision_hints is True
        assert options.target_vision_model == "claude"

    def test_dom_extraction_options_new_fields_have_descriptions(self):
        """DomExtractionOptions new fields have descriptions for OpenAPI."""
        from app.models import DomExtractionOptions

        schema = DomExtractionOptions.model_json_schema()
        properties = schema.get("properties", {})

        assert "description" in properties.get("include_metrics", {})
        assert "description" in properties.get("include_vision_hints", {})
        assert "description" in properties.get("target_vision_model", {})


class TestQualityMetricsModel:
    """Tests for QualityMetrics Pydantic model (Sprint 5.0 Story 01)."""

    # === Model Existence and Structure ===

    def test_quality_metrics_model_exists(self):
        """QualityMetrics model exists and is importable."""
        from app.models import QualityMetrics

        assert QualityMetrics is not None

    def test_quality_metrics_has_count_fields(self):
        """QualityMetrics has all 5 count fields."""
        from app.models import QualityMetrics

        schema = QualityMetrics.model_json_schema()
        properties = schema.get("properties", {})

        assert "element_count" in properties
        assert "visible_count" in properties
        assert "hidden_count" in properties
        assert "heading_count" in properties
        assert "unique_tag_count" in properties

    def test_quality_metrics_has_ratio_fields(self):
        """QualityMetrics has both ratio fields."""
        from app.models import QualityMetrics

        schema = QualityMetrics.model_json_schema()
        properties = schema.get("properties", {})

        assert "visible_ratio" in properties
        assert "hidden_ratio" in properties

    def test_quality_metrics_has_tag_analysis_fields(self):
        """QualityMetrics has tag analysis fields."""
        from app.models import QualityMetrics

        schema = QualityMetrics.model_json_schema()
        properties = schema.get("properties", {})

        assert "unique_tags" in properties
        assert "has_headings" in properties
        assert "tag_distribution" in properties

    def test_quality_metrics_has_text_stats_fields(self):
        """QualityMetrics has text statistics fields."""
        from app.models import QualityMetrics

        schema = QualityMetrics.model_json_schema()
        properties = schema.get("properties", {})

        assert "total_text_length" in properties
        assert "avg_text_length" in properties
        assert "min_text_length" in properties
        assert "max_text_length" in properties

    # === Model Instantiation ===

    def test_quality_metrics_instantiation_with_valid_data(self):
        """QualityMetrics can be instantiated with valid data."""
        from app.models import QualityMetrics

        metrics = QualityMetrics(
            element_count=25,
            visible_count=20,
            hidden_count=5,
            heading_count=3,
            unique_tag_count=6,
            visible_ratio=0.8,
            hidden_ratio=0.2,
            unique_tags=["h1", "h2", "p", "span", "a", "li"],
            has_headings=True,
            tag_distribution={"h1": 1, "h2": 2, "p": 10, "span": 5, "a": 4, "li": 3},
            total_text_length=1500,
            avg_text_length=60.0,
            min_text_length=5,
            max_text_length=200,
        )
        assert metrics.element_count == 25
        assert metrics.visible_count == 20
        assert metrics.visible_ratio == 0.8
        assert metrics.has_headings is True

    def test_quality_metrics_empty_extraction(self):
        """QualityMetrics handles empty extraction (zero elements)."""
        from app.models import QualityMetrics

        metrics = QualityMetrics(
            element_count=0,
            visible_count=0,
            hidden_count=0,
            heading_count=0,
            unique_tag_count=0,
            visible_ratio=0.0,
            hidden_ratio=0.0,
            unique_tags=[],
            has_headings=False,
            tag_distribution={},
            total_text_length=0,
            avg_text_length=0.0,
            min_text_length=0,
            max_text_length=0,
        )
        assert metrics.element_count == 0
        assert metrics.unique_tags == []
        assert metrics.tag_distribution == {}

    def test_quality_metrics_all_hidden_elements(self):
        """QualityMetrics handles all hidden elements case."""
        from app.models import QualityMetrics

        metrics = QualityMetrics(
            element_count=10,
            visible_count=0,
            hidden_count=10,
            heading_count=0,
            unique_tag_count=1,
            visible_ratio=0.0,
            hidden_ratio=1.0,
            unique_tags=["div"],
            has_headings=False,
            tag_distribution={"div": 10},
            total_text_length=0,
            avg_text_length=0.0,
            min_text_length=0,
            max_text_length=0,
        )
        assert metrics.hidden_ratio == 1.0
        assert metrics.visible_ratio == 0.0
        assert metrics.hidden_count == 10

    def test_quality_metrics_single_tag_type(self):
        """QualityMetrics handles single tag type extraction."""
        from app.models import QualityMetrics

        metrics = QualityMetrics(
            element_count=20,
            visible_count=20,
            hidden_count=0,
            heading_count=0,
            unique_tag_count=1,
            visible_ratio=1.0,
            hidden_ratio=0.0,
            unique_tags=["p"],
            has_headings=False,
            tag_distribution={"p": 20},
            total_text_length=1000,
            avg_text_length=50.0,
            min_text_length=10,
            max_text_length=100,
        )
        assert metrics.unique_tags == ["p"]
        assert metrics.unique_tag_count == 1
        assert metrics.tag_distribution == {"p": 20}

    # === Field Validation ===

    def test_quality_metrics_count_fields_reject_negative(self):
        """QualityMetrics count fields reject negative values."""
        from app.models import QualityMetrics

        with pytest.raises(ValidationError) as exc_info:
            QualityMetrics(
                element_count=-1,
                visible_count=0,
                hidden_count=0,
                heading_count=0,
                unique_tag_count=0,
                visible_ratio=0.0,
                hidden_ratio=0.0,
                unique_tags=[],
                has_headings=False,
                tag_distribution={},
                total_text_length=0,
                avg_text_length=0.0,
                min_text_length=0,
                max_text_length=0,
            )
        assert "element_count" in str(exc_info.value).lower()

    def test_quality_metrics_ratio_rejects_above_one(self):
        """QualityMetrics ratio fields reject values > 1.0."""
        from app.models import QualityMetrics

        with pytest.raises(ValidationError) as exc_info:
            QualityMetrics(
                element_count=10,
                visible_count=10,
                hidden_count=0,
                heading_count=0,
                unique_tag_count=1,
                visible_ratio=1.5,  # Invalid: > 1.0
                hidden_ratio=0.0,
                unique_tags=["p"],
                has_headings=False,
                tag_distribution={"p": 10},
                total_text_length=100,
                avg_text_length=10.0,
                min_text_length=5,
                max_text_length=20,
            )
        assert "visible_ratio" in str(exc_info.value).lower()

    def test_quality_metrics_ratio_rejects_below_zero(self):
        """QualityMetrics ratio fields reject values < 0.0."""
        from app.models import QualityMetrics

        with pytest.raises(ValidationError) as exc_info:
            QualityMetrics(
                element_count=10,
                visible_count=10,
                hidden_count=0,
                heading_count=0,
                unique_tag_count=1,
                visible_ratio=1.0,
                hidden_ratio=-0.1,  # Invalid: < 0.0
                unique_tags=["p"],
                has_headings=False,
                tag_distribution={"p": 10},
                total_text_length=100,
                avg_text_length=10.0,
                min_text_length=5,
                max_text_length=20,
            )
        assert "hidden_ratio" in str(exc_info.value).lower()

    # === Serialization ===

    def test_quality_metrics_serializes_to_dict(self):
        """QualityMetrics serializes to dictionary correctly."""
        from app.models import QualityMetrics

        metrics = QualityMetrics(
            element_count=5,
            visible_count=4,
            hidden_count=1,
            heading_count=1,
            unique_tag_count=3,
            visible_ratio=0.8,
            hidden_ratio=0.2,
            unique_tags=["h1", "p", "span"],
            has_headings=True,
            tag_distribution={"h1": 1, "p": 3, "span": 1},
            total_text_length=250,
            avg_text_length=50.0,
            min_text_length=10,
            max_text_length=100,
        )
        data = metrics.model_dump()

        assert data["element_count"] == 5
        assert data["visible_ratio"] == 0.8
        assert data["unique_tags"] == ["h1", "p", "span"]
        assert data["tag_distribution"] == {"h1": 1, "p": 3, "span": 1}
        assert data["has_headings"] is True

    def test_quality_metrics_serializes_to_json(self):
        """QualityMetrics serializes to JSON string correctly."""
        import json

        from app.models import QualityMetrics

        metrics = QualityMetrics(
            element_count=5,
            visible_count=4,
            hidden_count=1,
            heading_count=1,
            unique_tag_count=3,
            visible_ratio=0.8,
            hidden_ratio=0.2,
            unique_tags=["h1", "p", "span"],
            has_headings=True,
            tag_distribution={"h1": 1, "p": 3, "span": 1},
            total_text_length=250,
            avg_text_length=50.0,
            min_text_length=10,
            max_text_length=100,
        )
        json_str = metrics.model_dump_json()
        data = json.loads(json_str)

        assert data["element_count"] == 5
        assert data["visible_ratio"] == 0.8
        assert isinstance(data["unique_tags"], list)
        assert isinstance(data["tag_distribution"], dict)

    # === Field Descriptions ===

    def test_quality_metrics_fields_have_descriptions(self):
        """QualityMetrics fields have descriptions for OpenAPI."""
        from app.models import QualityMetrics

        schema = QualityMetrics.model_json_schema()
        properties = schema.get("properties", {})

        # Check key fields have descriptions
        assert "description" in properties.get("element_count", {})
        assert "description" in properties.get("visible_ratio", {})
        assert "description" in properties.get("unique_tags", {})
        assert "description" in properties.get("tag_distribution", {})
        assert "description" in properties.get("avg_text_length", {})

    def test_quality_metrics_has_docstring(self):
        """QualityMetrics model has a docstring."""
        from app.models import QualityMetrics

        assert QualityMetrics.__doc__ is not None
        assert len(QualityMetrics.__doc__) > 10


class TestDomExtractionResultMetrics:
    """Tests for DomExtractionResult.metrics field (Sprint 5.0 Story 01)."""

    def test_dom_extraction_result_has_metrics_field(self):
        """DomExtractionResult has metrics field."""
        from app.models import DomExtractionResult

        schema = DomExtractionResult.model_json_schema()
        properties = schema.get("properties", {})

        assert "metrics" in properties

    def test_dom_extraction_result_metrics_defaults_to_none(self):
        """DomExtractionResult.metrics defaults to None."""
        from app.models import DomExtractionResult

        result = DomExtractionResult(
            elements=[],
            viewport={"width": 1920, "height": 1080, "deviceScaleFactor": 1},
            extraction_time_ms=10.5,
            element_count=0,
        )
        assert result.metrics is None

    def test_dom_extraction_result_metrics_accepts_quality_metrics(self):
        """DomExtractionResult.metrics accepts QualityMetrics instance."""
        from app.models import DomExtractionResult, QualityMetrics

        metrics = QualityMetrics(
            element_count=5,
            visible_count=4,
            hidden_count=1,
            heading_count=1,
            unique_tag_count=3,
            visible_ratio=0.8,
            hidden_ratio=0.2,
            unique_tags=["h1", "p", "span"],
            has_headings=True,
            tag_distribution={"h1": 1, "p": 3, "span": 1},
            total_text_length=250,
            avg_text_length=50.0,
            min_text_length=10,
            max_text_length=100,
        )
        result = DomExtractionResult(
            elements=[],
            viewport={"width": 1920, "height": 1080, "deviceScaleFactor": 1},
            extraction_time_ms=10.5,
            element_count=5,
            metrics=metrics,
        )
        assert result.metrics is not None
        assert result.metrics.element_count == 5
        assert result.metrics.visible_ratio == 0.8

    def test_dom_extraction_result_metrics_serializes_to_dict(self):
        """DomExtractionResult with metrics serializes correctly."""
        from app.models import DomExtractionResult, QualityMetrics

        metrics = QualityMetrics(
            element_count=5,
            visible_count=4,
            hidden_count=1,
            heading_count=1,
            unique_tag_count=3,
            visible_ratio=0.8,
            hidden_ratio=0.2,
            unique_tags=["h1", "p", "span"],
            has_headings=True,
            tag_distribution={"h1": 1, "p": 3, "span": 1},
            total_text_length=250,
            avg_text_length=50.0,
            min_text_length=10,
            max_text_length=100,
        )
        result = DomExtractionResult(
            elements=[],
            viewport={"width": 1920, "height": 1080, "deviceScaleFactor": 1},
            extraction_time_ms=10.5,
            element_count=5,
            metrics=metrics,
        )
        data = result.model_dump()
        assert "metrics" in data
        assert data["metrics"]["element_count"] == 5
        assert data["metrics"]["visible_ratio"] == 0.8

    def test_dom_extraction_result_metrics_none_serialization(self):
        """DomExtractionResult with metrics=None serializes correctly."""
        from app.models import DomExtractionResult

        result = DomExtractionResult(
            elements=[],
            viewport={"width": 1920, "height": 1080, "deviceScaleFactor": 1},
            extraction_time_ms=10.5,
            element_count=0,
        )
        data = result.model_dump()
        # metrics should be None (not omitted) in model_dump
        assert "metrics" in data
        assert data["metrics"] is None

    def test_dom_extraction_result_metrics_field_has_description(self):
        """DomExtractionResult.metrics has description for OpenAPI."""
        from app.models import DomExtractionResult

        schema = DomExtractionResult.model_json_schema()
        properties = schema.get("properties", {})

        assert "description" in properties.get("metrics", {})


class TestVisionAIHintsModel:
    """Tests for VisionAIHints Pydantic model (Sprint 5.0 Story 02)."""

    # === Model Existence and Structure ===

    def test_vision_ai_hints_model_exists(self):
        """VisionAIHints model exists and is importable."""
        from app.models import VisionAIHints

        assert VisionAIHints is not None

    def test_vision_ai_hints_has_dimension_fields(self):
        """VisionAIHints has image dimension fields."""
        from app.models import VisionAIHints

        schema = VisionAIHints.model_json_schema()
        properties = schema.get("properties", {})

        assert "image_width" in properties
        assert "image_height" in properties
        assert "image_size_bytes" in properties

    def test_vision_ai_hints_has_compatibility_fields(self):
        """VisionAIHints has model compatibility flag fields."""
        from app.models import VisionAIHints

        schema = VisionAIHints.model_json_schema()
        properties = schema.get("properties", {})

        assert "claude_compatible" in properties
        assert "gemini_compatible" in properties
        assert "gpt4v_compatible" in properties
        assert "qwen_compatible" in properties

    def test_vision_ai_hints_has_resize_fields(self):
        """VisionAIHints has resize impact fields."""
        from app.models import VisionAIHints

        schema = VisionAIHints.model_json_schema()
        properties = schema.get("properties", {})

        assert "estimated_resize_factor" in properties
        assert "coordinate_accuracy" in properties

    def test_vision_ai_hints_has_tiling_fields(self):
        """VisionAIHints has tiling recommendation fields."""
        from app.models import VisionAIHints

        schema = VisionAIHints.model_json_schema()
        properties = schema.get("properties", {})

        assert "tiling_recommended" in properties
        assert "suggested_tile_count" in properties
        assert "suggested_tile_size" in properties
        assert "tiling_reason" in properties

    # === Model Instantiation ===

    def test_vision_ai_hints_instantiation_all_compatible(self):
        """VisionAIHints can be instantiated with all models compatible."""
        from app.models import VisionAIHints

        hints = VisionAIHints(
            image_width=1280,
            image_height=720,
            image_size_bytes=150000,
            claude_compatible=True,
            gemini_compatible=True,
            gpt4v_compatible=True,
            qwen_compatible=True,
            estimated_resize_factor=1.0,
            coordinate_accuracy=1.0,
            resize_impact_claude=0.0,
            resize_impact_gemini=0.0,
            resize_impact_gpt4v=0.0,
            resize_impact_qwen=0.0,
            tiling_recommended=False,
            suggested_tile_count=1,
            suggested_tile_size=None,
            tiling_reason=None,
        )
        assert hints.claude_compatible is True
        assert hints.gemini_compatible is True
        assert hints.gpt4v_compatible is True
        assert hints.qwen_compatible is True
        assert hints.tiling_recommended is False

    def test_vision_ai_hints_instantiation_partial_compatible(self):
        """VisionAIHints handles partial compatibility."""
        from app.models import VisionAIHints

        hints = VisionAIHints(
            image_width=1920,
            image_height=1080,
            image_size_bytes=500000,
            claude_compatible=False,  # Exceeds 1568px
            gemini_compatible=True,
            gpt4v_compatible=True,
            qwen_compatible=True,
            estimated_resize_factor=0.817,
            coordinate_accuracy=0.817,
            resize_impact_claude=18.3,  # (1920-1568)/1920 * 100
            resize_impact_gemini=0.0,
            resize_impact_gpt4v=0.0,
            resize_impact_qwen=0.0,
            tiling_recommended=False,
            suggested_tile_count=1,
            suggested_tile_size=None,
            tiling_reason=None,
        )
        assert hints.claude_compatible is False
        assert hints.gemini_compatible is True

    def test_vision_ai_hints_with_tiling_recommended(self):
        """VisionAIHints handles tiling recommendations."""
        from app.models import VisionAIHints

        hints = VisionAIHints(
            image_width=4096,
            image_height=8000,
            image_size_bytes=2000000,
            claude_compatible=False,
            gemini_compatible=False,
            gpt4v_compatible=False,
            qwen_compatible=False,
            estimated_resize_factor=0.25,
            coordinate_accuracy=0.25,
            resize_impact_claude=80.4,
            resize_impact_gemini=61.6,
            resize_impact_gpt4v=74.4,
            resize_impact_qwen=48.8,
            tiling_recommended=True,
            suggested_tile_count=6,
            suggested_tile_size={"width": 1024, "height": 1333},
            tiling_reason="Image exceeds all model limits",
        )
        assert hints.tiling_recommended is True
        assert hints.suggested_tile_count == 6
        assert hints.tiling_reason == "Image exceeds all model limits"

    # === Field Validation ===

    def test_vision_ai_hints_dimension_fields_positive(self):
        """VisionAIHints dimension fields must be positive."""
        from app.models import VisionAIHints

        with pytest.raises(ValidationError) as exc_info:
            VisionAIHints(
                image_width=-1,
                image_height=720,
                image_size_bytes=150000,
                claude_compatible=True,
                gemini_compatible=True,
                gpt4v_compatible=True,
                qwen_compatible=True,
                estimated_resize_factor=1.0,
                coordinate_accuracy=1.0,
                tiling_recommended=False,
                suggested_tile_count=1,
                suggested_tile_size=None,
                tiling_reason=None,
            )
        assert "image_width" in str(exc_info.value).lower()

    def test_vision_ai_hints_resize_factor_range(self):
        """VisionAIHints resize factor should be 0-1 range."""
        from app.models import VisionAIHints

        hints = VisionAIHints(
            image_width=1920,
            image_height=1080,
            image_size_bytes=500000,
            claude_compatible=False,
            gemini_compatible=True,
            gpt4v_compatible=True,
            qwen_compatible=True,
            estimated_resize_factor=0.5,
            coordinate_accuracy=0.5,
            resize_impact_claude=18.3,
            resize_impact_gemini=0.0,
            resize_impact_gpt4v=0.0,
            resize_impact_qwen=0.0,
            tiling_recommended=False,
            suggested_tile_count=1,
            suggested_tile_size=None,
            tiling_reason=None,
        )
        assert 0 <= hints.estimated_resize_factor <= 1
        assert 0 <= hints.coordinate_accuracy <= 1

    # === Serialization ===

    def test_vision_ai_hints_serializes_to_dict(self):
        """VisionAIHints serializes to dictionary correctly."""
        from app.models import VisionAIHints

        hints = VisionAIHints(
            image_width=1280,
            image_height=720,
            image_size_bytes=150000,
            claude_compatible=True,
            gemini_compatible=True,
            gpt4v_compatible=True,
            qwen_compatible=True,
            estimated_resize_factor=1.0,
            coordinate_accuracy=1.0,
            resize_impact_claude=0.0,
            resize_impact_gemini=0.0,
            resize_impact_gpt4v=0.0,
            resize_impact_qwen=0.0,
            tiling_recommended=False,
            suggested_tile_count=1,
            suggested_tile_size=None,
            tiling_reason=None,
        )
        data = hints.model_dump()

        assert data["image_width"] == 1280
        assert data["claude_compatible"] is True
        assert data["tiling_recommended"] is False

    # === Field Descriptions ===

    def test_vision_ai_hints_fields_have_descriptions(self):
        """VisionAIHints fields have descriptions for OpenAPI."""
        from app.models import VisionAIHints

        schema = VisionAIHints.model_json_schema()
        properties = schema.get("properties", {})

        assert "description" in properties.get("image_width", {})
        assert "description" in properties.get("claude_compatible", {})
        assert "description" in properties.get("tiling_recommended", {})

    def test_vision_ai_hints_has_docstring(self):
        """VisionAIHints model has a docstring."""
        from app.models import VisionAIHints

        assert VisionAIHints.__doc__ is not None
        assert len(VisionAIHints.__doc__) > 10


# =============================================================================
# Sprint 6.0: Tiled Screenshot Models Tests
# =============================================================================


class TestTileModel:
    """Tests for Tile Pydantic model (Sprint 6.0)."""

    def test_tile_model_exists(self):
        """Tile model exists and is importable."""
        from app.models import Tile

        assert Tile is not None

    def test_tile_creation_with_required_fields(self):
        """Tile can be created with required fields."""
        from app.models import Tile, TileBounds

        bounds = TileBounds(
            index=0, row=0, column=0, x=0, y=0, width=1200, height=800
        )
        tile = Tile(
            index=0,
            row=0,
            column=0,
            bounds=bounds,
            image_base64="dGVzdA==",
            file_size_bytes=12345,
        )
        assert tile.index == 0
        assert tile.bounds.width == 1200
        assert tile.image_base64 == "dGVzdA=="

    def test_tile_with_dom_extraction(self):
        """Tile accepts optional dom_extraction field."""
        from app.models import DomExtractionResult, Tile, TileBounds

        bounds = TileBounds(
            index=0, row=0, column=0, x=0, y=0, width=1200, height=800
        )
        dom_result = DomExtractionResult(
            elements=[],
            viewport={"width": 1200, "height": 800},
            extraction_time_ms=10.0,
            element_count=0,
        )
        tile = Tile(
            index=0,
            row=0,
            column=0,
            bounds=bounds,
            image_base64="dGVzdA==",
            file_size_bytes=12345,
            dom_extraction=dom_result,
        )
        assert tile.dom_extraction is not None
        assert tile.dom_extraction.element_count == 0

    def test_tile_dom_extraction_defaults_to_none(self):
        """Tile dom_extraction defaults to None."""
        from app.models import Tile, TileBounds

        bounds = TileBounds(
            index=0, row=0, column=0, x=0, y=0, width=1200, height=800
        )
        tile = Tile(
            index=0,
            row=0,
            column=0,
            bounds=bounds,
            image_base64="dGVzdA==",
            file_size_bytes=12345,
        )
        assert tile.dom_extraction is None

    def test_tile_serializes_to_json(self):
        """Tile serializes to JSON correctly."""
        import json

        from app.models import Tile, TileBounds

        bounds = TileBounds(
            index=1, row=1, column=0, x=0, y=750, width=1200, height=800
        )
        tile = Tile(
            index=1,
            row=1,
            column=0,
            bounds=bounds,
            image_base64="dGVzdA==",
            file_size_bytes=54321,
        )
        json_str = tile.model_dump_json()
        data = json.loads(json_str)

        assert data["index"] == 1
        assert data["bounds"]["y"] == 750
        assert data["file_size_bytes"] == 54321


class TestTileConfigModel:
    """Tests for TileConfig Pydantic model (Sprint 6.0)."""

    def test_tile_config_model_exists(self):
        """TileConfig model exists and is importable."""
        from app.models import TileConfig

        assert TileConfig is not None

    def test_tile_config_creation(self):
        """TileConfig can be created with all fields."""
        from app.models import TileConfig

        config = TileConfig(
            tile_width=1200,
            tile_height=800,
            overlap=50,
            total_tiles=4,
            grid={"columns": 1, "rows": 4},
        )
        assert config.tile_width == 1200
        assert config.tile_height == 800
        assert config.overlap == 50
        assert config.total_tiles == 4
        assert config.grid["rows"] == 4

    def test_tile_config_with_applied_preset(self):
        """TileConfig accepts optional applied_preset field."""
        from app.models import TileConfig

        config = TileConfig(
            tile_width=1568,
            tile_height=1568,
            overlap=50,
            total_tiles=3,
            grid={"columns": 1, "rows": 3},
            applied_preset="claude",
        )
        assert config.applied_preset == "claude"

    def test_tile_config_applied_preset_defaults_to_none(self):
        """TileConfig applied_preset defaults to None."""
        from app.models import TileConfig

        config = TileConfig(
            tile_width=1200,
            tile_height=800,
            overlap=50,
            total_tiles=4,
            grid={"columns": 1, "rows": 4},
        )
        assert config.applied_preset is None

    def test_tile_config_serializes_to_json(self):
        """TileConfig serializes to JSON correctly."""
        import json

        from app.models import TileConfig

        config = TileConfig(
            tile_width=1568,
            tile_height=1568,
            overlap=50,
            total_tiles=3,
            grid={"columns": 1, "rows": 3},
            applied_preset="claude",
        )
        json_str = config.model_dump_json()
        data = json.loads(json_str)

        assert data["tile_width"] == 1568
        assert data["applied_preset"] == "claude"


class TestCoordinateMappingModel:
    """Tests for CoordinateMapping Pydantic model (Sprint 6.0)."""

    def test_coordinate_mapping_model_exists(self):
        """CoordinateMapping model exists and is importable."""
        from app.models import CoordinateMapping

        assert CoordinateMapping is not None

    def test_coordinate_mapping_creation(self):
        """CoordinateMapping can be created."""
        from app.models import CoordinateMapping

        mapping = CoordinateMapping(
            type="tile_offset",
            instructions="Add tile bounds.x/y to element coordinates for full-page position",
            full_page_width=1200,
            full_page_height=5000,
        )
        assert mapping.type == "tile_offset"
        assert "full-page" in mapping.instructions
        assert mapping.full_page_width == 1200
        assert mapping.full_page_height == 5000

    def test_coordinate_mapping_type_defaults_to_tile_offset(self):
        """CoordinateMapping type defaults to 'tile_offset'."""
        from app.models import CoordinateMapping

        mapping = CoordinateMapping(
            instructions="Add tile offset",
            full_page_width=1200,
            full_page_height=5000,
        )
        assert mapping.type == "tile_offset"


class TestTiledScreenshotRequestModel:
    """Tests for TiledScreenshotRequest Pydantic model (Sprint 6.0)."""

    def test_tiled_request_model_exists(self):
        """TiledScreenshotRequest model exists and is importable."""
        from app.models import TiledScreenshotRequest

        assert TiledScreenshotRequest is not None

    def test_tiled_request_minimal(self):
        """TiledScreenshotRequest works with just URL."""
        from app.models import TiledScreenshotRequest

        request = TiledScreenshotRequest(url="https://example.com")
        assert str(request.url) == "https://example.com/"

    def test_tiled_request_default_tile_dimensions(self):
        """TiledScreenshotRequest has default tile dimensions."""
        from app.models import TiledScreenshotRequest

        request = TiledScreenshotRequest(url="https://example.com")
        # Should have reasonable defaults
        assert hasattr(request, "tile_width")
        assert hasattr(request, "tile_height")
        assert hasattr(request, "overlap")

    def test_tiled_request_custom_tile_dimensions(self):
        """TiledScreenshotRequest accepts custom tile dimensions."""
        from app.models import TiledScreenshotRequest

        request = TiledScreenshotRequest(
            url="https://example.com",
            tile_width=1000,
            tile_height=1200,
            overlap=100,
        )
        assert request.tile_width == 1000
        assert request.tile_height == 1200
        assert request.overlap == 100

    def test_tiled_request_target_vision_model(self):
        """TiledScreenshotRequest accepts target_vision_model."""
        from app.models import TiledScreenshotRequest

        request = TiledScreenshotRequest(
            url="https://example.com",
            target_vision_model="claude",
        )
        assert request.target_vision_model == "claude"

    def test_tiled_request_max_tile_count(self):
        """TiledScreenshotRequest accepts max_tile_count."""
        from app.models import TiledScreenshotRequest

        request = TiledScreenshotRequest(
            url="https://example.com",
            max_tile_count=50,
        )
        assert request.max_tile_count == 50

    def test_tiled_request_max_tile_count_default(self):
        """TiledScreenshotRequest max_tile_count defaults to 20."""
        from app.models import TiledScreenshotRequest

        request = TiledScreenshotRequest(url="https://example.com")
        assert request.max_tile_count == 20

    def test_tiled_request_with_dom_extraction(self):
        """TiledScreenshotRequest accepts extract_dom options."""
        from app.models import DomExtractionOptions, TiledScreenshotRequest

        options = DomExtractionOptions(enabled=True)
        request = TiledScreenshotRequest(
            url="https://example.com",
            extract_dom=options,
        )
        assert request.extract_dom.enabled is True

    def test_tiled_request_validation_overlap_less_than_tile(self):
        """TiledScreenshotRequest validates overlap < tile dimensions."""
        from app.models import TiledScreenshotRequest

        with pytest.raises(ValidationError):
            TiledScreenshotRequest(
                url="https://example.com",
                tile_width=800,
                tile_height=800,
                overlap=900,  # Greater than tile dimensions
            )

    def test_tiled_request_validation_max_tile_count_absolute_max(self):
        """TiledScreenshotRequest validates max_tile_count <= 1000."""
        from app.models import TiledScreenshotRequest

        with pytest.raises(ValidationError):
            TiledScreenshotRequest(
                url="https://example.com",
                max_tile_count=10001,  # Exceeds absolute max
            )


class TestTiledScreenshotResponseModel:
    """Tests for TiledScreenshotResponse Pydantic model (Sprint 6.0)."""

    def test_tiled_response_model_exists(self):
        """TiledScreenshotResponse model exists and is importable."""
        from app.models import TiledScreenshotResponse

        assert TiledScreenshotResponse is not None

    def test_tiled_response_creation(self):
        """TiledScreenshotResponse can be created with all fields."""
        from app.models import (
            CoordinateMapping,
            Tile,
            TileBounds,
            TileConfig,
            TiledScreenshotResponse,
        )

        bounds = TileBounds(
            index=0, row=0, column=0, x=0, y=0, width=1200, height=800
        )
        tile = Tile(
            index=0,
            row=0,
            column=0,
            bounds=bounds,
            image_base64="dGVzdA==",
            file_size_bytes=12345,
        )
        config = TileConfig(
            tile_width=1200,
            tile_height=800,
            overlap=50,
            total_tiles=1,
            grid={"columns": 1, "rows": 1},
        )
        mapping = CoordinateMapping(
            type="tile_offset",
            instructions="Add tile offset",
            full_page_width=1200,
            full_page_height=800,
        )
        response = TiledScreenshotResponse(
            success=True,
            url="https://example.com",
            full_page_dimensions={"width": 1200, "height": 800},
            tile_config=config,
            tiles=[tile],
            capture_time_ms=150.5,
            coordinate_mapping=mapping,
        )
        assert response.success is True
        assert len(response.tiles) == 1
        assert response.tile_config.total_tiles == 1

    def test_tiled_response_multiple_tiles(self):
        """TiledScreenshotResponse handles multiple tiles."""
        from app.models import (
            CoordinateMapping,
            Tile,
            TileBounds,
            TileConfig,
            TiledScreenshotResponse,
        )

        tiles = []
        for i in range(4):
            bounds = TileBounds(
                index=i, row=i, column=0, x=0, y=i * 750, width=1200, height=800
            )
            tile = Tile(
                index=i,
                row=i,
                column=0,
                bounds=bounds,
                image_base64="dGVzdA==",
                file_size_bytes=12345,
            )
            tiles.append(tile)

        config = TileConfig(
            tile_width=1200,
            tile_height=800,
            overlap=50,
            total_tiles=4,
            grid={"columns": 1, "rows": 4},
        )
        mapping = CoordinateMapping(
            type="tile_offset",
            instructions="Add tile offset",
            full_page_width=1200,
            full_page_height=3000,
        )
        response = TiledScreenshotResponse(
            success=True,
            url="https://example.com",
            full_page_dimensions={"width": 1200, "height": 3000},
            tile_config=config,
            tiles=tiles,
            capture_time_ms=500.0,
            coordinate_mapping=mapping,
        )
        assert len(response.tiles) == 4
        assert response.tiles[3].bounds.y == 2250

    def test_tiled_response_serializes_to_json(self):
        """TiledScreenshotResponse serializes to JSON correctly."""
        import json

        from app.models import (
            CoordinateMapping,
            Tile,
            TileBounds,
            TileConfig,
            TiledScreenshotResponse,
        )

        bounds = TileBounds(
            index=0, row=0, column=0, x=0, y=0, width=1200, height=800
        )
        tile = Tile(
            index=0,
            row=0,
            column=0,
            bounds=bounds,
            image_base64="dGVzdA==",
            file_size_bytes=12345,
        )
        config = TileConfig(
            tile_width=1200,
            tile_height=800,
            overlap=50,
            total_tiles=1,
            grid={"columns": 1, "rows": 1},
        )
        mapping = CoordinateMapping(
            type="tile_offset",
            instructions="Add tile offset",
            full_page_width=1200,
            full_page_height=800,
        )
        response = TiledScreenshotResponse(
            success=True,
            url="https://example.com",
            full_page_dimensions={"width": 1200, "height": 800},
            tile_config=config,
            tiles=[tile],
            capture_time_ms=150.5,
            coordinate_mapping=mapping,
        )
        json_str = response.model_dump_json()
        data = json.loads(json_str)

        assert data["success"] is True
        assert len(data["tiles"]) == 1
        assert data["tile_config"]["tile_width"] == 1200
        assert data["coordinate_mapping"]["type"] == "tile_offset"


class TestTileBoundsModelInModels:
    """Tests for TileBounds in app/models.py (Sprint 6.0)."""

    def test_tile_bounds_in_models_module(self):
        """TileBounds is importable from app.models."""
        from app.models import TileBounds

        assert TileBounds is not None

    def test_tile_bounds_validation_negative_x(self):
        """TileBounds rejects negative x value."""
        from app.models import TileBounds

        with pytest.raises(ValidationError):
            TileBounds(
                index=0, row=0, column=0, x=-10, y=0, width=100, height=100
            )

    def test_tile_bounds_validation_zero_width(self):
        """TileBounds rejects zero width."""
        from app.models import TileBounds

        with pytest.raises(ValidationError):
            TileBounds(
                index=0, row=0, column=0, x=0, y=0, width=0, height=100
            )

    def test_tile_bounds_validation_zero_height(self):
        """TileBounds rejects zero height."""
        from app.models import TileBounds

        with pytest.raises(ValidationError):
            TileBounds(
                index=0, row=0, column=0, x=0, y=0, width=100, height=0
            )
