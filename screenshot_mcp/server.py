"""MCP server for chromium-screenshots.

Provides screenshot capture tools for AI agents via the Model Context Protocol.
"""

import asyncio
import base64
import sys
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models import Cookie, ImageFormat, ScreenshotRequest, ScreenshotType
from app.screenshot import ScreenshotService

# Create server instance
server = Server("chromium-screenshots")

# Screenshot service instance (initialized lazily)
_screenshot_service: ScreenshotService | None = None


async def get_screenshot_service() -> ScreenshotService:
    """Get or initialize the screenshot service."""
    global _screenshot_service
    if _screenshot_service is None:
        _screenshot_service = ScreenshotService()
        await _screenshot_service.initialize()
    return _screenshot_service


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available screenshot tools."""
    return [
        Tool(
            name="screenshot",
            description=(
                "Capture a screenshot of a webpage. Returns base64-encoded image data. "
                "Supports cookie injection for authenticated pages. "
                "Use this for capturing web pages, especially long/full-page screenshots."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to capture (must include protocol, e.g., https://)",
                    },
                    "screenshot_type": {
                        "type": "string",
                        "enum": ["viewport", "full_page"],
                        "default": "viewport",
                        "description": "Type: viewport (visible area) or full_page (entire page)",
                    },
                    "format": {
                        "type": "string",
                        "enum": ["png", "jpeg"],
                        "default": "png",
                        "description": "Output image format",
                    },
                    "width": {
                        "type": "integer",
                        "minimum": 320,
                        "maximum": 3840,
                        "default": 1920,
                        "description": "Viewport width in pixels",
                    },
                    "height": {
                        "type": "integer",
                        "minimum": 240,
                        "maximum": 2160,
                        "default": 1080,
                        "description": "Viewport height in pixels",
                    },
                    "quality": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 90,
                        "description": "Image quality (1-100, only applies to JPEG)",
                    },
                    "wait_for_timeout": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 30000,
                        "default": 0,
                        "description": "Additional wait time in ms after page load",
                    },
                    "wait_for_selector": {
                        "type": "string",
                        "description": "CSS selector to wait for before capture",
                    },
                    "delay": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 10000,
                        "default": 0,
                        "description": "Delay in ms before taking screenshot",
                    },
                    "dark_mode": {
                        "type": "boolean",
                        "default": False,
                        "description": "Emulate dark color scheme preference",
                    },
                    "block_ads": {
                        "type": "boolean",
                        "default": False,
                        "description": "Block common ad/tracking domains",
                    },
                    "cookies": {
                        "type": "array",
                        "description": "Cookies to inject for authenticated pages",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "Cookie name"},
                                "value": {"type": "string", "description": "Cookie value"},
                                "domain": {"type": "string", "description": "Cookie domain"},
                                "path": {"type": "string", "description": "Cookie path"},
                                "httpOnly": {"type": "boolean", "description": "HTTP-only"},
                                "secure": {"type": "boolean", "description": "Secure flag"},
                                "sameSite": {
                                    "type": "string",
                                    "enum": ["Strict", "Lax", "None"],
                                    "description": "SameSite policy",
                                },
                                "expires": {"type": "integer", "description": "Unix timestamp"},
                            },
                            "required": ["name", "value"],
                        },
                    },
                    "localStorage": {
                        "type": "object",
                        "description": (
                            "localStorage key-value pairs to inject before capture. "
                            "For localStorage-based auth (Wasp, OpenSaaS, Firebase). "
                            "Example: {'wasp:sessionId': 'abc123', 'theme': 'dark'}"
                        ),
                    },
                    "sessionStorage": {
                        "type": "object",
                        "description": (
                            "sessionStorage key-value pairs to inject before capture. "
                            "For temporary session data. "
                            "Example: {'tempToken': 'xyz789'}"
                        ),
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="screenshot_to_file",
            description=(
                "Capture a screenshot and save it to a file. Returns the file path. "
                "Supports cookie injection for authenticated pages."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to capture (must include protocol)",
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Path where the screenshot will be saved",
                    },
                    "screenshot_type": {
                        "type": "string",
                        "enum": ["viewport", "full_page"],
                        "default": "viewport",
                        "description": "Type of screenshot",
                    },
                    "format": {
                        "type": "string",
                        "enum": ["png", "jpeg"],
                        "default": "png",
                        "description": "Output image format",
                    },
                    "width": {
                        "type": "integer",
                        "minimum": 320,
                        "maximum": 3840,
                        "default": 1920,
                        "description": "Viewport width in pixels",
                    },
                    "height": {
                        "type": "integer",
                        "minimum": 240,
                        "maximum": 2160,
                        "default": 1080,
                        "description": "Viewport height in pixels",
                    },
                    "quality": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 90,
                        "description": "JPEG quality",
                    },
                    "wait_for_timeout": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 30000,
                        "default": 0,
                        "description": "Wait time after page load in ms",
                    },
                    "wait_for_selector": {
                        "type": "string",
                        "description": "CSS selector to wait for",
                    },
                    "delay": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 10000,
                        "default": 0,
                        "description": "Delay before capture in ms",
                    },
                    "dark_mode": {
                        "type": "boolean",
                        "default": False,
                        "description": "Emulate dark color scheme",
                    },
                    "block_ads": {
                        "type": "boolean",
                        "default": False,
                        "description": "Block ad domains",
                    },
                    "cookies": {
                        "type": "array",
                        "description": "Cookies to inject for authenticated pages",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "Cookie name"},
                                "value": {"type": "string", "description": "Cookie value"},
                                "domain": {"type": "string", "description": "Cookie domain"},
                                "path": {"type": "string", "description": "Cookie path"},
                                "httpOnly": {"type": "boolean", "description": "HTTP-only"},
                                "secure": {"type": "boolean", "description": "Secure flag"},
                                "sameSite": {
                                    "type": "string",
                                    "enum": ["Strict", "Lax", "None"],
                                    "description": "SameSite policy",
                                },
                                "expires": {"type": "integer", "description": "Unix timestamp"},
                            },
                            "required": ["name", "value"],
                        },
                    },
                    "localStorage": {
                        "type": "object",
                        "description": (
                            "localStorage key-value pairs to inject before capture. "
                            "For localStorage-based auth (Wasp, OpenSaaS, Firebase). "
                            "Example: {'wasp:sessionId': 'abc123', 'theme': 'dark'}"
                        ),
                    },
                    "sessionStorage": {
                        "type": "object",
                        "description": (
                            "sessionStorage key-value pairs to inject before capture. "
                            "For temporary session data. "
                            "Example: {'tempToken': 'xyz789'}"
                        ),
                    },
                },
                "required": ["url", "output_path"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    if name == "screenshot":
        return await handle_screenshot(arguments)
    elif name == "screenshot_to_file":
        return await handle_screenshot_to_file(arguments)
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


def _parse_cookies(cookie_dicts: list[dict] | None) -> list[Cookie] | None:
    """Convert cookie dictionaries to Cookie model instances."""
    if not cookie_dicts:
        return None
    return [Cookie(**cookie) for cookie in cookie_dicts]


async def handle_screenshot(arguments: dict) -> list[TextContent]:
    """Capture a screenshot and return base64-encoded image."""
    try:
        service = await get_screenshot_service()

        request = ScreenshotRequest(
            url=arguments["url"],
            screenshot_type=ScreenshotType(arguments.get("screenshot_type", "viewport")),
            format=ImageFormat(arguments.get("format", "png")),
            width=arguments.get("width", 1920),
            height=arguments.get("height", 1080),
            quality=arguments.get("quality", 90),
            wait_for_timeout=arguments.get("wait_for_timeout", 0),
            wait_for_selector=arguments.get("wait_for_selector"),
            delay=arguments.get("delay", 0),
            dark_mode=arguments.get("dark_mode", False),
            block_ads=arguments.get("block_ads", False),
            cookies=_parse_cookies(arguments.get("cookies")),
            localStorage=arguments.get("localStorage"),
            sessionStorage=arguments.get("sessionStorage"),
        )

        screenshot_bytes, capture_time = await service.capture(request)
        base64_image = base64.b64encode(screenshot_bytes).decode("utf-8")

        return [
            TextContent(
                type="text",
                text=(
                    f"Screenshot captured successfully.\n"
                    f"Format: {request.format.value}\n"
                    f"Size: {len(screenshot_bytes):,} bytes\n"
                    f"Capture time: {capture_time:.2f}ms\n"
                    f"Dimensions: {request.width}x{request.height}\n"
                    f"Type: {request.screenshot_type.value}\n\n"
                    f"Base64 image data:\n{base64_image}"
                ),
            )
        ]

    except Exception as e:
        return [TextContent(type="text", text=f"Screenshot failed: {str(e)}")]


async def handle_screenshot_to_file(arguments: dict) -> list[TextContent]:
    """Capture a screenshot and save to file."""
    try:
        service = await get_screenshot_service()

        output_path = Path(arguments["output_path"]).expanduser().resolve()

        # Determine format from file extension if not specified
        file_format = arguments.get("format")
        if not file_format:
            suffix = output_path.suffix.lower()
            if suffix in (".jpg", ".jpeg"):
                file_format = "jpeg"
            else:
                file_format = "png"

        request = ScreenshotRequest(
            url=arguments["url"],
            screenshot_type=ScreenshotType(arguments.get("screenshot_type", "viewport")),
            format=ImageFormat(file_format),
            width=arguments.get("width", 1920),
            height=arguments.get("height", 1080),
            quality=arguments.get("quality", 90),
            wait_for_timeout=arguments.get("wait_for_timeout", 0),
            wait_for_selector=arguments.get("wait_for_selector"),
            delay=arguments.get("delay", 0),
            dark_mode=arguments.get("dark_mode", False),
            block_ads=arguments.get("block_ads", False),
            cookies=_parse_cookies(arguments.get("cookies")),
            localStorage=arguments.get("localStorage"),
            sessionStorage=arguments.get("sessionStorage"),
        )

        screenshot_bytes, capture_time = await service.capture(request)

        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write screenshot to file
        output_path.write_bytes(screenshot_bytes)

        return [
            TextContent(
                type="text",
                text=(
                    f"Screenshot saved successfully.\n"
                    f"Path: {output_path}\n"
                    f"Format: {request.format.value}\n"
                    f"Size: {len(screenshot_bytes):,} bytes\n"
                    f"Capture time: {capture_time:.2f}ms\n"
                    f"Dimensions: {request.width}x{request.height}\n"
                    f"Type: {request.screenshot_type.value}"
                ),
            )
        ]

    except Exception as e:
        return [TextContent(type="text", text=f"Screenshot failed: {str(e)}")]


async def cleanup():
    """Clean up resources on shutdown."""
    global _screenshot_service
    if _screenshot_service is not None:
        await _screenshot_service.shutdown()
        _screenshot_service = None


async def run_server():
    """Run the MCP server."""
    try:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )
    finally:
        await cleanup()


def main():
    """Entry point for the MCP server."""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
