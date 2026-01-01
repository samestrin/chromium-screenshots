"""Pydantic models for screenshot requests and responses."""

from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, HttpUrl, model_validator

# Re-export TileBounds from tiling module for convenience
from app.tiling import TileBounds


class SameSitePolicy(str, Enum):
    """Cookie SameSite attribute values."""

    STRICT = "Strict"
    LAX = "Lax"
    NONE = "None"


class VisionModel(str, Enum):
    """Supported Vision AI models for optimization hints.

    Used to select model-specific thresholds for image sizing
    and tiling recommendations.
    """

    CLAUDE = "claude"
    GEMINI = "gemini"
    GPT4V = "gpt4v"
    QWEN_VL_MAX = "qwen-vl-max"


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

    # Tiling-related fields (Sprint 6.0)
    tile_index: Optional[int] = Field(
        default=None, description="Index of tile containing this element (for tiled captures)"
    )
    tile_relative_rect: Optional[BoundingRect] = Field(
        default=None,
        description="Element position relative to tile origin (for tiled captures)",
    )
    is_fixed: bool = Field(
        default=False,
        description="Whether element has position:fixed (appears in all tiles)",
    )


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
    quality: Optional["ExtractionQuality"] = Field(
        default=None,
        description="Quality assessment of the extraction (good/low/poor/empty)",
    )
    warnings: list["QualityWarning"] = Field(
        default_factory=list,
        description="Warnings about potential issues with the extraction",
    )
    metrics: Optional["QualityMetrics"] = Field(
        default=None,
        description="Detailed quality metrics, present when include_metrics=true",
    )


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
    include_metrics: bool = Field(
        default=False,
        description="Include detailed quality metrics in response",
    )
    include_vision_hints: bool = Field(
        default=False,
        description="Include Vision AI optimization hints",
    )
    target_vision_model: Optional[VisionModel] = Field(
        default=None,
        description="Target Vision AI model for hints: 'claude', 'gemini', 'gpt4v', 'qwen-vl-max'",
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


class ExtractionQuality(str, Enum):
    """Quality assessment of DOM extraction results.

    Indicates the overall quality of extracted DOM elements:
    - GOOD: 21+ elements with tag diversity (optimal for Vision AI)
    - LOW: 5-20 elements (usable but may lack context)
    - POOR: 1-4 elements (minimal extraction, limited usefulness)
    - EMPTY: 0 elements (no content extracted)
    """

    GOOD = "good"
    LOW = "low"
    POOR = "poor"
    EMPTY = "empty"


class QualityWarning(BaseModel):
    """Warning generated during DOM extraction quality assessment.

    Contains actionable information about potential issues with
    the extracted DOM elements.
    """

    code: str = Field(
        ...,
        description="Machine-readable warning code (e.g., 'low_element_count', 'no_headings')",
    )
    message: str = Field(
        ...,
        description="Human-readable description of the warning",
    )
    suggestion: str = Field(
        ...,
        description="Actionable suggestion for addressing the warning",
    )


class QualityMetrics(BaseModel):
    """Detailed quality metrics for DOM extraction results.

    Provides comprehensive statistics about extracted DOM elements,
    including element counts, visibility ratios, tag distribution,
    and text statistics. Used by Vision AI integrations to assess
    extraction quality and optimize processing.
    """

    # === Element Counts ===
    element_count: int = Field(
        ...,
        ge=0,
        description="Total number of DOM elements extracted",
    )
    visible_count: int = Field(
        ...,
        ge=0,
        description="Number of visible elements (not hidden via CSS)",
    )
    hidden_count: int = Field(
        ...,
        ge=0,
        description="Number of hidden elements (display:none or visibility:hidden)",
    )
    heading_count: int = Field(
        ...,
        ge=0,
        description="Number of heading elements (h1-h6) extracted",
    )
    unique_tag_count: int = Field(
        ...,
        ge=0,
        description="Count of unique HTML tag types in extraction",
    )

    # === Visibility Ratios ===
    visible_ratio: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Ratio of visible elements (0.0 to 1.0)",
    )
    hidden_ratio: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Ratio of hidden elements (0.0 to 1.0)",
    )

    # === Tag Analysis ===
    unique_tags: list[str] = Field(
        ...,
        description="List of unique HTML tag names found (e.g., ['h1', 'p', 'span'])",
    )
    has_headings: bool = Field(
        ...,
        description="Whether any heading elements (h1-h6) were found",
    )
    tag_distribution: dict[str, int] = Field(
        ...,
        description="Count of each tag type (e.g., {'h1': 2, 'p': 10})",
    )

    # === Text Statistics ===
    total_text_length: int = Field(
        ...,
        ge=0,
        description="Total character count of all element text content",
    )
    avg_text_length: float = Field(
        ...,
        ge=0.0,
        description="Average text length per element in characters",
    )
    min_text_length: int = Field(
        ...,
        ge=0,
        description="Minimum text length among all elements",
    )
    max_text_length: int = Field(
        ...,
        ge=0,
        description="Maximum text length among all elements",
    )


class VisionAIHints(BaseModel):
    """Vision AI optimization hints for image sizing and tiling.

    Provides model-specific compatibility information, resize impact
    estimates, and tiling recommendations to optimize Vision AI
    processing of screenshot images.
    """

    # === Image Dimensions ===
    image_width: int = Field(
        ...,
        gt=0,
        description="Image width in pixels",
    )
    image_height: int = Field(
        ...,
        gt=0,
        description="Image height in pixels",
    )
    image_size_bytes: int = Field(
        ...,
        ge=0,
        description="Image file size in bytes",
    )

    # === Document Dimensions (for full_page screenshots) ===
    document_width: Optional[int] = Field(
        default=None,
        gt=0,
        description="Full document width in pixels (for full_page screenshots)",
    )
    document_height: Optional[int] = Field(
        default=None,
        gt=0,
        description="Full document height in pixels (for full_page screenshots)",
    )

    # === Model Compatibility Flags ===
    claude_compatible: bool = Field(
        ...,
        description="Compatible with Claude Vision (max dimension <= 1568px)",
    )
    gemini_compatible: bool = Field(
        ...,
        description="Compatible with Gemini Vision (max dimension <= 3072px)",
    )
    gpt4v_compatible: bool = Field(
        ...,
        description="Compatible with GPT-4V (max dimension <= 2048px)",
    )
    qwen_compatible: bool = Field(
        ...,
        description="Compatible with Qwen-VL (max dimension <= 4096px)",
    )

    # === Resize Impact ===
    estimated_resize_factor: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Estimated resize factor for target model (1.0 = no resize needed)",
    )
    coordinate_accuracy: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Coordinate accuracy after resize (1.0 = full accuracy)",
    )

    # === Per-Model Resize Impact (percentage of detail loss) ===
    resize_impact_claude: float = Field(
        ...,
        ge=0.0,
        description="Resize impact for Claude Vision (percentage, 0.0 = no resize needed)",
    )
    resize_impact_gemini: float = Field(
        ...,
        ge=0.0,
        description="Resize impact for Gemini Vision (percentage, 0.0 = no resize needed)",
    )
    resize_impact_gpt4v: float = Field(
        ...,
        ge=0.0,
        description="Resize impact for GPT-4V (percentage, 0.0 = no resize needed)",
    )
    resize_impact_qwen: float = Field(
        ...,
        ge=0.0,
        description="Resize impact for Qwen-VL (percentage, 0.0 = no resize needed)",
    )

    # === Recommended Dimensions ===
    recommended_width: Optional[int] = Field(
        default=None,
        gt=0,
        description="Recommended width for target model (None if no resize needed)",
    )
    recommended_height: Optional[int] = Field(
        default=None,
        gt=0,
        description="Recommended height for target model (None if no resize needed)",
    )

    # === Tiling Recommendations ===
    tiling_recommended: bool = Field(
        ...,
        description="Whether image tiling is recommended for better results",
    )
    suggested_tile_count: int = Field(
        ...,
        ge=1,
        description="Suggested number of tiles if tiling is recommended",
    )
    suggested_tile_size: Optional[dict[str, int]] = Field(
        default=None,
        description="Suggested tile dimensions {'width': int, 'height': int}",
    )
    tile_overlap_percent: float = Field(
        default=15.0,
        ge=0.0,
        le=50.0,
        description="Tile overlap percentage (default 15%)",
    )
    tiling_reason: Optional[str] = Field(
        default=None,
        description="Reason for tiling recommendation",
    )


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
    image_base64: str = Field(
        ...,
        description="Base64-encoded screenshot image data",
    )
    dom_extraction: Optional[DomExtractionResult] = Field(
        default=None,
        description="DOM extraction results, present when extract_dom was enabled",
    )
    vision_hints: Optional[VisionAIHints] = Field(
        default=None,
        description="Vision AI optimization hints, present when include_vision_hints was enabled",
    )


class ErrorResponse(BaseModel):
    """Response model for errors."""

    success: bool = False
    error: str
    detail: Optional[str] = None


# =============================================================================
# Sprint 6.0: Tiled Screenshot Models
# =============================================================================


class Tile(BaseModel):
    """Individual tile from a tiled screenshot capture.

    Represents a single viewport-sized tile from a full-page screenshot,
    including its position in the grid and the captured image data.
    """

    index: int = Field(..., ge=0, description="Sequential tile index (0-based)")
    row: int = Field(..., ge=0, description="Row position in tile grid")
    column: int = Field(..., ge=0, description="Column position in tile grid")
    bounds: TileBounds = Field(..., description="Tile position and dimensions")
    image_base64: str = Field(..., description="Base64-encoded tile image data")
    file_size_bytes: int = Field(..., ge=0, description="Tile image file size in bytes")
    dom_extraction: Optional[DomExtractionResult] = Field(
        default=None,
        description="DOM extraction results for this tile, if enabled",
    )


class TileConfig(BaseModel):
    """Configuration and metadata for tile grid generation.

    Contains the tile dimensions, overlap settings, and grid structure
    used to generate the tiled screenshot.
    """

    tile_width: int = Field(..., gt=0, description="Width of each tile in pixels")
    tile_height: int = Field(..., gt=0, description="Height of each tile in pixels")
    overlap: int = Field(..., ge=0, description="Overlap between adjacent tiles in pixels")
    total_tiles: int = Field(..., ge=1, description="Total number of tiles generated")
    grid: dict[str, int] = Field(
        ...,
        description="Grid dimensions as {'columns': int, 'rows': int}",
    )
    applied_preset: Optional[str] = Field(
        default=None,
        description="Vision AI preset name if one was applied (e.g., 'claude', 'gemini')",
    )


class CoordinateMapping(BaseModel):
    """Instructions for mapping tile-relative coordinates to full-page coordinates.

    Provides guidance for Vision AI integrations on how to convert
    element coordinates from tile-relative to absolute page positions.
    """

    type: str = Field(
        default="tile_offset",
        description="Mapping type: 'tile_offset' means add tile bounds to element coords",
    )
    instructions: str = Field(
        ...,
        description="Human-readable instructions for coordinate adjustment",
    )
    full_page_width: int = Field(..., gt=0, description="Full page width in pixels")
    full_page_height: int = Field(..., gt=0, description="Full page height in pixels")


class TiledScreenshotRequest(BaseModel):
    """Request model for tiled screenshot capture.

    Captures a full-page screenshot as a grid of viewport-sized tiles,
    optimized for Vision AI processing.
    """

    url: HttpUrl = Field(..., description="URL to capture")
    tile_width: int = Field(
        default=1568,
        gt=0,
        le=4096,
        description="Width of each tile in pixels (default: 1568 for Claude)",
    )
    tile_height: int = Field(
        default=1568,
        gt=0,
        le=4096,
        description="Height of each tile in pixels (default: 1568 for Claude)",
    )
    overlap: int = Field(
        default=50,
        ge=0,
        le=500,
        description="Overlap between adjacent tiles in pixels (default: 50)",
    )
    max_tile_count: int = Field(
        default=20,
        ge=1,
        le=1000,
        description="Maximum tiles to generate (default: 20, absolute max: 1000)",
    )
    target_vision_model: Optional[str] = Field(
        default=None,
        description="Vision AI model preset: 'claude', 'gemini', 'gpt4v'",
    )
    format: ImageFormat = Field(
        default=ImageFormat.PNG,
        description="Output image format",
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
        default=None,
        description="CSS selector to wait for before capture",
    )
    delay: int = Field(
        default=0,
        ge=0,
        le=10000,
        description="Delay in ms before taking screenshot (0-10000)",
    )
    dark_mode: bool = Field(default=False, description="Emulate dark color scheme")
    block_ads: bool = Field(default=False, description="Block common ad domains")
    cookies: Optional[list[Cookie]] = Field(
        default=None,
        description="Cookies to inject into the browser context",
    )
    localStorage: Optional[dict[str, Any]] = Field(
        default=None,
        description="localStorage key-value pairs to inject",
    )
    sessionStorage: Optional[dict[str, Any]] = Field(
        default=None,
        description="sessionStorage key-value pairs to inject",
    )
    extract_dom: Optional[DomExtractionOptions] = Field(
        default=None,
        description="Options for extracting DOM elements from each tile",
    )

    @model_validator(mode="after")
    def validate_overlap_less_than_tile(self) -> "TiledScreenshotRequest":
        """Ensure overlap is less than tile dimensions."""
        if self.overlap >= self.tile_width:
            raise ValueError(
                f"overlap ({self.overlap}) must be less than tile_width ({self.tile_width})"
            )
        if self.overlap >= self.tile_height:
            raise ValueError(
                f"overlap ({self.overlap}) must be less than tile_height ({self.tile_height})"
            )
        return self


class TiledScreenshotResponse(BaseModel):
    """Response model for tiled screenshot capture.

    Contains the grid of captured tiles with their positions and
    instructions for coordinate mapping.
    """

    success: bool = Field(default=True, description="Whether capture was successful")
    url: str = Field(..., description="URL that was captured")
    full_page_dimensions: dict[str, int] = Field(
        ...,
        description="Full page dimensions as {'width': int, 'height': int}",
    )
    tile_config: TileConfig = Field(..., description="Tile configuration used")
    tiles: list[Tile] = Field(..., description="List of captured tiles")
    capture_time_ms: float = Field(
        ...,
        description="Total capture time in milliseconds",
    )
    coordinate_mapping: CoordinateMapping = Field(
        ...,
        description="Instructions for coordinate mapping",
    )
