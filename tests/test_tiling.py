"""Tests for tile grid calculation and coordinate adjustment."""

import pytest

from app.tiling import (
    calculate_tile_grid,
    TileBounds,
    VISION_AI_PRESETS,
    apply_vision_preset,
)


class TestCalculateTileGrid:
    """Tests for calculate_tile_grid function."""

    def test_calculate_tile_grid_standard(self):
        """Test standard case: 3000px page, 800px viewport, 50px overlap."""
        tiles = calculate_tile_grid(
            page_height=3000,
            viewport_height=800,
            overlap=50,
        )

        # With step = 800 - 50 = 750px
        # Tiles needed: ceil(3000 / 750) = 4 tiles
        assert len(tiles) >= 4

        # First tile starts at 0
        assert tiles[0].y == 0
        assert tiles[0].height == 800

        # Verify overlap between consecutive tiles
        for i in range(1, len(tiles)):
            prev_end = tiles[i-1].y + tiles[i-1].height
            curr_start = tiles[i].y
            assert prev_end - curr_start == 50  # overlap

    def test_calculate_tile_grid_single_tile(self):
        """Test page smaller than viewport returns single tile."""
        tiles = calculate_tile_grid(
            page_height=500,
            viewport_height=800,
            overlap=50,
        )

        assert len(tiles) == 1
        assert tiles[0].y == 0
        assert tiles[0].height == 500  # Clipped to page height

    def test_calculate_tile_grid_exact_multiple(self):
        """Test page that divides evenly into tiles."""
        tiles = calculate_tile_grid(
            page_height=1500,
            viewport_height=800,
            overlap=50,
        )

        # Step = 750px, so we need 2 tiles (0-800, 750-1500)
        assert len(tiles) == 2

        # Last tile should end exactly at page height
        last_tile = tiles[-1]
        assert last_tile.y + last_tile.height >= 1500

    def test_calculate_tile_grid_with_overlap(self):
        """Test overlap math is correct."""
        tiles = calculate_tile_grid(
            page_height=2000,
            viewport_height=1000,
            overlap=100,
        )

        # Step = 1000 - 100 = 900px
        # Tiles: 0-1000, 900-1900, 1800-2000
        assert len(tiles) >= 2

        # Check overlap regions exist
        if len(tiles) >= 2:
            tile0_end = tiles[0].y + tiles[0].height
            tile1_start = tiles[1].y
            overlap_region = tile0_end - tile1_start
            assert overlap_region == 100

    def test_calculate_tile_grid_invalid_overlap(self):
        """Test overlap >= viewport raises ValueError."""
        with pytest.raises(ValueError, match="overlap"):
            calculate_tile_grid(
                page_height=2000,
                viewport_height=800,
                overlap=800,  # Equal to viewport
            )

        with pytest.raises(ValueError, match="overlap"):
            calculate_tile_grid(
                page_height=2000,
                viewport_height=800,
                overlap=900,  # Greater than viewport
            )

    def test_calculate_tile_grid_invalid_dimensions(self):
        """Test negative values raise ValueError."""
        with pytest.raises(ValueError):
            calculate_tile_grid(
                page_height=-100,
                viewport_height=800,
                overlap=50,
            )

        with pytest.raises(ValueError):
            calculate_tile_grid(
                page_height=2000,
                viewport_height=-800,
                overlap=50,
            )

        with pytest.raises(ValueError):
            calculate_tile_grid(
                page_height=2000,
                viewport_height=800,
                overlap=-50,
            )

    def test_calculate_tile_grid_with_width(self):
        """Test horizontal tiling for wide pages."""
        tiles = calculate_tile_grid(
            page_width=2400,
            page_height=1000,
            viewport_width=1200,
            viewport_height=800,
            overlap=50,
        )

        # Should have tiles in multiple columns
        columns = set(t.column for t in tiles)
        assert len(columns) >= 2

    def test_tile_bounds_attributes(self):
        """Test TileBounds has required attributes."""
        tiles = calculate_tile_grid(
            page_height=2000,
            viewport_height=800,
            overlap=50,
        )

        tile = tiles[0]
        assert hasattr(tile, 'index')
        assert hasattr(tile, 'row')
        assert hasattr(tile, 'column')
        assert hasattr(tile, 'x')
        assert hasattr(tile, 'y')
        assert hasattr(tile, 'width')
        assert hasattr(tile, 'height')

        # First tile should be index 0, row 0, column 0
        assert tile.index == 0
        assert tile.row == 0
        assert tile.column == 0


class TestTileBoundsModel:
    """Tests for TileBounds Pydantic model."""

    def test_tile_bounds_creation(self):
        """Test creating valid TileBounds."""
        bounds = TileBounds(
            index=0,
            row=0,
            column=0,
            x=0,
            y=0,
            width=1200,
            height=800,
        )

        assert bounds.index == 0
        assert bounds.width == 1200
        assert bounds.height == 800

    def test_tile_bounds_json_serialization(self):
        """Test TileBounds serializes to JSON correctly."""
        bounds = TileBounds(
            index=1,
            row=1,
            column=0,
            x=0,
            y=750,
            width=1200,
            height=800,
        )

        json_data = bounds.model_dump()
        assert json_data['index'] == 1
        assert json_data['y'] == 750


class TestCoordinateAdjustment:
    """Tests for coordinate adjustment functions."""

    def test_adjust_coordinates_first_tile(self):
        """First tile (y=0) requires no offset adjustment."""
        from app.tiling import adjust_element_coordinates, TileBounds

        tile_bounds = TileBounds(
            index=0, row=0, column=0, x=0, y=0, width=1200, height=800
        )
        # Element at position (100, 200) within tile
        element_rect = {"x": 100, "y": 200, "width": 50, "height": 30}

        adjusted = adjust_element_coordinates(element_rect, tile_bounds)

        # For first tile, page coords = tile coords
        assert adjusted["x"] == 100
        assert adjusted["y"] == 200

    def test_adjust_coordinates_offset_tile(self):
        """Tile at y=750 requires y offset adjustment."""
        from app.tiling import adjust_element_coordinates, TileBounds

        tile_bounds = TileBounds(
            index=1, row=1, column=0, x=0, y=750, width=1200, height=800
        )
        # Element at position (100, 200) within tile
        element_rect = {"x": 100, "y": 200, "width": 50, "height": 30}

        adjusted = adjust_element_coordinates(element_rect, tile_bounds)

        # Page coords = tile coords + tile offset
        assert adjusted["x"] == 100  # No x offset for single column
        assert adjusted["y"] == 950  # 200 + 750 = 950

    def test_adjust_coordinates_horizontal_offset(self):
        """Tile with x offset adjusts horizontal position."""
        from app.tiling import adjust_element_coordinates, TileBounds

        tile_bounds = TileBounds(
            index=1, row=0, column=1, x=1150, y=0, width=1200, height=800
        )
        # Element at position (100, 200) within tile
        element_rect = {"x": 100, "y": 200, "width": 50, "height": 30}

        adjusted = adjust_element_coordinates(element_rect, tile_bounds)

        # Page coords = tile coords + tile offset
        assert adjusted["x"] == 1250  # 100 + 1150
        assert adjusted["y"] == 200

    def test_adjust_coordinates_preserves_dimensions(self):
        """Adjustment preserves width and height."""
        from app.tiling import adjust_element_coordinates, TileBounds

        tile_bounds = TileBounds(
            index=1, row=1, column=0, x=0, y=750, width=1200, height=800
        )
        element_rect = {"x": 100, "y": 200, "width": 150, "height": 80}

        adjusted = adjust_element_coordinates(element_rect, tile_bounds)

        assert adjusted["width"] == 150
        assert adjusted["height"] == 80

    def test_adjust_coordinates_batch(self):
        """Batch adjustment handles multiple elements."""
        from app.tiling import adjust_elements_batch, TileBounds

        tile_bounds = TileBounds(
            index=2, row=2, column=0, x=0, y=1500, width=1200, height=800
        )
        elements = [
            {"x": 50, "y": 100, "width": 20, "height": 10},
            {"x": 200, "y": 300, "width": 40, "height": 25},
            {"x": 100, "y": 600, "width": 100, "height": 50},
        ]

        adjusted = adjust_elements_batch(elements, tile_bounds)

        assert len(adjusted) == 3
        # First element
        assert adjusted[0]["x"] == 50
        assert adjusted[0]["y"] == 1600  # 100 + 1500
        # Second element
        assert adjusted[1]["x"] == 200
        assert adjusted[1]["y"] == 1800  # 300 + 1500
        # Third element
        assert adjusted[2]["x"] == 100
        assert adjusted[2]["y"] == 2100  # 600 + 1500

    def test_adjust_coordinates_immutable(self):
        """Adjustment does not modify original element."""
        from app.tiling import adjust_element_coordinates, TileBounds

        tile_bounds = TileBounds(
            index=1, row=1, column=0, x=0, y=750, width=1200, height=800
        )
        original_rect = {"x": 100, "y": 200, "width": 50, "height": 30}
        original_copy = original_rect.copy()

        adjust_element_coordinates(original_rect, tile_bounds)

        # Original should be unchanged
        assert original_rect == original_copy


# =============================================================================
# Sprint 6.0: Vision AI Presets Tests (Phase 3)
# =============================================================================


class TestVisionAIPresets:
    """Tests for Vision AI preset configuration.

    AC: 03-01 - Vision AI Presets Config
    """

    def test_vision_ai_presets_structure(self):
        """VISION_AI_PRESETS has correct structure with required keys."""
        assert "claude" in VISION_AI_PRESETS
        assert "gemini" in VISION_AI_PRESETS
        assert "gpt4v" in VISION_AI_PRESETS

        # Each preset should have tile_width, tile_height, overlap
        for name, preset in VISION_AI_PRESETS.items():
            assert "tile_width" in preset, f"{name} missing tile_width"
            assert "tile_height" in preset, f"{name} missing tile_height"
            assert "overlap" in preset, f"{name} missing overlap"

    def test_claude_preset_values(self):
        """Claude preset uses 1568x1568 with 50px overlap."""
        preset = VISION_AI_PRESETS["claude"]
        assert preset["tile_width"] == 1568
        assert preset["tile_height"] == 1568
        assert preset["overlap"] == 50

    def test_gemini_preset_values(self):
        """Gemini preset uses 3072x3072 with 100px overlap."""
        preset = VISION_AI_PRESETS["gemini"]
        assert preset["tile_width"] == 3072
        assert preset["tile_height"] == 3072
        assert preset["overlap"] == 100

    def test_gpt4v_preset_values(self):
        """GPT-4V preset uses 2048x2048 with 75px overlap."""
        preset = VISION_AI_PRESETS["gpt4v"]
        assert preset["tile_width"] == 2048
        assert preset["tile_height"] == 2048
        assert preset["overlap"] == 75

    def test_preset_keys_lowercase(self):
        """All preset keys are lowercase."""
        for key in VISION_AI_PRESETS.keys():
            assert key == key.lower(), f"Preset key {key} is not lowercase"


class TestApplyVisionPreset:
    """Tests for apply_vision_preset function.

    AC: 03-03 - Preset Application Logic
    """

    def test_apply_preset_claude(self):
        """apply_vision_preset('claude') returns correct values."""
        result = apply_vision_preset("claude")
        assert result["tile_width"] == 1568
        assert result["tile_height"] == 1568
        assert result["overlap"] == 50

    def test_apply_preset_gemini(self):
        """apply_vision_preset('gemini') returns correct values."""
        result = apply_vision_preset("gemini")
        assert result["tile_width"] == 3072
        assert result["tile_height"] == 3072
        assert result["overlap"] == 100

    def test_apply_preset_gpt4v(self):
        """apply_vision_preset('gpt4v') returns correct values."""
        result = apply_vision_preset("gpt4v")
        assert result["tile_width"] == 2048
        assert result["tile_height"] == 2048
        assert result["overlap"] == 75

    def test_apply_preset_case_insensitive(self):
        """Preset names are case-insensitive."""
        result_lower = apply_vision_preset("claude")
        result_upper = apply_vision_preset("CLAUDE")
        result_mixed = apply_vision_preset("Claude")

        assert result_lower == result_upper == result_mixed

    def test_apply_preset_unknown_model_raises(self):
        """Unknown preset name raises ValueError."""
        with pytest.raises(ValueError, match="Unknown Vision AI preset"):
            apply_vision_preset("unknown_model")

    def test_apply_preset_with_override_tile_width(self):
        """Custom tile_width overrides preset value."""
        result = apply_vision_preset("claude", tile_width=1200)
        assert result["tile_width"] == 1200
        assert result["tile_height"] == 1568  # Preset value
        assert result["overlap"] == 50  # Preset value

    def test_apply_preset_with_override_tile_height(self):
        """Custom tile_height overrides preset value."""
        result = apply_vision_preset("gemini", tile_height=2000)
        assert result["tile_width"] == 3072  # Preset value
        assert result["tile_height"] == 2000
        assert result["overlap"] == 100  # Preset value

    def test_apply_preset_with_override_overlap(self):
        """Custom overlap overrides preset value."""
        result = apply_vision_preset("gpt4v", overlap=25)
        assert result["tile_width"] == 2048  # Preset value
        assert result["tile_height"] == 2048  # Preset value
        assert result["overlap"] == 25

    def test_apply_preset_with_multiple_overrides(self):
        """Multiple custom values override preset values."""
        result = apply_vision_preset(
            "claude",
            tile_width=1000,
            tile_height=800,
            overlap=30
        )
        assert result["tile_width"] == 1000
        assert result["tile_height"] == 800
        assert result["overlap"] == 30

    def test_apply_preset_returns_copy(self):
        """apply_vision_preset returns a copy, not the original preset."""
        result1 = apply_vision_preset("claude")
        result2 = apply_vision_preset("claude")

        result1["tile_width"] = 999

        # Original preset and second call should be unaffected
        assert result2["tile_width"] == 1568
        assert VISION_AI_PRESETS["claude"]["tile_width"] == 1568
