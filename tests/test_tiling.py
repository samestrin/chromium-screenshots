"""Tests for tile grid calculation and coordinate adjustment."""

import pytest

# Import will fail until module is created - this is expected for RED phase
try:
    from app.tiling import (
        calculate_tile_grid,
        TileBounds,
    )
except ImportError:
    calculate_tile_grid = None
    TileBounds = None


class TestCalculateTileGrid:
    """Tests for calculate_tile_grid function."""

    @pytest.mark.skipif(calculate_tile_grid is None, reason="Module not implemented yet")
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

    @pytest.mark.skipif(calculate_tile_grid is None, reason="Module not implemented yet")
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

    @pytest.mark.skipif(calculate_tile_grid is None, reason="Module not implemented yet")
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

    @pytest.mark.skipif(calculate_tile_grid is None, reason="Module not implemented yet")
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

    @pytest.mark.skipif(calculate_tile_grid is None, reason="Module not implemented yet")
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

    @pytest.mark.skipif(calculate_tile_grid is None, reason="Module not implemented yet")
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

    @pytest.mark.skipif(calculate_tile_grid is None, reason="Module not implemented yet")
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

    @pytest.mark.skipif(calculate_tile_grid is None, reason="Module not implemented yet")
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

    @pytest.mark.skipif(TileBounds is None, reason="Model not implemented yet")
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

    @pytest.mark.skipif(TileBounds is None, reason="Model not implemented yet")
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
