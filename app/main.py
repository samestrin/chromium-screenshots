"""FastAPI application for Chromium screenshot service."""

import asyncio
import base64
from contextlib import asynccontextmanager
from importlib.metadata import version as get_version
from typing import Optional

# Get version from pyproject.toml (single source of truth)
try:
    __version__ = get_version("chromium-screenshots")
except Exception:
    __version__ = "1.2.0"  # Fallback if not installed as package

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


def parse_storage_string(storage_string: Optional[str]) -> dict[str, str]:
    """Parse a storage string into a dictionary.

    Format: "key=value;key2=value2" (semicolon-separated)

    Keys can contain special characters like colons (e.g., wasp:sessionId).
    Values can contain = signs.

    Args:
        storage_string: Semicolon-separated storage string, or None

    Returns:
        Dictionary of key-value pairs

    Raises:
        HTTPException: If storage format is invalid (missing =)
    """
    if not storage_string:
        return {}

    storage = {}
    for storage_part in storage_string.split(";"):
        storage_part = storage_part.strip()
        if not storage_part:
            continue

        if "=" not in storage_part:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid storage format: expected 'key=value', got '{storage_part}'",
            )

        # Split on first = only (value may contain =)
        key, value = storage_part.split("=", 1)
        storage[key.strip()] = value.strip()

    return storage


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
    version=__version__,
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration."""
    is_healthy = await screenshot_service.health_check()
    if is_healthy:
        return {"status": "healthy", "version": __version__, "browser": "chromium"}
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
        result = await screenshot_service.capture(request)

        # Handle both return types: (bytes, time) or (bytes, time, dom_result)
        if len(result) == 3:
            screenshot_bytes, capture_time, _ = result
        else:
            screenshot_bytes, capture_time = result

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
    Capture a screenshot and return JSON with image + DOM data.

    Returns base64-encoded image alongside metadata and DOM extraction
    results. This enables Zero-Drift capture where pixels and DOM
    coordinates are from the exact same render frame.
    """
    try:
        result = await screenshot_service.capture(request)

        # Handle both return types: (bytes, time) or (bytes, time, dom_result)
        if len(result) == 3:
            screenshot_bytes, capture_time, dom_result = result
        else:
            screenshot_bytes, capture_time = result
            dom_result = None

        # Convert raw dict to DomExtractionResult if present
        dom_extraction = None
        if dom_result:
            from app.models import (
                BoundingRect,
                DomElement,
                DomExtractionResult,
                QualityMetrics,
            )
            from app.quality_assessment import assess_extraction_quality

            elements = [
                DomElement(
                    selector=el["selector"],
                    xpath=el["xpath"],
                    tag_name=el["tag_name"],
                    text=el["text"],
                    rect=BoundingRect(**el["rect"]),
                    computed_style=el["computed_style"],
                    is_visible=el["is_visible"],
                    z_index=el["z_index"],
                )
                for el in dom_result["elements"]
            ]

            # Assess extraction quality
            quality_result = assess_extraction_quality(elements)

            # Convert metrics dataclass to Pydantic model if include_metrics=True
            metrics = None
            if (
                request.extract_dom
                and request.extract_dom.include_metrics
                and quality_result.metrics
            ):
                metrics = QualityMetrics(
                    element_count=quality_result.metrics.element_count,
                    visible_count=quality_result.metrics.visible_count,
                    hidden_count=quality_result.metrics.hidden_count,
                    heading_count=quality_result.metrics.heading_count,
                    unique_tag_count=quality_result.metrics.unique_tag_count,
                    visible_ratio=quality_result.metrics.visible_ratio,
                    hidden_ratio=quality_result.metrics.hidden_ratio,
                    unique_tags=quality_result.metrics.unique_tags,
                    has_headings=quality_result.metrics.has_headings,
                    tag_distribution=quality_result.metrics.tag_distribution,
                    total_text_length=quality_result.metrics.total_text_length,
                    avg_text_length=quality_result.metrics.avg_text_length,
                    min_text_length=quality_result.metrics.min_text_length,
                    max_text_length=quality_result.metrics.max_text_length,
                )

            dom_extraction = DomExtractionResult(
                elements=elements,
                viewport=dom_result["viewport"],
                extraction_time_ms=dom_result["extraction_time_ms"],
                element_count=dom_result["element_count"],
                quality=quality_result.quality,
                warnings=quality_result.warnings,
                metrics=metrics,
            )

        # Generate vision hints if requested
        vision_hints = None
        if (
            request.extract_dom
            and request.extract_dom.include_vision_hints
        ):
            from app.quality_assessment import generate_vision_hints

            # Get target model from request if specified
            target_model = None
            if request.extract_dom.target_vision_model:
                target_model = request.extract_dom.target_vision_model.value

            vision_hints = generate_vision_hints(
                image_width=request.width,
                image_height=request.height,
                image_size_bytes=len(screenshot_bytes),
                target_model=target_model,
            )

        return ScreenshotResponse(
            url=str(request.url),
            screenshot_type=request.screenshot_type,
            format=request.format,
            width=request.width,
            height=request.height,
            file_size_bytes=len(screenshot_bytes),
            capture_time_ms=round(capture_time, 2),
            image_base64=base64.b64encode(screenshot_bytes).decode("utf-8"),
            dom_extraction=dom_extraction,
            vision_hints=vision_hints,
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
    localStorage: Optional[str] = Query(
        default=None,
        description="localStorage to inject: 'key=value;key2=value2' format",
    ),
    sessionStorage: Optional[str] = Query(
        default=None,
        description="sessionStorage to inject: 'key=value;key2=value2' format",
    ),
):
    """
    Capture a screenshot using GET parameters.

    Simpler interface for basic screenshots - just pass the URL
    and optional parameters as query strings.

    Example: /screenshot?url=https://example.com&type=full_page
    Example with cookies: /screenshot?url=https://example.com&cookies=session=abc123
    Example with localStorage: /screenshot?url=https://example.com&localStorage=wasp:sessionId=abc123
    """
    # Parse cookie string into Cookie objects
    parsed_cookies = parse_cookie_string(cookies) if cookies else None

    # Parse storage strings into dicts
    parsed_local_storage = parse_storage_string(localStorage) if localStorage else None
    parsed_session_storage = (
        parse_storage_string(sessionStorage) if sessionStorage else None
    )

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
        localStorage=parsed_local_storage,
        sessionStorage=parsed_session_storage,
    )

    return await take_screenshot(request)
