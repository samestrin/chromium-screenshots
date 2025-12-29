"""Tests for MCP server - cookie support in screenshot tools."""

import pytest


class TestMCPInputSchemaCookies:
    """Tests for MCP tool inputSchema cookies parameter."""

    @pytest.mark.asyncio
    async def test_screenshot_tool_has_cookies_in_schema(self):
        """screenshot tool inputSchema includes cookies parameter."""
        from screenshot_mcp.server import list_tools

        tools = await list_tools()

        # Find the screenshot tool
        screenshot_tool = None
        for tool in tools:
            if tool.name == "screenshot":
                screenshot_tool = tool
                break

        assert screenshot_tool is not None
        assert "cookies" in screenshot_tool.inputSchema["properties"]

    @pytest.mark.asyncio
    async def test_screenshot_to_file_tool_has_cookies_in_schema(self):
        """screenshot_to_file tool inputSchema includes cookies parameter."""
        from screenshot_mcp.server import list_tools

        tools = await list_tools()

        # Find the screenshot_to_file tool
        screenshot_to_file_tool = None
        for tool in tools:
            if tool.name == "screenshot_to_file":
                screenshot_to_file_tool = tool
                break

        assert screenshot_to_file_tool is not None
        assert "cookies" in screenshot_to_file_tool.inputSchema["properties"]

    @pytest.mark.asyncio
    async def test_cookies_schema_is_array_type(self):
        """cookies parameter schema is array type."""
        from screenshot_mcp.server import list_tools

        tools = await list_tools()
        screenshot_tool = next(t for t in tools if t.name == "screenshot")

        cookies_schema = screenshot_tool.inputSchema["properties"]["cookies"]
        assert cookies_schema["type"] == "array"

    @pytest.mark.asyncio
    async def test_cookies_schema_items_are_objects(self):
        """cookies array items are objects with cookie fields."""
        from screenshot_mcp.server import list_tools

        tools = await list_tools()
        screenshot_tool = next(t for t in tools if t.name == "screenshot")

        cookies_schema = screenshot_tool.inputSchema["properties"]["cookies"]
        assert "items" in cookies_schema
        assert cookies_schema["items"]["type"] == "object"

    @pytest.mark.asyncio
    async def test_cookies_schema_has_required_fields(self):
        """cookies items schema has name and value as required."""
        from screenshot_mcp.server import list_tools

        tools = await list_tools()
        screenshot_tool = next(t for t in tools if t.name == "screenshot")

        cookies_schema = screenshot_tool.inputSchema["properties"]["cookies"]
        item_schema = cookies_schema["items"]

        # Check that name and value are in properties
        assert "name" in item_schema["properties"]
        assert "value" in item_schema["properties"]

        # Check required fields
        assert "required" in item_schema
        assert "name" in item_schema["required"]
        assert "value" in item_schema["required"]


class TestMCPHandlersCookiePassthrough:
    """Tests for MCP handlers passing cookies to ScreenshotService."""

    @pytest.mark.asyncio
    async def test_handle_screenshot_accepts_cookies_argument(self):
        """handle_screenshot accepts cookies in arguments."""
        from unittest.mock import AsyncMock, patch

        with patch("screenshot_mcp.server.get_screenshot_service") as mock_get_service:
            mock_service = AsyncMock()
            mock_service.capture.return_value = (b"fake_image", 100.0)
            mock_get_service.return_value = mock_service

            from screenshot_mcp.server import handle_screenshot

            result = await handle_screenshot({
                "url": "https://example.com",
                "cookies": [
                    {"name": "session", "value": "abc123"},
                ],
            })

            # Should not raise an error
            assert len(result) == 1

            # Verify capture was called
            mock_service.capture.assert_called_once()

            # Check that cookies were passed in the request
            call_args = mock_service.capture.call_args
            request = call_args[0][0]
            assert request.cookies is not None
            assert len(request.cookies) == 1
            assert request.cookies[0].name == "session"
            assert request.cookies[0].value == "abc123"

    @pytest.mark.asyncio
    async def test_handle_screenshot_to_file_accepts_cookies_argument(self):
        """handle_screenshot_to_file accepts cookies in arguments."""
        import tempfile
        from pathlib import Path
        from unittest.mock import AsyncMock, patch

        with patch("screenshot_mcp.server.get_screenshot_service") as mock_get_service:
            mock_service = AsyncMock()
            mock_service.capture.return_value = (b"fake_image", 100.0)
            mock_get_service.return_value = mock_service

            from screenshot_mcp.server import handle_screenshot_to_file

            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                output_path = f.name

            try:
                result = await handle_screenshot_to_file({
                    "url": "https://example.com",
                    "output_path": output_path,
                    "cookies": [
                        {"name": "auth", "value": "token123"},
                    ],
                })

                # Should not raise an error
                assert len(result) == 1

                # Verify capture was called with cookies
                call_args = mock_service.capture.call_args
                request = call_args[0][0]
                assert request.cookies is not None
                assert request.cookies[0].name == "auth"
            finally:
                Path(output_path).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_handle_screenshot_without_cookies(self):
        """handle_screenshot works without cookies argument."""
        from unittest.mock import AsyncMock, patch

        with patch("screenshot_mcp.server.get_screenshot_service") as mock_get_service:
            mock_service = AsyncMock()
            mock_service.capture.return_value = (b"fake_image", 100.0)
            mock_get_service.return_value = mock_service

            from screenshot_mcp.server import handle_screenshot

            result = await handle_screenshot({
                "url": "https://example.com",
            })

            # Should not raise an error
            assert len(result) == 1

            # Verify cookies is None in request
            call_args = mock_service.capture.call_args
            request = call_args[0][0]
            assert request.cookies is None

    @pytest.mark.asyncio
    async def test_cookies_with_all_optional_fields(self):
        """handle_screenshot accepts cookies with all optional fields."""
        from unittest.mock import AsyncMock, patch

        with patch("screenshot_mcp.server.get_screenshot_service") as mock_get_service:
            mock_service = AsyncMock()
            mock_service.capture.return_value = (b"fake_image", 100.0)
            mock_get_service.return_value = mock_service

            from screenshot_mcp.server import handle_screenshot

            result = await handle_screenshot({
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
            })

            assert len(result) == 1

            # Verify all cookie fields were passed
            call_args = mock_service.capture.call_args
            request = call_args[0][0]
            cookie = request.cookies[0]
            assert cookie.domain == "example.com"
            assert cookie.path == "/app"
            assert cookie.httpOnly is True
            assert cookie.secure is True
            assert cookie.sameSite == "Strict"


class TestMCPQualityIntegration:
    """Tests for MCP quality assessment integration."""

    @pytest.mark.asyncio
    async def test_screenshot_handler_includes_quality_in_response(self):
        """screenshot handler includes quality in text response."""
        from unittest.mock import AsyncMock, MagicMock, patch

        from screenshot_mcp.server import handle_screenshot

        mock_service = MagicMock()
        mock_service.capture = AsyncMock(return_value=(
            b"fake_image",
            100.0,
            {
                "elements": [
                    {
                        "selector": f"#el-{i}",
                        "xpath": f"/html/body/p[{i}]",
                        "tag_name": "p",
                        "text": f"Text content {i}" * 5,
                        "rect": {"x": 0, "y": i * 20, "width": 100, "height": 20},
                        "computed_style": {},
                        "is_visible": True,
                        "z_index": 0,
                    }
                    for i in range(10)
                ],
                "viewport": {"width": 1920, "height": 1080},
                "extraction_time_ms": 25.0,
                "element_count": 10,
            },
        ))

        with patch("screenshot_mcp.server.get_screenshot_service", return_value=mock_service):
            result = await handle_screenshot({
                "url": "https://example.com",
                "extract_dom": {"enabled": True},
            })

            assert len(result) == 1
            response_text = result[0].text

            # Should include quality in text response
            assert "Quality:" in response_text
            assert "low" in response_text.lower()

    @pytest.mark.asyncio
    async def test_screenshot_handler_includes_quality_warnings(self):
        """screenshot handler includes quality warnings when present."""
        from unittest.mock import AsyncMock, MagicMock, patch

        from screenshot_mcp.server import handle_screenshot

        mock_service = MagicMock()
        mock_service.capture = AsyncMock(return_value=(
            b"fake_image",
            100.0,
            {
                "elements": [],  # Empty -> EMPTY quality with warnings
                "viewport": {"width": 1920, "height": 1080},
                "extraction_time_ms": 5.0,
                "element_count": 0,
            },
        ))

        with patch("screenshot_mcp.server.get_screenshot_service", return_value=mock_service):
            result = await handle_screenshot({
                "url": "https://example.com",
                "extract_dom": {"enabled": True},
            })

            response_text = result[0].text

            # Should include quality and warnings
            assert "Quality: empty" in response_text
            assert "NO_ELEMENTS" in response_text

    @pytest.mark.asyncio
    async def test_screenshot_handler_quality_in_json_output(self):
        """screenshot handler includes quality in JSON DOM output."""
        import json
        from unittest.mock import AsyncMock, MagicMock, patch

        from screenshot_mcp.server import handle_screenshot

        mock_service = MagicMock()
        mock_service.capture = AsyncMock(return_value=(
            b"fake_image",
            100.0,
            {
                "elements": [
                    {
                        "selector": f"#el-{i}",
                        "xpath": f"/html/body/p[{i}]",
                        "tag_name": "p",
                        "text": f"Text {i}",
                        "rect": {"x": 0, "y": i * 20, "width": 100, "height": 20},
                        "computed_style": {},
                        "is_visible": True,
                        "z_index": 0,
                    }
                    for i in range(5)  # 5 elements -> LOW quality
                ],
                "viewport": {"width": 1920, "height": 1080},
                "extraction_time_ms": 15.0,
                "element_count": 5,
            },
        ))

        with patch("screenshot_mcp.server.get_screenshot_service", return_value=mock_service):
            result = await handle_screenshot({
                "url": "https://example.com",
                "extract_dom": {"enabled": True},
            })

            response_text = result[0].text

            # Find the JSON part and parse it
            marker = "DOM Elements (JSON):\n"
            json_start = response_text.find(marker) + len(marker)
            json_str = response_text[json_start:]
            dom_data = json.loads(json_str)

            # Quality and warnings should be in JSON
            assert "quality" in dom_data
            assert dom_data["quality"] == "low"
            assert "warnings" in dom_data
            assert isinstance(dom_data["warnings"], list)

    @pytest.mark.asyncio
    async def test_screenshot_to_file_handler_includes_quality(self):
        """screenshot_to_file handler includes quality in response."""
        import os
        import tempfile
        from unittest.mock import AsyncMock, MagicMock, patch

        from screenshot_mcp.server import handle_screenshot_to_file

        mock_service = MagicMock()
        mock_service.capture = AsyncMock(return_value=(
            b"fake_image",
            100.0,
            {
                "elements": [
                    {
                        "selector": f"#el-{i}",
                        "xpath": f"/html/body/p[{i}]",
                        "tag_name": "p",
                        "text": f"Text {i}" * 10,
                        "rect": {"x": 0, "y": i * 20, "width": 100, "height": 20},
                        "computed_style": {},
                        "is_visible": True,
                        "z_index": 0,
                    }
                    for i in range(15)  # 15 elements -> LOW quality
                ],
                "viewport": {"width": 1920, "height": 1080},
                "extraction_time_ms": 20.0,
                "element_count": 15,
            },
        ))

        with patch("screenshot_mcp.server.get_screenshot_service", return_value=mock_service):
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = os.path.join(tmpdir, "test.png")

                result = await handle_screenshot_to_file({
                    "url": "https://example.com",
                    "output_path": output_path,
                    "extract_dom": {"enabled": True},
                })

                response_text = result[0].text

                # Should include quality in response
                assert "Quality:" in response_text
                assert "low" in response_text.lower()
