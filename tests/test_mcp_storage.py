"""Tests for MCP server localStorage and sessionStorage support."""

from unittest.mock import AsyncMock, patch


class TestMCPToolSchemaStorage:
    """Tests for storage parameters in MCP tool schemas."""

    async def test_screenshot_tool_has_localstorage_parameter(self):
        """Screenshot tool schema includes localStorage parameter."""
        from screenshot_mcp.server import list_tools

        tools = await list_tools()
        screenshot_tool = next(t for t in tools if t.name == "screenshot")

        assert "localStorage" in screenshot_tool.inputSchema["properties"]
        assert screenshot_tool.inputSchema["properties"]["localStorage"]["type"] == "object"

    async def test_screenshot_tool_has_sessionstorage_parameter(self):
        """Screenshot tool schema includes sessionStorage parameter."""
        from screenshot_mcp.server import list_tools

        tools = await list_tools()
        screenshot_tool = next(t for t in tools if t.name == "screenshot")

        assert "sessionStorage" in screenshot_tool.inputSchema["properties"]
        assert screenshot_tool.inputSchema["properties"]["sessionStorage"]["type"] == "object"

    async def test_screenshot_to_file_tool_has_localstorage_parameter(self):
        """Screenshot_to_file tool schema includes localStorage parameter."""
        from screenshot_mcp.server import list_tools

        tools = await list_tools()
        file_tool = next(t for t in tools if t.name == "screenshot_to_file")

        assert "localStorage" in file_tool.inputSchema["properties"]
        assert file_tool.inputSchema["properties"]["localStorage"]["type"] == "object"

    async def test_screenshot_to_file_tool_has_sessionstorage_parameter(self):
        """Screenshot_to_file tool schema includes sessionStorage parameter."""
        from screenshot_mcp.server import list_tools

        tools = await list_tools()
        file_tool = next(t for t in tools if t.name == "screenshot_to_file")

        assert "sessionStorage" in file_tool.inputSchema["properties"]
        assert file_tool.inputSchema["properties"]["sessionStorage"]["type"] == "object"

    async def test_localstorage_description_is_helpful(self):
        """localStorage parameter has helpful description for AI models."""
        from screenshot_mcp.server import list_tools

        tools = await list_tools()
        screenshot_tool = next(t for t in tools if t.name == "screenshot")

        description = screenshot_tool.inputSchema["properties"]["localStorage"]["description"]
        assert "localStorage" in description.lower() or "storage" in description.lower()

    async def test_sessionstorage_description_is_helpful(self):
        """sessionStorage parameter has helpful description for AI models."""
        from screenshot_mcp.server import list_tools

        tools = await list_tools()
        screenshot_tool = next(t for t in tools if t.name == "screenshot")

        description = screenshot_tool.inputSchema["properties"]["sessionStorage"]["description"]
        assert "sessionStorage" in description.lower() or "storage" in description.lower()


class TestMCPHandlerStorageIntegration:
    """Tests for storage parameter handling in MCP handlers."""

    async def test_screenshot_handler_passes_localstorage_to_service(self):
        """Screenshot handler passes localStorage to ScreenshotService."""
        from screenshot_mcp.server import handle_screenshot

        with patch("screenshot_mcp.server.get_screenshot_service") as mock_get_service:
            mock_service = AsyncMock()
            mock_service.capture.return_value = (b"fake_image", 100.0)
            mock_get_service.return_value = mock_service

            await handle_screenshot({
                "url": "https://example.com",
                "localStorage": {"wasp:sessionId": "abc123", "theme": "dark"},
            })

            # Verify the request was created with localStorage
            call_args = mock_service.capture.call_args
            request = call_args[0][0]
            assert request.localStorage == {"wasp:sessionId": "abc123", "theme": "dark"}

    async def test_screenshot_handler_passes_sessionstorage_to_service(self):
        """Screenshot handler passes sessionStorage to ScreenshotService."""
        from screenshot_mcp.server import handle_screenshot

        with patch("screenshot_mcp.server.get_screenshot_service") as mock_get_service:
            mock_service = AsyncMock()
            mock_service.capture.return_value = (b"fake_image", 100.0)
            mock_get_service.return_value = mock_service

            await handle_screenshot({
                "url": "https://example.com",
                "sessionStorage": {"tempData": "xyz"},
            })

            call_args = mock_service.capture.call_args
            request = call_args[0][0]
            assert request.sessionStorage == {"tempData": "xyz"}

    async def test_screenshot_handler_passes_both_storages(self):
        """Screenshot handler passes both localStorage and sessionStorage."""
        from screenshot_mcp.server import handle_screenshot

        with patch("screenshot_mcp.server.get_screenshot_service") as mock_get_service:
            mock_service = AsyncMock()
            mock_service.capture.return_value = (b"fake_image", 100.0)
            mock_get_service.return_value = mock_service

            await handle_screenshot({
                "url": "https://example.com",
                "localStorage": {"token": "abc"},
                "sessionStorage": {"session": "xyz"},
            })

            call_args = mock_service.capture.call_args
            request = call_args[0][0]
            assert request.localStorage == {"token": "abc"}
            assert request.sessionStorage == {"session": "xyz"}

    async def test_screenshot_to_file_handler_passes_storage(self):
        """Screenshot_to_file handler passes storage to ScreenshotService."""
        from screenshot_mcp.server import handle_screenshot_to_file

        with patch("screenshot_mcp.server.get_screenshot_service") as mock_get_service:
            mock_service = AsyncMock()
            mock_service.capture.return_value = (b"fake_image", 100.0)
            mock_get_service.return_value = mock_service

            with patch("pathlib.Path.write_bytes"):
                with patch("pathlib.Path.mkdir"):
                    await handle_screenshot_to_file({
                        "url": "https://example.com",
                        "output_path": "/tmp/test.png",
                        "localStorage": {"key": "value"},
                        "sessionStorage": {"temp": "data"},
                    })

            call_args = mock_service.capture.call_args
            request = call_args[0][0]
            assert request.localStorage == {"key": "value"}
            assert request.sessionStorage == {"temp": "data"}

    async def test_storage_with_nested_objects(self):
        """Storage with nested objects is passed correctly."""
        from screenshot_mcp.server import handle_screenshot

        with patch("screenshot_mcp.server.get_screenshot_service") as mock_get_service:
            mock_service = AsyncMock()
            mock_service.capture.return_value = (b"fake_image", 100.0)
            mock_get_service.return_value = mock_service

            await handle_screenshot({
                "url": "https://example.com",
                "localStorage": {
                    "user": {"id": 123, "name": "test"},
                    "settings": {"theme": "dark"},
                },
            })

            call_args = mock_service.capture.call_args
            request = call_args[0][0]
            assert request.localStorage == {
                "user": {"id": 123, "name": "test"},
                "settings": {"theme": "dark"},
            }


class TestMCPCombinedCookiesAndStorage:
    """Tests for combined cookies and storage support."""

    async def test_combined_cookies_and_localstorage(self):
        """Handler supports both cookies and localStorage in same request."""
        from screenshot_mcp.server import handle_screenshot

        with patch("screenshot_mcp.server.get_screenshot_service") as mock_get_service:
            mock_service = AsyncMock()
            mock_service.capture.return_value = (b"fake_image", 100.0)
            mock_get_service.return_value = mock_service

            await handle_screenshot({
                "url": "https://example.com",
                "cookies": [{"name": "session", "value": "cookie_val"}],
                "localStorage": {"token": "storage_val"},
            })

            call_args = mock_service.capture.call_args
            request = call_args[0][0]
            assert request.cookies is not None
            assert len(request.cookies) == 1
            assert request.cookies[0].name == "session"
            assert request.localStorage == {"token": "storage_val"}

    async def test_combined_cookies_and_both_storages(self):
        """Handler supports cookies, localStorage, and sessionStorage together."""
        from screenshot_mcp.server import handle_screenshot

        with patch("screenshot_mcp.server.get_screenshot_service") as mock_get_service:
            mock_service = AsyncMock()
            mock_service.capture.return_value = (b"fake_image", 100.0)
            mock_get_service.return_value = mock_service

            await handle_screenshot({
                "url": "https://example.com",
                "cookies": [{"name": "tracking", "value": "123"}],
                "localStorage": {"wasp:sessionId": "abc"},
                "sessionStorage": {"csrf": "token"},
            })

            call_args = mock_service.capture.call_args
            request = call_args[0][0]
            assert request.cookies is not None
            assert request.localStorage == {"wasp:sessionId": "abc"}
            assert request.sessionStorage == {"csrf": "token"}

    async def test_storage_only_no_cookies(self):
        """Handler works with storage but no cookies."""
        from screenshot_mcp.server import handle_screenshot

        with patch("screenshot_mcp.server.get_screenshot_service") as mock_get_service:
            mock_service = AsyncMock()
            mock_service.capture.return_value = (b"fake_image", 100.0)
            mock_get_service.return_value = mock_service

            await handle_screenshot({
                "url": "https://example.com",
                "localStorage": {"key": "value"},
            })

            call_args = mock_service.capture.call_args
            request = call_args[0][0]
            assert request.cookies is None
            assert request.localStorage == {"key": "value"}

    async def test_empty_storage_dicts(self):
        """Handler handles empty storage dicts correctly."""
        from screenshot_mcp.server import handle_screenshot

        with patch("screenshot_mcp.server.get_screenshot_service") as mock_get_service:
            mock_service = AsyncMock()
            mock_service.capture.return_value = (b"fake_image", 100.0)
            mock_get_service.return_value = mock_service

            await handle_screenshot({
                "url": "https://example.com",
                "localStorage": {},
                "sessionStorage": {},
            })

            call_args = mock_service.capture.call_args
            request = call_args[0][0]
            # Empty dicts should still be passed (or converted to None depending on implementation)
            assert request.localStorage == {} or request.localStorage is None
            assert request.sessionStorage == {} or request.sessionStorage is None
