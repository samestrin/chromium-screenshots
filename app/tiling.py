"""Tile grid calculation and coordinate adjustment for Vision AI processing.

This module provides functions to calculate tile grids for full-page screenshots
and adjust DOM element coordinates for tile-relative positioning.
"""

from typing import Optional

from pydantic import BaseModel, Field


class TileBounds(BaseModel):
    """Position and size of a tile within the full page.

    Represents a single tile's location in both the tile grid and the
    full page coordinate system.

    Attributes:
        index: Sequential tile index (0-based)
        row: Row position in the tile grid (0-based)
        column: Column position in the tile grid (0-based)
        x: X coordinate of tile's top-left corner in full page
        y: Y coordinate of tile's top-left corner in full page
        width: Tile width in pixels
        height: Tile height in pixels
    """

    index: int = Field(..., ge=0, description="Sequential tile index (0-based)")
    row: int = Field(..., ge=0, description="Row position in tile grid")
    column: int = Field(..., ge=0, description="Column position in tile grid")
    x: int = Field(..., ge=0, description="X coordinate in full page")
    y: int = Field(..., ge=0, description="Y coordinate in full page")
    width: int = Field(..., gt=0, description="Tile width in pixels")
    height: int = Field(..., gt=0, description="Tile height in pixels")


# Vision AI model-specific tile size presets
# These dimensions are optimized to stay within each model's processing limits
# while maximizing the captured area per tile.
VISION_AI_PRESETS = {
    "claude": {
        "tile_width": 1568,
        "tile_height": 1568,
        "overlap": 50,
    },
    "gemini": {
        "tile_width": 3072,
        "tile_height": 3072,
        "overlap": 100,
    },
    "gpt4v": {
        "tile_width": 2048,
        "tile_height": 2048,
        "overlap": 75,
    },
}


def _validate_dimensions(
    page_width: int,
    page_height: int,
    viewport_width: int,
    viewport_height: int,
    overlap: int,
) -> None:
    """Validate input dimensions for tile grid calculation.

    Args:
        page_width: Full page width in pixels
        page_height: Full page height in pixels
        viewport_width: Tile/viewport width in pixels
        viewport_height: Tile/viewport height in pixels
        overlap: Overlap between adjacent tiles in pixels

    Raises:
        ValueError: If any dimension is invalid
    """
    if page_width <= 0:
        raise ValueError(f"page_width must be positive, got {page_width}")
    if page_height <= 0:
        raise ValueError(f"page_height must be positive, got {page_height}")
    if viewport_width <= 0:
        raise ValueError(f"viewport_width must be positive, got {viewport_width}")
    if viewport_height <= 0:
        raise ValueError(f"viewport_height must be positive, got {viewport_height}")
    if overlap < 0:
        raise ValueError(f"overlap must be non-negative, got {overlap}")
    if overlap >= viewport_width:
        raise ValueError(
            f"overlap ({overlap}) must be less than viewport_width ({viewport_width})"
        )
    if overlap >= viewport_height:
        raise ValueError(
            f"overlap ({overlap}) must be less than viewport_height ({viewport_height})"
        )


def calculate_tile_grid(
    page_height: int,
    viewport_height: int,
    overlap: int = 50,
    page_width: Optional[int] = None,
    viewport_width: Optional[int] = None,
) -> list[TileBounds]:
    """Calculate tile grid with overlap for full-page capture.

    Generates a grid of tiles that covers the entire page with configurable
    overlap between adjacent tiles. Overlap ensures elements at tile boundaries
    are captured in multiple tiles for proper Vision AI detection.

    Args:
        page_height: Full page height in pixels
        viewport_height: Height of each tile in pixels
        overlap: Pixel overlap between adjacent tiles (default: 50)
        page_width: Full page width (default: viewport_width, single column)
        viewport_width: Width of each tile (default: page_width, single column)

    Returns:
        List of TileBounds objects defining each tile's position

    Raises:
        ValueError: If dimensions are invalid (negative, zero, or overlap >= viewport)

    Example:
        >>> tiles = calculate_tile_grid(
        ...     page_height=3000,
        ...     viewport_height=800,
        ...     overlap=50
        ... )
        >>> len(tiles)
        4
        >>> tiles[0].y, tiles[0].height
        (0, 800)
    """
    # Default to single column if width not specified
    if viewport_width is None:
        viewport_width = 1200  # Standard desktop width
    if page_width is None:
        page_width = viewport_width  # Single column

    # Validate all dimensions
    _validate_dimensions(
        page_width, page_height, viewport_width, viewport_height, overlap
    )

    tiles: list[TileBounds] = []

    # Calculate step size (tile size minus overlap)
    step_x = viewport_width - overlap
    step_y = viewport_height - overlap

    tile_index = 0
    row = 0
    y = 0

    while y < page_height:
        col = 0
        x = 0

        while x < page_width:
            # Calculate actual tile dimensions (may be clipped at edges)
            tile_width = min(viewport_width, page_width - x)
            tile_height = min(viewport_height, page_height - y)

            tiles.append(
                TileBounds(
                    index=tile_index,
                    row=row,
                    column=col,
                    x=x,
                    y=y,
                    width=tile_width,
                    height=tile_height,
                )
            )

            tile_index += 1

            # Break if this tile reached the page edge
            if x + tile_width >= page_width:
                break

            x += step_x
            col += 1

        # Break if this row's tiles reached the page bottom
        if y + tile_height >= page_height:
            break

        y += step_y
        row += 1

    return tiles


def adjust_element_coordinates(
    element_rect: dict[str, float],
    tile_bounds: TileBounds,
) -> dict[str, float]:
    """Adjust element coordinates from tile-relative to full-page absolute.

    Converts DOM element bounding rectangle coordinates from tile-relative
    positions to absolute page positions by adding the tile's offset.

    Args:
        element_rect: Element rectangle with x, y, width, height
        tile_bounds: Tile position within the full page

    Returns:
        New dictionary with adjusted x, y coordinates (width, height unchanged)

    Example:
        >>> bounds = TileBounds(index=1, row=1, column=0, x=0, y=750, ...)
        >>> rect = {"x": 100, "y": 200, "width": 50, "height": 30}
        >>> adjusted = adjust_element_coordinates(rect, bounds)
        >>> adjusted["y"]  # 200 + 750 = 950
        950
    """
    return {
        "x": element_rect["x"] + tile_bounds.x,
        "y": element_rect["y"] + tile_bounds.y,
        "width": element_rect["width"],
        "height": element_rect["height"],
    }


def adjust_elements_batch(
    elements: list[dict[str, float]],
    tile_bounds: TileBounds,
) -> list[dict[str, float]]:
    """Adjust coordinates for a batch of elements.

    Processes multiple element rectangles, converting each from tile-relative
    to absolute page coordinates.

    Args:
        elements: List of element rectangles with x, y, width, height
        tile_bounds: Tile position within the full page

    Returns:
        List of new dictionaries with adjusted coordinates

    Example:
        >>> bounds = TileBounds(index=2, row=2, column=0, x=0, y=1500, ...)
        >>> elements = [{"x": 50, "y": 100, ...}, {"x": 200, "y": 300, ...}]
        >>> adjusted = adjust_elements_batch(elements, bounds)
        >>> [e["y"] for e in adjusted]
        [1600, 1800]
    """
    return [adjust_element_coordinates(el, tile_bounds) for el in elements]


def apply_vision_preset(
    preset_name: str,
    tile_width: Optional[int] = None,
    tile_height: Optional[int] = None,
    overlap: Optional[int] = None,
) -> dict[str, int]:
    """Apply Vision AI preset with optional overrides.

    Loads preset configuration for the specified Vision AI model and applies
    any user-specified overrides. User-specified values take precedence.

    Args:
        preset_name: Vision AI model name ('claude', 'gemini', 'gpt4v')
        tile_width: Optional override for tile width
        tile_height: Optional override for tile height
        overlap: Optional override for overlap

    Returns:
        Dictionary with tile_width, tile_height, and overlap values

    Raises:
        ValueError: If preset_name is not recognized

    Example:
        >>> config = apply_vision_preset('claude', tile_width=1000)
        >>> config['tile_width']
        1000
        >>> config['tile_height']
        1568
    """
    preset_name_lower = preset_name.lower()

    if preset_name_lower not in VISION_AI_PRESETS:
        valid_presets = ", ".join(sorted(VISION_AI_PRESETS.keys()))
        raise ValueError(
            f"Unknown Vision AI preset '{preset_name}'. "
            f"Valid options: {valid_presets}"
        )

    preset = VISION_AI_PRESETS[preset_name_lower].copy()

    # Apply user overrides (user-specified values take precedence)
    if tile_width is not None:
        preset["tile_width"] = tile_width
    if tile_height is not None:
        preset["tile_height"] = tile_height
    if overlap is not None:
        preset["overlap"] = overlap

    return preset


def calculate_per_tile_wait(
    wait_for_timeout: int,
    tile_count: int,
    min_wait: int = 50,
) -> int:
    """Calculate per-tile wait time for lazy loading support.

    Distributes the total wait_for_timeout across all tiles, ensuring
    each tile gets at least min_wait milliseconds for content to load.

    Args:
        wait_for_timeout: Total wait time in milliseconds (0 = use min_wait)
        tile_count: Number of tiles to distribute wait across
        min_wait: Minimum wait per tile in milliseconds (default: 50)

    Returns:
        Per-tile wait time in milliseconds

    Examples:
        >>> calculate_per_tile_wait(1000, 4)  # 1000ms / 4 tiles = 250ms
        250
        >>> calculate_per_tile_wait(100, 4)   # 100ms / 4 = 25ms, but min is 50
        50
        >>> calculate_per_tile_wait(0, 4)     # No timeout = use min_wait
        50
    """
    if wait_for_timeout <= 0:
        return min_wait

    calculated = wait_for_timeout // tile_count
    return max(min_wait, calculated)
