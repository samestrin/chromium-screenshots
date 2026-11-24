"""Smoke test for the MCP 1.x server entry point."""

import pytest


@pytest.mark.asyncio
async def test_mcp_server_exposes_both_screenshot_tools():
    """The MCP server imports and lists its tools under the supported SDK."""
    from screenshot_mcp.server import list_tools

    tools = await list_tools()

    assert {tool.name for tool in tools} == {"screenshot", "screenshot_to_file"}
    for tool in tools:
        assert tool.inputSchema["type"] == "object"
        assert "url" in tool.inputSchema["properties"]