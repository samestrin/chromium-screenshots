"""Screenshot service using Playwright with Chromium."""

import asyncio
import json
import time
from contextlib import asynccontextmanager
from typing import Any, Optional
from urllib.parse import urlparse

from playwright.async_api import Browser, async_playwright

from .dom_extraction import get_extraction_script
from .models import (
    Cookie,
    CoordinateMapping,
    ImageFormat,
    ScreenshotRequest,
    ScreenshotType,
    Tile,
    TileConfig,
    TiledScreenshotRequest,
    TiledScreenshotResponse,
)
from .tiling import apply_vision_preset, calculate_per_tile_wait, calculate_tile_grid


def extract_domain_from_url(url: str) -> Optional[str]:
    """Extract the domain/hostname from a URL.

    Args:
        url: The URL to extract the domain from

    Returns:
        The hostname/domain, or None if the URL is invalid
    """
    try:
        parsed = urlparse(url)
        return parsed.hostname
    except Exception:
        return None


def extract_origin(url: str) -> str:
    """Extract the origin (scheme + host + port) from a URL.

    Used for storage injection - localStorage/sessionStorage are origin-scoped.
    Example: "https://example.com:8080/path" -> "https://example.com:8080"

    Args:
        url: The URL to extract the origin from

    Returns:
        The origin string (scheme://host[:port])
    """
    parsed = urlparse(url)
    # Include port only if present (netloc includes it)
    return f"{parsed.scheme}://{parsed.netloc}"


def has_storage_to_inject(request: ScreenshotRequest) -> bool:
    """Check if the request has localStorage or sessionStorage to inject.

    Args:
        request: The screenshot request

    Returns:
        True if there are storage values to inject, False otherwise
    """
    has_local = request.localStorage is not None and len(request.localStorage) > 0
    has_session = (
        request.sessionStorage is not None and len(request.sessionStorage) > 0
    )
    return has_local or has_session


def build_storage_injection_script(storage_type: str, values: dict[str, Any]) -> str:
    """Build JavaScript code to inject storage values.

    Values are JSON-stringified if they are not strings. This matches how
    frameworks like Wasp expect localStorage values to be stored.

    Args:
        storage_type: Either "localStorage" or "sessionStorage"
        values: Dictionary of key-value pairs to inject

    Returns:
        JavaScript code string to execute via page.evaluate()
    """
    lines = []
    for key, value in values.items():
        # Stringify non-string values (objects, arrays, numbers, booleans)
        if isinstance(value, str):
            serialized = value
        else:
            serialized = json.dumps(value)
        # Escape for JavaScript string literal
        escaped_key = key.replace("\\", "\\\\").replace("'", "\\'")
        escaped_value = serialized.replace("\\", "\\\\").replace("'", "\\'")
        lines.append(f"{storage_type}.setItem('{escaped_key}', '{escaped_value}');")
    return "\n".join(lines)


def prepare_cookies_for_playwright(
    cookies: Optional[list[Cookie]], url: str
) -> list[dict]:
    """Prepare cookies for Playwright's context.add_cookies() API.

    Converts Cookie model instances to Playwright-compatible dictionaries,
    inferring domain from the target URL when not specified.

    Args:
        cookies: List of Cookie objects (or None)
        url: Target URL for domain inference

    Returns:
        List of cookie dictionaries compatible with Playwright
    """
    if not cookies:
        return []

    inferred_domain = extract_domain_from_url(url)
    result = []

    for cookie in cookies:
        cookie_dict = {
            "name": cookie.name,
            "value": cookie.value,
            "domain": cookie.domain if cookie.domain else inferred_domain,
        }

        # Only include optional fields if they're set
        if cookie.path is not None:
            cookie_dict["path"] = cookie.path
        if cookie.httpOnly is not None:
            cookie_dict["httpOnly"] = cookie.httpOnly
        if cookie.secure is not None:
            cookie_dict["secure"] = cookie.secure
        if cookie.sameSite is not None:
            cookie_dict["sameSite"] = cookie.sameSite
        if cookie.expires is not None:
            cookie_dict["expires"] = cookie.expires

        result.append(cookie_dict)

    return result

# Common ad/tracking domains to block
AD_DOMAINS = [
    "doubleclick.net",
    "googlesyndication.com",
    "googleadservices.com",
    "google-analytics.com",
    "facebook.net",
    "facebook.com/tr",
    "analytics",
    "adservice",
    "ads.",
    "tracking.",
]


class ScreenshotService:
    """Service for capturing screenshots using Chromium via Playwright."""

    def __init__(self):
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize Playwright and launch Chromium browser."""
        if self._browser is not None:
            return

        async with self._lock:
            if self._browser is not None:
                return

            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-software-rasterizer",
                    "--disable-extensions",
                ],
            )

    async def shutdown(self) -> None:
        """Clean up browser and Playwright resources."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    @asynccontextmanager
    async def _get_page(self, request: ScreenshotRequest):
        """Context manager for creating and cleaning up browser pages.

        Handles two-step navigation for storage injection:
        1. If storage (localStorage/sessionStorage) is provided, first navigate
           to the origin to establish the browsing context
        2. Inject storage values via page.evaluate()
        3. Then navigate to the actual target URL
        """
        if not self._browser:
            await self.initialize()

        context = await self._browser.new_context(
            viewport={"width": request.width, "height": request.height},
            color_scheme="dark" if request.dark_mode else "light",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
        )

        # Block ads if requested
        if request.block_ads:
            await context.route(
                "**/*",
                lambda route: (
                    route.abort()
                    if any(domain in route.request.url for domain in AD_DOMAINS)
                    else route.continue_()
                ),
            )

        # Inject cookies if provided
        if request.cookies:
            playwright_cookies = prepare_cookies_for_playwright(
                request.cookies, str(request.url)
            )
            if playwright_cookies:
                await context.add_cookies(playwright_cookies)

        page = await context.new_page()

        # Two-step navigation for storage injection
        if has_storage_to_inject(request):
            # Step 1: Navigate to origin first (fast, just establish context)
            origin = extract_origin(str(request.url))
            await page.goto(origin, wait_until="domcontentloaded", timeout=30000)

            # Step 2: Inject localStorage values
            if request.localStorage:
                script = build_storage_injection_script(
                    "localStorage", request.localStorage
                )
                await page.evaluate(script)

            # Step 3: Inject sessionStorage values
            if request.sessionStorage:
                script = build_storage_injection_script(
                    "sessionStorage", request.sessionStorage
                )
                await page.evaluate(script)

        try:
            yield page
        finally:
            await context.close()

    async def capture(
        self, request: ScreenshotRequest
    ) -> tuple[bytes, float] | tuple[bytes, float, dict[str, Any]]:
        """
        Capture a screenshot based on the request parameters.

        Args:
            request: Screenshot request with URL and options

        Returns:
            Tuple of (screenshot bytes, capture time in ms) when extract_dom is
            None or disabled.
            Tuple of (screenshot bytes, capture time in ms, dom_result dict) when
            extract_dom is enabled.

        Raises:
            Exception: If screenshot capture fails
        """
        start_time = time.perf_counter()
        dom_result: Optional[dict[str, Any]] = None

        async with self._get_page(request) as page:
            # Navigate to URL
            await page.goto(
                str(request.url),
                wait_until="networkidle",
                timeout=30000,
            )

            # Wait for additional timeout if specified
            if request.wait_for_timeout > 0:
                await page.wait_for_timeout(request.wait_for_timeout)

            # Wait for specific selector if provided
            if request.wait_for_selector:
                await page.wait_for_selector(
                    request.wait_for_selector,
                    timeout=10000,
                )

            # Apply delay before capture if specified
            if request.delay > 0:
                await asyncio.sleep(request.delay / 1000)

            # Extract DOM elements if enabled (do this before screenshot
            # to ensure same page state)
            if request.extract_dom and request.extract_dom.enabled:
                extraction_script = get_extraction_script()
                options = {
                    "selectors": request.extract_dom.selectors,
                    "includeHidden": request.extract_dom.include_hidden,
                    "minTextLength": request.extract_dom.min_text_length,
                    "maxElements": request.extract_dom.max_elements,
                }
                dom_result = await page.evaluate(
                    f"""
                    {extraction_script}
                    extractDomElements({json.dumps(options)});
                    """
                )

            # Prepare screenshot options
            screenshot_options = {
                "type": request.format.value,
                "full_page": request.screenshot_type == ScreenshotType.FULL_PAGE,
            }

            # Quality only applies to JPEG
            if request.format == ImageFormat.JPEG:
                screenshot_options["quality"] = request.quality

            # Capture screenshot
            screenshot_bytes = await page.screenshot(**screenshot_options)

        capture_time = (time.perf_counter() - start_time) * 1000

        # Return with or without DOM result based on extraction status
        if dom_result is not None:
            return screenshot_bytes, capture_time, dom_result
        return screenshot_bytes, capture_time

    async def capture_tiled(
        self, request: TiledScreenshotRequest
    ) -> TiledScreenshotResponse:
        """
        Capture a full-page screenshot as a grid of viewport-sized tiles.

        Optimized for Vision AI processing - each tile is sized to fit within
        model input limits while maintaining coordinate accuracy.

        Args:
            request: Tiled screenshot request with URL and tile options

        Returns:
            TiledScreenshotResponse with tiles, config, and coordinate mapping

        Raises:
            Exception: If screenshot capture fails
        """
        import base64

        start_time = time.perf_counter()

        if not self._browser:
            await self.initialize()

        # Apply Vision AI preset if specified
        effective_tile_width = request.tile_width
        effective_tile_height = request.tile_height
        effective_overlap = request.overlap
        applied_preset = None

        if request.target_vision_model:
            preset_config = apply_vision_preset(
                request.target_vision_model,
                tile_width=request.tile_width if request.tile_width != 1568 else None,
                tile_height=request.tile_height if request.tile_height != 1568 else None,
                overlap=request.overlap if request.overlap != 50 else None,
            )
            effective_tile_width = preset_config["tile_width"]
            effective_tile_height = preset_config["tile_height"]
            effective_overlap = preset_config["overlap"]
            applied_preset = request.target_vision_model.lower()

        # Create context with tile dimensions as viewport
        context = await self._browser.new_context(
            viewport={"width": effective_tile_width, "height": effective_tile_height},
            color_scheme="dark" if request.dark_mode else "light",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
        )

        try:
            # Block ads if requested
            if request.block_ads:
                await context.route(
                    "**/*",
                    lambda route: (
                        route.abort()
                        if any(domain in route.request.url for domain in AD_DOMAINS)
                        else route.continue_()
                    ),
                )

            # Inject cookies if provided
            if request.cookies:
                playwright_cookies = prepare_cookies_for_playwright(
                    request.cookies, str(request.url)
                )
                if playwright_cookies:
                    await context.add_cookies(playwright_cookies)

            page = await context.new_page()

            # Handle storage injection if needed
            if request.localStorage or request.sessionStorage:
                origin = extract_origin(str(request.url))
                await page.goto(origin, wait_until="domcontentloaded", timeout=30000)

                if request.localStorage:
                    script = build_storage_injection_script(
                        "localStorage", request.localStorage
                    )
                    await page.evaluate(script)

                if request.sessionStorage:
                    script = build_storage_injection_script(
                        "sessionStorage", request.sessionStorage
                    )
                    await page.evaluate(script)

            # Navigate to target URL
            await page.goto(
                str(request.url),
                wait_until="networkidle",
                timeout=30000,
            )

            # Wait for additional timeout if specified
            if request.wait_for_timeout > 0:
                await page.wait_for_timeout(request.wait_for_timeout)

            # Wait for specific selector if provided
            if request.wait_for_selector:
                await page.wait_for_selector(
                    request.wait_for_selector,
                    timeout=10000,
                )

            # Apply delay before capture if specified
            if request.delay > 0:
                await asyncio.sleep(request.delay / 1000)

            # Get full page dimensions
            page_dimensions = await page.evaluate(
                """() => ({
                    width: Math.max(
                        document.body.scrollWidth,
                        document.documentElement.scrollWidth
                    ),
                    height: Math.max(
                        document.body.scrollHeight,
                        document.documentElement.scrollHeight
                    )
                })"""
            )

            page_width = page_dimensions["width"]
            page_height = page_dimensions["height"]

            # Calculate tile grid
            tile_bounds_list = calculate_tile_grid(
                page_height=page_height,
                viewport_height=effective_tile_height,
                overlap=effective_overlap,
                page_width=page_width,
                viewport_width=effective_tile_width,
            )

            # Validate max_tile_count limit - return HTTP 400 if exceeded
            if len(tile_bounds_list) > request.max_tile_count:
                from fastapi import HTTPException

                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Page requires {len(tile_bounds_list)} tiles but max_tile_count "
                        f"is {request.max_tile_count}. Increase max_tile_count (max 1000) "
                        f"or use larger tile dimensions."
                    ),
                )

            # Capture tiles
            tiles: list[Tile] = []
            screenshot_options = {
                "type": request.format.value,
            }
            if request.format == ImageFormat.JPEG:
                screenshot_options["quality"] = request.quality

            # Calculate per-tile wait time for lazy loading support
            per_tile_wait = calculate_per_tile_wait(
                request.wait_for_timeout, len(tile_bounds_list)
            )

            for bounds in tile_bounds_list:
                # Scroll to tile position
                await page.evaluate(f"window.scrollTo({bounds.x}, {bounds.y})")
                await page.wait_for_timeout(per_tile_wait)  # Wait for lazy loading

                # Capture screenshot with clip region
                screenshot_bytes = await page.screenshot(
                    **screenshot_options,
                    clip={
                        "x": 0,
                        "y": 0,
                        "width": bounds.width,
                        "height": bounds.height,
                    },
                )

                # Convert to base64
                image_base64 = base64.b64encode(screenshot_bytes).decode("utf-8")

                # Extract DOM if enabled
                dom_extraction = None
                if request.extract_dom and request.extract_dom.enabled:
                    extraction_script = get_extraction_script()
                    options = {
                        "selectors": request.extract_dom.selectors,
                        "includeHidden": request.extract_dom.include_hidden,
                        "minTextLength": request.extract_dom.min_text_length,
                        "maxElements": request.extract_dom.max_elements,
                    }
                    dom_extraction = await page.evaluate(
                        f"""
                        {extraction_script}
                        extractDomElements({json.dumps(options)});
                        """
                    )

                    # Enrich DOM elements with tile metadata (US-02)
                    if dom_extraction and "elements" in dom_extraction:
                        for element in dom_extraction["elements"]:
                            # Set tile_index to identify which tile contains this element
                            element["tile_index"] = bounds.index

                            # Store original tile-relative rect before adjustment
                            if "rect" in element:
                                element["tile_relative_rect"] = {
                                    "x": element["rect"]["x"],
                                    "y": element["rect"]["y"],
                                    "width": element["rect"]["width"],
                                    "height": element["rect"]["height"],
                                }
                                # Adjust rect to absolute page coordinates
                                element["rect"]["x"] += bounds.x
                                element["rect"]["y"] += bounds.y

                    # Add low element warning if fewer than 5 elements in tile
                    elem_count = dom_extraction.get("element_count", 0)
                    if elem_count < 5:
                        if "warnings" not in dom_extraction:
                            dom_extraction["warnings"] = []
                        dom_extraction["warnings"].append({
                            "code": "low_element_count_per_tile",
                            "message": (
                                f"Tile {bounds.index} has only {elem_count} elements "
                                f"(threshold: 5)"
                            ),
                            "severity": "info",
                            "suggestion": (
                                "Consider using different selectors or checking "
                                "if page content loaded correctly"
                            ),
                        })

                tile = Tile(
                    index=bounds.index,
                    row=bounds.row,
                    column=bounds.column,
                    bounds=bounds,
                    image_base64=image_base64,
                    file_size_bytes=len(screenshot_bytes),
                    dom_extraction=dom_extraction,
                )
                tiles.append(tile)

            # Calculate grid dimensions
            max_row = max(t.row for t in tiles) if tiles else 0
            max_col = max(t.column for t in tiles) if tiles else 0

            # Build tile config
            tile_config = TileConfig(
                tile_width=effective_tile_width,
                tile_height=effective_tile_height,
                overlap=effective_overlap,
                total_tiles=len(tiles),
                grid={"rows": max_row + 1, "columns": max_col + 1},
                applied_preset=applied_preset,
            )

            # Build coordinate mapping
            coordinate_mapping = CoordinateMapping(
                type="tile_offset",
                instructions=(
                    "Add tile bounds.x/y to element coordinates for full-page position"
                ),
                full_page_width=page_width,
                full_page_height=page_height,
            )

            capture_time = (time.perf_counter() - start_time) * 1000

            return TiledScreenshotResponse(
                success=True,
                url=str(request.url),
                full_page_dimensions={"width": page_width, "height": page_height},
                tile_config=tile_config,
                tiles=tiles,
                capture_time_ms=capture_time,
                coordinate_mapping=coordinate_mapping,
            )

        finally:
            await context.close()

    async def health_check(self) -> bool:
        """Check if the browser is healthy and can take screenshots."""
        try:
            if not self._browser or not self._browser.is_connected():
                return False

            # Quick test page load
            context = await self._browser.new_context()
            page = await context.new_page()
            await page.goto("about:blank")
            await context.close()
            return True
        except Exception:
            return False


# Global singleton instance
screenshot_service = ScreenshotService()
