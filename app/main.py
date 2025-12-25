"""FastAPI application for Chromium screenshot service."""

import asyncio
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response

from .models import (
    Cookie,
    ErrorResponse,
    ImageFormat,
    ScreenshotRequest,
    ScreenshotResponse,
    ScreenshotType,
)
from .screenshot import screenshot_service


def parse_cookie_string(cookie_string: Optional[str]) -> list[Cookie]:
    """Parse a cookie string into a list of Cookie objects.

    Format: "name=value;name2=value2" (semicolon-separated)

    Args:
        cookie_string: Semicolon-separated cookie string, or None

    Returns:
        List of Cookie objects

    Raises:
        HTTPException: If cookie format is invalid (missing =)
    """
    if not cookie_string:
        return []

    cookies = []
    for cookie_part in cookie_string.split(";"):
        cookie_part = cookie_part.strip()
        if not cookie_part:
            continue

        if "=" not in cookie_part:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid cookie format: expected 'name=value', got '{cookie_part}'",
            )

        # Split on first = only (value may contain =)
        name, value = cookie_part.split("=", 1)
        cookies.append(Cookie(name=name.strip(), value=value.strip()))

    return cookies


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - initialize and cleanup browser."""
    await screenshot_service.initialize()
    yield
    await screenshot_service.shutdown()


app = FastAPI(
    title="Screenshot API",
    description=(
        "A fast, Chrome-based screenshot service supporting "
        "viewport and full-page captures."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration."""
    is_healthy = await screenshot_service.health_check()
    if is_healthy:
        return {"status": "healthy", "browser": "chromium"}
    raise HTTPException(status_code=503, detail="Browser not available")


@app.post(
    "/screenshot",
    response_class=Response,
    responses={
        200: {
            "content": {"image/png": {}, "image/jpeg": {}},
            "description": "Screenshot image",
        },
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Screenshot capture failed"},
    },
)
async def take_screenshot(request: ScreenshotRequest):
    """
    Capture a screenshot of a webpage.

    Returns the screenshot image directly as binary data.
    Use the `format` parameter to choose between PNG and JPEG output.
    """
    try:
        screenshot_bytes, capture_time = await screenshot_service.capture(request)

        media_type = (
            "image/png" if request.format == ImageFormat.PNG else "image/jpeg"
        )

        return Response(
            content=screenshot_bytes,
            media_type=media_type,
            headers={
                "X-Capture-Time-Ms": str(round(capture_time, 2)),
                "X-Screenshot-Type": request.screenshot_type.value,
                "Content-Disposition": (
                    f'inline; filename="screenshot.{request.format.value}"'
                ),
            },
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Screenshot capture timed out",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Screenshot capture failed: {str(e)}",
        )


@app.post("/screenshot/json", response_model=ScreenshotResponse)
async def take_screenshot_with_metadata(request: ScreenshotRequest):
    """
    Capture a screenshot and return metadata (without the image).

    Useful for validation or when you need capture statistics
    before downloading the image.
    """
    try:
        screenshot_bytes, capture_time = await screenshot_service.capture(request)

        return ScreenshotResponse(
            url=str(request.url),
            screenshot_type=request.screenshot_type,
            format=request.format,
            width=request.width,
            height=request.height,
            file_size_bytes=len(screenshot_bytes),
            capture_time_ms=round(capture_time, 2),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Screenshot capture failed: {str(e)}",
        )


@app.get(
    "/screenshot",
    response_class=Response,
    responses={
        200: {
            "content": {"image/png": {}, "image/jpeg": {}},
            "description": "Screenshot image",
        },
    },
)
async def take_screenshot_get(
    url: str = Query(..., description="URL to capture"),
    type: ScreenshotType = Query(
        default=ScreenshotType.VIEWPORT,
        description="Screenshot type: viewport or full_page",
    ),
    format: ImageFormat = Query(default=ImageFormat.PNG, description="Image format"),
    width: int = Query(default=1920, ge=320, le=3840, description="Viewport width"),
    height: int = Query(default=1080, ge=240, le=2160, description="Viewport height"),
    quality: int = Query(default=90, ge=1, le=100, description="JPEG quality"),
    wait: int = Query(
        default=0, ge=0, le=30000, description="Wait time after load (ms)"
    ),
    dark: bool = Query(default=False, description="Enable dark mode"),
    cookies: Optional[str] = Query(
        default=None,
        description="Cookies to inject: 'name=value;name2=value2' format",
    ),
):
    """
    Capture a screenshot using GET parameters.

    Simpler interface for basic screenshots - just pass the URL
    and optional parameters as query strings.

    Example: /screenshot?url=https://example.com&type=full_page
    Example with cookies: /screenshot?url=https://example.com&cookies=session=abc123
    """
    # Parse cookie string into Cookie objects
    parsed_cookies = parse_cookie_string(cookies) if cookies else None

    request = ScreenshotRequest(
        url=url,
        screenshot_type=type,
        format=format,
        width=width,
        height=height,
        quality=quality,
        wait_for_timeout=wait,
        dark_mode=dark,
        cookies=parsed_cookies,
    )

    return await take_screenshot(request)
