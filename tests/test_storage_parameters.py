"""Tests for storage parameter parsing functions."""

import pytest
from fastapi import HTTPException


class TestParseStorageString:
    """Tests for parse_storage_string function."""

    def test_parse_storage_string_simple_key_value(self):
        """Simple key=value parsing."""
        from app.main import parse_storage_string

        result = parse_storage_string("key=value")
        assert result == {"key": "value"}

    def test_parse_storage_string_semicolon_separated(self):
        """Semicolon-separated key=value;key2=value2 parsing."""
        from app.main import parse_storage_string

        result = parse_storage_string("key=value;key2=value2")
        assert result == {"key": "value", "key2": "value2"}

    def test_parse_storage_string_special_characters_in_keys(self):
        """Keys can contain special characters like colons."""
        from app.main import parse_storage_string

        result = parse_storage_string("wasp:sessionId=abc123;color-theme=light")
        assert result == {"wasp:sessionId": "abc123", "color-theme": "light"}

    def test_parse_storage_string_empty_returns_empty_dict(self):
        """Empty string returns empty dict."""
        from app.main import parse_storage_string

        result = parse_storage_string("")
        assert result == {}

    def test_parse_storage_string_none_returns_empty_dict(self):
        """None returns empty dict."""
        from app.main import parse_storage_string

        result = parse_storage_string(None)
        assert result == {}

    def test_parse_storage_string_invalid_format_raises_error(self):
        """Invalid format (missing =) raises HTTPException."""
        from app.main import parse_storage_string

        with pytest.raises(HTTPException) as exc_info:
            parse_storage_string("invalid_no_equals")
        assert exc_info.value.status_code == 400
        assert "localStorage" in exc_info.value.detail.lower() or "storage" in exc_info.value.detail.lower()

    def test_parse_storage_string_value_with_equals(self):
        """Value can contain = signs."""
        from app.main import parse_storage_string

        result = parse_storage_string("key=val=ue=with=equals")
        assert result == {"key": "val=ue=with=equals"}

    def test_parse_storage_string_url_encoded_values(self):
        """URL-encoded values are preserved as-is."""
        from app.main import parse_storage_string

        result = parse_storage_string("key=hello%20world")
        assert result == {"key": "hello%20world"}

    def test_parse_storage_string_whitespace_handling(self):
        """Whitespace around keys and values is stripped."""
        from app.main import parse_storage_string

        result = parse_storage_string(" key = value ; key2 = value2 ")
        assert result == {"key": "value", "key2": "value2"}

    def test_parse_storage_string_empty_parts_ignored(self):
        """Empty parts (consecutive semicolons) are ignored."""
        from app.main import parse_storage_string

        result = parse_storage_string("key=value;;key2=value2")
        assert result == {"key": "value", "key2": "value2"}

    def test_parse_storage_string_json_value(self):
        """JSON string values are preserved."""
        from app.main import parse_storage_string

        # Pre-stringified JSON value
        result = parse_storage_string('prefs={"theme":"dark"}')
        assert result == {"prefs": '{"theme":"dark"}'}
