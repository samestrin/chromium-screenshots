"""Pydantic models for screenshot requests and responses."""

from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, HttpUrl


class SameSitePolicy(str, Enum):
    """Cookie SameSite attribute values."""

    STRICT = "Strict"
    LAX = "Lax"
    NONE = "None"


class BoundingRect(BaseModel):
    """Bounding rectangle for DOM element positioning."""

    x: float = Field(..., description="X coordinate of the element's top-left corner")
    y: float = Field(..., description="Y coordinate of the element's top-left corner")
    width: float = Field(..., description="Width of the element in pixels")
    height: float = Field(..., description="Height of the element in pixels")


class DomElement(BaseModel):
    """DOM element with position, text, and style information."""

    selector: str = Field(..., description="Unique CSS selector for the element")
    xpath: str = Field(..., description="Full XPath from document root")
    tag_name: str = Field(..., description="HTML tag name (e.g., 'h1', 'p', 'div')")
    text: str = Field(..., description="Text content of the element")
    rect: BoundingRect = Field(..., description="Bounding rectangle for element position")
    computed_style: dict[str, Any] = Field(
        ..., description="Computed CSS styles (e.g., color, font-size)"
    )
    is_visible: bool = Field(..., description="Whether the element is visible")
    z_index: int = Field(..., description="Stacking order (z-index) of the element")


class DomExtractionResult(BaseModel):
    """Result of DOM element extraction."""

    elements: list[DomElement] = Field(
        ..., description="List of extracted DOM elements"
    )
    viewport: dict[str, Any] = Field(
        ..., description="Viewport dimensions (width, height, deviceScaleFactor)"
    )
    extraction_time_ms: float = Field(
        ..., description="Time taken to extract DOM elements in milliseconds"
    )
    element_count: int = Field(..., description="Total number of elements extracted")


class DomExtractionOptions(BaseModel):
    """Options for DOM element extraction."""

    enabled: bool = Field(
        default=False,
        description="Whether to extract DOM elements alongside screenshot",
    )
    selectors: list[str] = Field(
        default=[
            "h1", "h2", "h3", "h4", "h5", "h6",
            "p", "span", "a", "li", "button", "label",
            "td", "th", "caption", "figcaption", "blockquote",
        ],
        description="CSS selectors for elements to extract",
    )
    include_hidden: bool = Field(
        default=False,
        description="Include elements with visibility:hidden or display:none",
    )
    min_text_length: int = Field(
        default=1,
        description="Minimum text length to include element",
    )
    max_elements: int = Field(
        default=500,
        description="Maximum number of elements to return",
    )


class Cookie(BaseModel):
    """Cookie model for browser cookie injection.

    Compatible with Playwright's context.add_cookies() API.
    All optional fields default to None and will be omitted when
    converting to Playwright format if not specified.
    """

    name: str = Field(..., description="Cookie name (required)")
    value: str = Field(..., description="Cookie value (required)")
    domain: Optional[str] = Field(
        default=None,
        description="Cookie domain. If not specified, inferred from target URL",
    )
    path: Optional[str] = Field(
        default=None, description="Cookie path. Defaults to '/' if not specified"
    )
    httpOnly: Optional[bool] = Field(
        default=None, description="Whether the cookie is HTTP-only"
    )
    secure: Optional[bool] = Field(
        default=None, description="Whether the cookie requires HTTPS"
    )
    sameSite: Optional[Literal["Strict", "Lax", "None"]] = Field(
        default=None, description="Cookie SameSite policy: Strict, Lax, or None"
    )
    expires: Optional[int] = Field(
        default=None, description="Cookie expiration as Unix timestamp"
    )

    def __repr__(self) -> str:
        """Return string representation with masked value for security."""
        return f"Cookie(name={self.name!r}, value='***', domain={self.domain!r})"

    def __str__(self) -> str:
        """Return string with masked value for security in logs."""
        return f"Cookie(name={self.name!r}, value='***', domain={self.domain!r})"


class ScreenshotType(str, Enum):
    """Screenshot capture type."""

    VIEWPORT = "viewport"
    FULL_PAGE = "full_page"


class ImageFormat(str, Enum):
    """Output image format."""

    PNG = "png"
    JPEG = "jpeg"


class ScreenshotRequest(BaseModel):
    """Request model for screenshot capture."""

    url: HttpUrl = Field(..., description="URL to capture")
    screenshot_type: ScreenshotType = Field(
        default=ScreenshotType.VIEWPORT,
        description="Type of screenshot: viewport (visible area) or full_page (entire page)",
    )
    format: ImageFormat = Field(
        default=ImageFormat.PNG, description="Output image format"
    )
    width: int = Field(
        default=1920, ge=320, le=3840, description="Viewport width in pixels"
    )
    height: int = Field(
        default=1080, ge=240, le=2160, description="Viewport height in pixels"
    )
    quality: int = Field(
        default=90,
        ge=1,
        le=100,
        description="Image quality (1-100, only applies to JPEG)",
    )
    wait_for_timeout: int = Field(
        default=0,
        ge=0,
        le=30000,
        description="Additional wait time in ms after page load (0-30000)",
    )
    wait_for_selector: Optional[str] = Field(
        default=None, description="CSS selector to wait for before capture"
    )
    delay: int = Field(
        default=0,
        ge=0,
        le=10000,
        description="Delay in ms before taking screenshot (0-10000)",
    )
    dark_mode: bool = Field(
        default=False, description="Emulate dark color scheme preference"
    )
    block_ads: bool = Field(
        default=False, description="Block common ad domains"
    )
    cookies: Optional[list[Cookie]] = Field(
        default=None,
        description="Cookies to inject into the browser context before capture",
    )
    localStorage: Optional[dict[str, Any]] = Field(
        default=None,
        description="localStorage key-value pairs to inject before capture. "
        "Values can be strings or objects (objects will be JSON-stringified). "
        "Example: {'wasp:sessionId': 'abc123', 'theme': 'dark'}",
    )
    sessionStorage: Optional[dict[str, Any]] = Field(
        default=None,
        description="sessionStorage key-value pairs to inject before capture. "
        "Values can be strings or objects (objects will be JSON-stringified). "
        "Example: {'temp-data': 'xyz'}",
    )
    extract_dom: Optional[DomExtractionOptions] = Field(
        default=None,
        description="Options for extracting DOM element positions and text",
    )


class ScreenshotResponse(BaseModel):
    """Response model for successful screenshot."""

    success: bool = True
    url: str
    screenshot_type: ScreenshotType
    format: ImageFormat
    width: int
    height: int
    file_size_bytes: int
    capture_time_ms: float
    dom_extraction: Optional[DomExtractionResult] = Field(
        default=None,
        description="DOM extraction results, present when extract_dom was enabled",
    )


class ErrorResponse(BaseModel):
    """Response model for errors."""

    success: bool = False
    error: str
    detail: Optional[str] = None
