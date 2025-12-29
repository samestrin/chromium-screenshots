"""Tests for DOM extraction quality assessment."""

import pytest
from app.models import BoundingRect, DomElement, ExtractionQuality, QualityWarning


def create_dom_element(
    tag_name: str = "p",
    text: str = "Sample text content",
    is_visible: bool = True,
    selector: str = "#element",
    xpath: str = "/html/body/element",
) -> DomElement:
    """Helper to create DomElement for testing."""
    return DomElement(
        selector=selector,
        xpath=xpath,
        tag_name=tag_name,
        text=text,
        rect=BoundingRect(x=0, y=0, width=100, height=50),
        computed_style={},
        is_visible=is_visible,
        z_index=0,
    )


def create_elements(count: int, tag_name: str = "p", text: str = "Sample text") -> list[DomElement]:
    """Helper to create a list of DomElement objects."""
    return [
        create_dom_element(
            tag_name=tag_name,
            text=f"{text} {i}",
            selector=f"#element-{i}",
            xpath=f"/html/body/element[{i}]",
        )
        for i in range(count)
    ]


def create_diverse_elements(count: int) -> list[DomElement]:
    """Create elements with diverse tag types including headings."""
    tags = ["h1", "h2", "p", "span", "a", "li", "button"]
    return [
        create_dom_element(
            tag_name=tags[i % len(tags)],
            text=f"Element {i} content",
            selector=f"#element-{i}",
            xpath=f"/html/body/element[{i}]",
        )
        for i in range(count)
    ]


class TestElementCountDetection:
    """Tests for element count quality detection rules."""

    def test_empty_extraction_returns_empty_quality(self):
        """Empty element list returns EMPTY quality."""
        from app.quality_assessment import assess_extraction_quality

        result = assess_extraction_quality([])
        assert result.quality == ExtractionQuality.EMPTY

    def test_empty_extraction_includes_no_elements_warning(self):
        """Empty element list includes NO_ELEMENTS warning."""
        from app.quality_assessment import assess_extraction_quality

        result = assess_extraction_quality([])
        warning_codes = [w.code for w in result.warnings]
        assert "NO_ELEMENTS" in warning_codes

    def test_sparse_extraction_returns_poor_quality(self):
        """1-4 elements returns POOR quality."""
        from app.quality_assessment import assess_extraction_quality

        elements = create_elements(3)
        result = assess_extraction_quality(elements)
        assert result.quality == ExtractionQuality.POOR

    def test_sparse_extraction_includes_low_element_count_warning(self):
        """1-4 elements includes LOW_ELEMENT_COUNT warning."""
        from app.quality_assessment import assess_extraction_quality

        elements = create_elements(3)
        result = assess_extraction_quality(elements)
        warning_codes = [w.code for w in result.warnings]
        assert "LOW_ELEMENT_COUNT" in warning_codes

    def test_moderate_extraction_baseline_low_quality(self):
        """5-20 elements returns LOW quality baseline."""
        from app.quality_assessment import assess_extraction_quality

        elements = create_elements(12)
        result = assess_extraction_quality(elements)
        assert result.quality == ExtractionQuality.LOW

    def test_moderate_extraction_no_count_warnings(self):
        """5-20 elements has no element count warnings."""
        from app.quality_assessment import assess_extraction_quality

        elements = create_elements(12)
        result = assess_extraction_quality(elements)
        warning_codes = [w.code for w in result.warnings]
        assert "NO_ELEMENTS" not in warning_codes
        assert "LOW_ELEMENT_COUNT" not in warning_codes

    def test_rich_diverse_extraction_returns_good_quality(self):
        """21+ elements with diversity returns GOOD quality."""
        from app.quality_assessment import assess_extraction_quality

        elements = create_diverse_elements(25)
        result = assess_extraction_quality(elements)
        assert result.quality == ExtractionQuality.GOOD

    def test_boundary_zero_elements_empty(self):
        """Boundary: 0 elements -> EMPTY."""
        from app.quality_assessment import assess_extraction_quality

        result = assess_extraction_quality([])
        assert result.quality == ExtractionQuality.EMPTY

    def test_boundary_one_element_poor(self):
        """Boundary: 1 element -> POOR."""
        from app.quality_assessment import assess_extraction_quality

        elements = create_elements(1)
        result = assess_extraction_quality(elements)
        assert result.quality == ExtractionQuality.POOR

    def test_boundary_four_elements_poor(self):
        """Boundary: 4 elements -> POOR."""
        from app.quality_assessment import assess_extraction_quality

        elements = create_elements(4)
        result = assess_extraction_quality(elements)
        assert result.quality == ExtractionQuality.POOR

    def test_boundary_five_elements_low(self):
        """Boundary: 5 elements -> LOW."""
        from app.quality_assessment import assess_extraction_quality

        elements = create_elements(5)
        result = assess_extraction_quality(elements)
        assert result.quality == ExtractionQuality.LOW

    def test_boundary_twenty_elements_low(self):
        """Boundary: 20 elements -> LOW."""
        from app.quality_assessment import assess_extraction_quality

        elements = create_elements(20)
        result = assess_extraction_quality(elements)
        assert result.quality == ExtractionQuality.LOW

    def test_boundary_twentyone_elements_eligible_for_good(self):
        """Boundary: 21 elements with diversity -> eligible for GOOD."""
        from app.quality_assessment import assess_extraction_quality

        elements = create_diverse_elements(21)
        result = assess_extraction_quality(elements)
        # With diversity, 21 elements can be GOOD
        assert result.quality == ExtractionQuality.GOOD

    def test_none_input_treated_as_empty(self):
        """None input treated as empty list."""
        from app.quality_assessment import assess_extraction_quality

        result = assess_extraction_quality(None)  # type: ignore
        assert result.quality == ExtractionQuality.EMPTY

    def test_warning_has_actionable_suggestion(self):
        """Warnings have actionable suggestions."""
        from app.quality_assessment import assess_extraction_quality

        result = assess_extraction_quality([])
        assert len(result.warnings) > 0
        for warning in result.warnings:
            assert len(warning.suggestion) > 0

    def test_verification_urls_constant_exists(self):
        """VERIFICATION_URLS constant is defined."""
        from app.quality_assessment import VERIFICATION_URLS

        assert VERIFICATION_URLS is not None
        assert len(VERIFICATION_URLS) > 0


class TestLargeDiversityLess:
    """Tests for large element counts without diversity."""

    def test_many_elements_without_diversity_returns_low(self):
        """50 elements all same tag -> LOW, not GOOD."""
        from app.quality_assessment import assess_extraction_quality

        # All div elements - no diversity
        elements = create_elements(50, tag_name="div")
        result = assess_extraction_quality(elements)
        assert result.quality == ExtractionQuality.LOW

    def test_many_elements_without_headings_returns_low(self):
        """Many elements without h1-h6 -> LOW, not GOOD."""
        from app.quality_assessment import assess_extraction_quality

        # Various non-heading tags
        tags = ["p", "span", "a", "li", "button"]
        elements = [
            create_dom_element(
                tag_name=tags[i % len(tags)],
                text=f"Text {i}",
                selector=f"#el-{i}",
            )
            for i in range(30)
        ]
        result = assess_extraction_quality(elements)
        # Without headings, even with diversity, should not be GOOD
        assert result.quality != ExtractionQuality.GOOD


class TestQualityAssessmentResult:
    """Tests for the structure of quality assessment results."""

    def test_result_has_quality_field(self):
        """Result has quality field with ExtractionQuality enum."""
        from app.quality_assessment import assess_extraction_quality, QualityAssessmentResult

        result = assess_extraction_quality([])
        assert hasattr(result, "quality")
        assert isinstance(result.quality, ExtractionQuality)

    def test_result_has_warnings_list(self):
        """Result has warnings field as list of QualityWarning."""
        from app.quality_assessment import assess_extraction_quality

        result = assess_extraction_quality([])
        assert hasattr(result, "warnings")
        assert isinstance(result.warnings, list)
        for w in result.warnings:
            assert isinstance(w, QualityWarning)
