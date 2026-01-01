"""Tests for DOM extraction quality assessment."""

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


class TestTagDiversityDetection:
    """Tests for tag diversity detection rules."""

    def test_heading_detection_h1(self):
        """h1 tag is recognized as heading."""
        from app.quality_assessment import assess_extraction_quality

        elements = [create_dom_element(tag_name="h1", text="Heading") for _ in range(25)]
        result = assess_extraction_quality(elements)
        warning_codes = [w.code for w in result.warnings]
        assert "NO_HEADINGS" not in warning_codes

    def test_heading_detection_h2(self):
        """h2 tag is recognized as heading."""
        from app.quality_assessment import assess_extraction_quality

        elements = [create_dom_element(tag_name="h2", text="Heading") for _ in range(25)]
        result = assess_extraction_quality(elements)
        warning_codes = [w.code for w in result.warnings]
        assert "NO_HEADINGS" not in warning_codes

    def test_heading_detection_h3(self):
        """h3 tag is recognized as heading."""
        from app.quality_assessment import assess_extraction_quality

        elements = [create_dom_element(tag_name="h3", text="Heading") for _ in range(25)]
        result = assess_extraction_quality(elements)
        warning_codes = [w.code for w in result.warnings]
        assert "NO_HEADINGS" not in warning_codes

    def test_heading_detection_h4(self):
        """h4 tag is recognized as heading."""
        from app.quality_assessment import assess_extraction_quality

        elements = [create_dom_element(tag_name="h4", text="Heading") for _ in range(25)]
        result = assess_extraction_quality(elements)
        warning_codes = [w.code for w in result.warnings]
        assert "NO_HEADINGS" not in warning_codes

    def test_heading_detection_h5(self):
        """h5 tag is recognized as heading."""
        from app.quality_assessment import assess_extraction_quality

        elements = [create_dom_element(tag_name="h5", text="Heading") for _ in range(25)]
        result = assess_extraction_quality(elements)
        warning_codes = [w.code for w in result.warnings]
        assert "NO_HEADINGS" not in warning_codes

    def test_heading_detection_h6(self):
        """h6 tag is recognized as heading."""
        from app.quality_assessment import assess_extraction_quality

        elements = [create_dom_element(tag_name="h6", text="Heading") for _ in range(25)]
        result = assess_extraction_quality(elements)
        warning_codes = [w.code for w in result.warnings]
        assert "NO_HEADINGS" not in warning_codes

    def test_no_headings_warning(self):
        """NO_HEADINGS warning when no h1-h6 tags present."""
        from app.quality_assessment import assess_extraction_quality

        # 30 elements, no headings
        tags = ["p", "span", "a", "div", "li"]
        elements = [
            create_dom_element(tag_name=tags[i % len(tags)], text=f"Text {i}")
            for i in range(30)
        ]
        result = assess_extraction_quality(elements)
        warning_codes = [w.code for w in result.warnings]
        assert "NO_HEADINGS" in warning_codes

    def test_low_tag_diversity_warning_single_tag(self):
        """LOW_TAG_DIVERSITY warning when all elements same tag (21+ elements)."""
        from app.quality_assessment import assess_extraction_quality

        elements = [create_dom_element(tag_name="div", text=f"Div {i}") for i in range(25)]
        result = assess_extraction_quality(elements)
        warning_codes = [w.code for w in result.warnings]
        assert "LOW_TAG_DIVERSITY" in warning_codes

    def test_low_tag_diversity_warning_two_tags(self):
        """LOW_TAG_DIVERSITY warning when only 2 tag types (21+ elements)."""
        from app.quality_assessment import assess_extraction_quality

        elements = [
            create_dom_element(tag_name="div" if i % 2 == 0 else "p", text=f"Text {i}")
            for i in range(25)
        ]
        result = assess_extraction_quality(elements)
        warning_codes = [w.code for w in result.warnings]
        assert "LOW_TAG_DIVERSITY" in warning_codes

    def test_no_diversity_warning_three_tags(self):
        """No LOW_TAG_DIVERSITY warning with 3+ tag types."""
        from app.quality_assessment import assess_extraction_quality

        # 3 different tags including heading
        elements = []
        for i in range(25):
            if i % 3 == 0:
                tag = "h1"
            elif i % 3 == 1:
                tag = "p"
            else:
                tag = "div"
            elements.append(create_dom_element(tag_name=tag, text=f"Text {i}"))

        result = assess_extraction_quality(elements)
        warning_codes = [w.code for w in result.warnings]
        assert "LOW_TAG_DIVERSITY" not in warning_codes

    def test_case_insensitive_tag_matching(self):
        """Tag matching is case-insensitive."""
        from app.quality_assessment import assess_extraction_quality

        # Uppercase tags
        elements = [
            create_dom_element(tag_name="H1", text="Heading"),
            *[create_dom_element(tag_name="DIV", text=f"Div {i}") for i in range(24)],
        ]
        result = assess_extraction_quality(elements)
        warning_codes = [w.code for w in result.warnings]
        # Should recognize H1 as heading (case-insensitive)
        assert "NO_HEADINGS" not in warning_codes

    def test_diversity_boundary_one_tag(self):
        """Boundary: 1 unique tag -> LOW_TAG_DIVERSITY (if 21+ elements)."""
        from app.quality_assessment import assess_extraction_quality

        elements = [create_dom_element(tag_name="span", text=f"S {i}") for i in range(25)]
        result = assess_extraction_quality(elements)
        warning_codes = [w.code for w in result.warnings]
        assert "LOW_TAG_DIVERSITY" in warning_codes

    def test_diversity_boundary_two_tags(self):
        """Boundary: 2 unique tags -> LOW_TAG_DIVERSITY (if 21+ elements)."""
        from app.quality_assessment import assess_extraction_quality

        elements = [
            create_dom_element(tag_name="a" if i % 2 == 0 else "li", text=f"Text {i}")
            for i in range(25)
        ]
        result = assess_extraction_quality(elements)
        warning_codes = [w.code for w in result.warnings]
        assert "LOW_TAG_DIVERSITY" in warning_codes

    def test_diversity_boundary_three_tags(self):
        """Boundary: 3 unique tags -> no LOW_TAG_DIVERSITY."""
        from app.quality_assessment import assess_extraction_quality

        tags = ["h1", "p", "div"]
        elements = [
            create_dom_element(tag_name=tags[i % 3], text=f"Text {i}")
            for i in range(25)
        ]
        result = assess_extraction_quality(elements)
        warning_codes = [w.code for w in result.warnings]
        assert "LOW_TAG_DIVERSITY" not in warning_codes

    def test_heading_set_defined(self):
        """HEADING_TAGS constant is defined with h1-h6."""
        from app.quality_assessment import HEADING_TAGS

        assert HEADING_TAGS is not None
        assert "h1" in HEADING_TAGS
        assert "h2" in HEADING_TAGS
        assert "h3" in HEADING_TAGS
        assert "h4" in HEADING_TAGS
        assert "h5" in HEADING_TAGS
        assert "h6" in HEADING_TAGS
        assert len(HEADING_TAGS) == 6

    def test_mixed_headings_and_divs_good_quality(self):
        """Mixed headings and divs with 3+ diversity can be GOOD."""
        from app.quality_assessment import assess_extraction_quality

        elements = [
            create_dom_element(tag_name="h1", text="Title"),
            create_dom_element(tag_name="h2", text="Subtitle"),
            *[create_dom_element(tag_name="div", text=f"Div {i}") for i in range(23)],
        ]
        result = assess_extraction_quality(elements)
        # Has headings and 3 tag types (h1, h2, div)
        assert result.quality == ExtractionQuality.GOOD


class TestHiddenElementsDetection:
    """Tests for hidden elements detection rules."""

    def test_many_hidden_warning_over_50_percent(self):
        """MANY_HIDDEN warning when >50% elements hidden."""
        from app.quality_assessment import assess_extraction_quality

        # 60% hidden (6 hidden, 4 visible)
        elements = [
            create_dom_element(is_visible=False, text=f"Hidden {i}")
            for i in range(6)
        ] + [
            create_dom_element(is_visible=True, text=f"Visible {i}")
            for i in range(4)
        ]
        result = assess_extraction_quality(elements)
        warning_codes = [w.code for w in result.warnings]
        assert "MANY_HIDDEN" in warning_codes

    def test_no_hidden_warning_under_50_percent(self):
        """No MANY_HIDDEN warning when <=50% elements hidden."""
        from app.quality_assessment import assess_extraction_quality

        # Exactly 50% hidden (5 hidden, 5 visible)
        elements = [
            create_dom_element(is_visible=False, text=f"Hidden {i}")
            for i in range(5)
        ] + [
            create_dom_element(is_visible=True, text=f"Visible {i}")
            for i in range(5)
        ]
        result = assess_extraction_quality(elements)
        warning_codes = [w.code for w in result.warnings]
        assert "MANY_HIDDEN" not in warning_codes

    def test_hidden_boundary_exactly_50_percent(self):
        """Boundary: exactly 50% hidden -> no warning."""
        from app.quality_assessment import assess_extraction_quality

        elements = [
            create_dom_element(is_visible=False, text=f"Hidden {i}")
            for i in range(5)
        ] + [
            create_dom_element(is_visible=True, text=f"Visible {i}")
            for i in range(5)
        ]
        result = assess_extraction_quality(elements)
        warning_codes = [w.code for w in result.warnings]
        assert "MANY_HIDDEN" not in warning_codes

    def test_hidden_boundary_just_over_50_percent(self):
        """Boundary: 51%+ hidden -> warning."""
        from app.quality_assessment import assess_extraction_quality

        # 6/10 = 60% hidden (over 50%)
        elements = [
            create_dom_element(is_visible=False, text=f"Hidden {i}")
            for i in range(6)
        ] + [
            create_dom_element(is_visible=True, text=f"Visible {i}")
            for i in range(4)
        ]
        result = assess_extraction_quality(elements)
        warning_codes = [w.code for w in result.warnings]
        assert "MANY_HIDDEN" in warning_codes

    def test_all_visible_no_warning(self):
        """All visible elements -> no MANY_HIDDEN warning."""
        from app.quality_assessment import assess_extraction_quality

        elements = [
            create_dom_element(is_visible=True, text=f"Visible {i}")
            for i in range(10)
        ]
        result = assess_extraction_quality(elements)
        warning_codes = [w.code for w in result.warnings]
        assert "MANY_HIDDEN" not in warning_codes

    def test_all_hidden_warning(self):
        """All hidden elements -> MANY_HIDDEN warning."""
        from app.quality_assessment import assess_extraction_quality

        elements = [
            create_dom_element(is_visible=False, text=f"Hidden {i}")
            for i in range(10)
        ]
        result = assess_extraction_quality(elements)
        warning_codes = [w.code for w in result.warnings]
        assert "MANY_HIDDEN" in warning_codes


class TestTextLengthDetection:
    """Tests for text length detection rules."""

    def test_minimal_text_warning_under_10_chars_avg(self):
        """MINIMAL_TEXT warning when avg text length < 10 chars."""
        from app.quality_assessment import assess_extraction_quality

        # Short text, avg < 10 chars
        elements = [
            create_dom_element(text="Hi")  # 2 chars
            for _ in range(10)
        ]
        result = assess_extraction_quality(elements)
        warning_codes = [w.code for w in result.warnings]
        assert "MINIMAL_TEXT" in warning_codes

    def test_no_minimal_text_warning_over_10_chars_avg(self):
        """No MINIMAL_TEXT warning when avg text length >= 10 chars."""
        from app.quality_assessment import assess_extraction_quality

        # Longer text, avg >= 10 chars
        elements = [
            create_dom_element(text="This is a longer text content")  # 30 chars
            for _ in range(10)
        ]
        result = assess_extraction_quality(elements)
        warning_codes = [w.code for w in result.warnings]
        assert "MINIMAL_TEXT" not in warning_codes

    def test_text_length_boundary_exactly_10_chars(self):
        """Boundary: avg exactly 10 chars -> no warning."""
        from app.quality_assessment import assess_extraction_quality

        # Each element has exactly 10 chars
        elements = [
            create_dom_element(text="1234567890")  # 10 chars
            for _ in range(10)
        ]
        result = assess_extraction_quality(elements)
        warning_codes = [w.code for w in result.warnings]
        assert "MINIMAL_TEXT" not in warning_codes

    def test_text_length_boundary_under_10_chars(self):
        """Boundary: avg < 10 chars -> warning."""
        from app.quality_assessment import assess_extraction_quality

        # Each element has 9 chars
        elements = [
            create_dom_element(text="123456789")  # 9 chars
            for _ in range(10)
        ]
        result = assess_extraction_quality(elements)
        warning_codes = [w.code for w in result.warnings]
        assert "MINIMAL_TEXT" in warning_codes

    def test_empty_text_elements_warning(self):
        """Elements with empty text trigger MINIMAL_TEXT warning."""
        from app.quality_assessment import assess_extraction_quality

        elements = [
            create_dom_element(text="")  # 0 chars
            for _ in range(10)
        ]
        result = assess_extraction_quality(elements)
        warning_codes = [w.code for w in result.warnings]
        assert "MINIMAL_TEXT" in warning_codes

    def test_mixed_text_lengths(self):
        """Mixed text lengths calculate correct average."""
        from app.quality_assessment import assess_extraction_quality

        # Average: (20 + 20 + 0 + 0 + 0) / 5 = 8 chars -> warning
        elements = [
            create_dom_element(text="12345678901234567890"),  # 20 chars
            create_dom_element(text="12345678901234567890"),  # 20 chars
            create_dom_element(text=""),  # 0 chars
            create_dom_element(text=""),  # 0 chars
            create_dom_element(text=""),  # 0 chars
        ]
        result = assess_extraction_quality(elements)
        warning_codes = [w.code for w in result.warnings]
        assert "MINIMAL_TEXT" in warning_codes


class TestPerformanceBenchmarks:
    """Tests for performance requirements."""

    def test_performance_100_elements_under_5ms(self):
        """assess_extraction_quality completes in <5ms for 100 elements."""
        import time

        from app.quality_assessment import assess_extraction_quality

        elements = create_diverse_elements(100)

        # Run multiple times to get stable measurement
        iterations = 10
        total_time = 0
        for _ in range(iterations):
            start = time.perf_counter()
            assess_extraction_quality(elements)
            end = time.perf_counter()
            total_time += (end - start) * 1000  # Convert to ms

        avg_time = total_time / iterations
        assert avg_time < 5.0, f"Average time {avg_time:.2f}ms exceeds 5ms threshold"

    def test_performance_50_elements_under_2ms(self):
        """assess_extraction_quality completes in <2ms for 50 elements."""
        import time

        from app.quality_assessment import assess_extraction_quality

        elements = create_diverse_elements(50)

        iterations = 10
        total_time = 0
        for _ in range(iterations):
            start = time.perf_counter()
            assess_extraction_quality(elements)
            end = time.perf_counter()
            total_time += (end - start) * 1000

        avg_time = total_time / iterations
        assert avg_time < 2.0, f"Average time {avg_time:.2f}ms exceeds 2ms threshold"

    def test_performance_20_elements_under_1ms(self):
        """assess_extraction_quality completes in <1ms for 20 elements."""
        import time

        from app.quality_assessment import assess_extraction_quality

        elements = create_diverse_elements(20)

        iterations = 10
        total_time = 0
        for _ in range(iterations):
            start = time.perf_counter()
            assess_extraction_quality(elements)
            end = time.perf_counter()
            total_time += (end - start) * 1000

        avg_time = total_time / iterations
        assert avg_time < 1.0, f"Average time {avg_time:.2f}ms exceeds 1ms threshold"

    def test_performance_linear_scaling(self):
        """Performance scales linearly (O(n) complexity)."""
        import time

        from app.quality_assessment import assess_extraction_quality

        # Measure time for different element counts
        def measure_time(n: int) -> float:
            elements = create_diverse_elements(n)
            iterations = 5
            total = 0
            for _ in range(iterations):
                start = time.perf_counter()
                assess_extraction_quality(elements)
                end = time.perf_counter()
                total += (end - start)
            return total / iterations

        time_50 = measure_time(50)
        time_100 = measure_time(100)
        time_200 = measure_time(200)

        # Check for linear scaling: doubling elements should roughly double time
        # Allow for 3x tolerance due to overhead and measurement variance
        ratio_1 = time_100 / time_50 if time_50 > 0 else 1
        ratio_2 = time_200 / time_100 if time_100 > 0 else 1

        # Ratios should be roughly 2x (linear), definitely not 4x (quadratic)
        assert ratio_1 < 4.0, f"Ratio 100/50 = {ratio_1:.2f} suggests non-linear scaling"
        assert ratio_2 < 4.0, f"Ratio 200/100 = {ratio_2:.2f} suggests non-linear scaling"

    def test_performance_empty_list_fast(self):
        """Empty list should be extremely fast."""
        import time

        from app.quality_assessment import assess_extraction_quality

        iterations = 100
        total_time = 0
        for _ in range(iterations):
            start = time.perf_counter()
            assess_extraction_quality([])
            end = time.perf_counter()
            total_time += (end - start) * 1000

        avg_time = total_time / iterations
        assert avg_time < 0.5, f"Empty list took {avg_time:.3f}ms, expected <0.5ms"


class TestQualityAssessmentResult:
    """Tests for the structure of quality assessment results."""

    def test_result_has_quality_field(self):
        """Result has quality field with ExtractionQuality enum."""
        from app.quality_assessment import assess_extraction_quality

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


class TestQualityMetricsComputation:
    """Tests for QualityMetrics computation in assess_extraction_quality (Sprint 5.0)."""

    def test_result_has_metrics_field(self):
        """QualityAssessmentResult has metrics field."""
        from app.quality_assessment import assess_extraction_quality

        result = assess_extraction_quality([])
        assert hasattr(result, "metrics")

    def test_metrics_has_all_count_fields(self):
        """Metrics contains all 5 count fields."""
        from app.quality_assessment import assess_extraction_quality

        elements = create_diverse_elements(10)
        result = assess_extraction_quality(elements)

        assert hasattr(result.metrics, "element_count")
        assert hasattr(result.metrics, "visible_count")
        assert hasattr(result.metrics, "hidden_count")
        assert hasattr(result.metrics, "heading_count")
        assert hasattr(result.metrics, "unique_tag_count")

    def test_metrics_has_all_ratio_fields(self):
        """Metrics contains all ratio fields."""
        from app.quality_assessment import assess_extraction_quality

        elements = create_diverse_elements(10)
        result = assess_extraction_quality(elements)

        assert hasattr(result.metrics, "visible_ratio")
        assert hasattr(result.metrics, "hidden_ratio")

    def test_metrics_has_all_tag_fields(self):
        """Metrics contains all tag analysis fields."""
        from app.quality_assessment import assess_extraction_quality

        elements = create_diverse_elements(10)
        result = assess_extraction_quality(elements)

        assert hasattr(result.metrics, "unique_tags")
        assert hasattr(result.metrics, "has_headings")
        assert hasattr(result.metrics, "tag_distribution")

    def test_metrics_has_all_text_stats_fields(self):
        """Metrics contains all text statistics fields."""
        from app.quality_assessment import assess_extraction_quality

        elements = create_diverse_elements(10)
        result = assess_extraction_quality(elements)

        assert hasattr(result.metrics, "total_text_length")
        assert hasattr(result.metrics, "avg_text_length")
        assert hasattr(result.metrics, "min_text_length")
        assert hasattr(result.metrics, "max_text_length")

    def test_metrics_element_count_computed_correctly(self):
        """element_count matches number of input elements."""
        from app.quality_assessment import assess_extraction_quality

        elements = create_elements(25)
        result = assess_extraction_quality(elements)

        assert result.metrics.element_count == 25

    def test_metrics_visible_hidden_counts(self):
        """visible_count and hidden_count computed correctly."""
        from app.quality_assessment import assess_extraction_quality

        # 6 visible, 4 hidden
        elements = [
            create_dom_element(is_visible=True, text=f"Visible {i}")
            for i in range(6)
        ] + [
            create_dom_element(is_visible=False, text=f"Hidden {i}")
            for i in range(4)
        ]
        result = assess_extraction_quality(elements)

        assert result.metrics.visible_count == 6
        assert result.metrics.hidden_count == 4

    def test_metrics_heading_count(self):
        """heading_count correctly counts h1-h6 elements."""
        from app.quality_assessment import assess_extraction_quality

        elements = [
            create_dom_element(tag_name="h1", text="H1"),
            create_dom_element(tag_name="h2", text="H2"),
            create_dom_element(tag_name="h3", text="H3"),
            create_dom_element(tag_name="p", text="Para 1"),
            create_dom_element(tag_name="p", text="Para 2"),
        ]
        result = assess_extraction_quality(elements)

        assert result.metrics.heading_count == 3

    def test_metrics_unique_tag_count(self):
        """unique_tag_count correctly counts distinct tags."""
        from app.quality_assessment import assess_extraction_quality

        elements = [
            create_dom_element(tag_name="h1", text="H1"),
            create_dom_element(tag_name="h1", text="H1 again"),
            create_dom_element(tag_name="p", text="Para"),
            create_dom_element(tag_name="span", text="Span"),
        ]
        result = assess_extraction_quality(elements)

        assert result.metrics.unique_tag_count == 3  # h1, p, span

    def test_metrics_visibility_ratios(self):
        """visible_ratio and hidden_ratio computed correctly."""
        from app.quality_assessment import assess_extraction_quality

        # 8 visible, 2 hidden = 80% visible, 20% hidden
        elements = [
            create_dom_element(is_visible=True, text=f"Visible {i}")
            for i in range(8)
        ] + [
            create_dom_element(is_visible=False, text=f"Hidden {i}")
            for i in range(2)
        ]
        result = assess_extraction_quality(elements)

        assert result.metrics.visible_ratio == 0.8
        assert result.metrics.hidden_ratio == 0.2

    def test_metrics_unique_tags_list(self):
        """unique_tags contains list of distinct tag names."""
        from app.quality_assessment import assess_extraction_quality

        elements = [
            create_dom_element(tag_name="h1", text="H1"),
            create_dom_element(tag_name="p", text="Para"),
            create_dom_element(tag_name="span", text="Span"),
            create_dom_element(tag_name="p", text="Another para"),
        ]
        result = assess_extraction_quality(elements)

        assert isinstance(result.metrics.unique_tags, list)
        assert set(result.metrics.unique_tags) == {"h1", "p", "span"}

    def test_metrics_has_headings_true(self):
        """has_headings is True when headings present."""
        from app.quality_assessment import assess_extraction_quality

        elements = [
            create_dom_element(tag_name="h1", text="Heading"),
            create_dom_element(tag_name="p", text="Para"),
        ]
        result = assess_extraction_quality(elements)

        assert result.metrics.has_headings is True

    def test_metrics_has_headings_false(self):
        """has_headings is False when no headings."""
        from app.quality_assessment import assess_extraction_quality

        elements = [
            create_dom_element(tag_name="p", text="Para 1"),
            create_dom_element(tag_name="div", text="Div"),
        ]
        result = assess_extraction_quality(elements)

        assert result.metrics.has_headings is False

    def test_metrics_tag_distribution(self):
        """tag_distribution is dict with correct counts."""
        from app.quality_assessment import assess_extraction_quality

        elements = [
            create_dom_element(tag_name="h1", text="H1"),
            create_dom_element(tag_name="h1", text="H1 again"),
            create_dom_element(tag_name="p", text="Para 1"),
            create_dom_element(tag_name="p", text="Para 2"),
            create_dom_element(tag_name="p", text="Para 3"),
            create_dom_element(tag_name="span", text="Span"),
        ]
        result = assess_extraction_quality(elements)

        assert isinstance(result.metrics.tag_distribution, dict)
        assert result.metrics.tag_distribution == {"h1": 2, "p": 3, "span": 1}

    def test_metrics_total_text_length(self):
        """total_text_length sums all element text lengths."""
        from app.quality_assessment import assess_extraction_quality

        elements = [
            create_dom_element(text="12345"),  # 5 chars
            create_dom_element(text="1234567890"),  # 10 chars
            create_dom_element(text="123"),  # 3 chars
        ]
        result = assess_extraction_quality(elements)

        assert result.metrics.total_text_length == 18  # 5 + 10 + 3

    def test_metrics_avg_text_length(self):
        """avg_text_length computes correct average."""
        from app.quality_assessment import assess_extraction_quality

        elements = [
            create_dom_element(text="12345"),  # 5 chars
            create_dom_element(text="1234567890"),  # 10 chars
            create_dom_element(text="123"),  # 3 chars
        ]
        result = assess_extraction_quality(elements)

        assert result.metrics.avg_text_length == 6.0  # 18 / 3

    def test_metrics_min_max_text_length(self):
        """min_text_length and max_text_length tracked correctly."""
        from app.quality_assessment import assess_extraction_quality

        elements = [
            create_dom_element(text="123456789012345"),  # 15 chars
            create_dom_element(text="12"),  # 2 chars
            create_dom_element(text="12345678"),  # 8 chars
        ]
        result = assess_extraction_quality(elements)

        assert result.metrics.min_text_length == 2
        assert result.metrics.max_text_length == 15

    # === Edge Cases ===

    def test_metrics_empty_elements(self):
        """Empty elements list produces zero metrics."""
        from app.quality_assessment import assess_extraction_quality

        result = assess_extraction_quality([])

        assert result.metrics.element_count == 0
        assert result.metrics.visible_count == 0
        assert result.metrics.hidden_count == 0
        assert result.metrics.heading_count == 0
        assert result.metrics.unique_tag_count == 0
        assert result.metrics.visible_ratio == 0.0
        assert result.metrics.hidden_ratio == 0.0
        assert result.metrics.unique_tags == []
        assert result.metrics.has_headings is False
        assert result.metrics.tag_distribution == {}
        assert result.metrics.total_text_length == 0
        assert result.metrics.avg_text_length == 0.0
        assert result.metrics.min_text_length == 0
        assert result.metrics.max_text_length == 0

    def test_metrics_none_input(self):
        """None input produces zero metrics."""
        from app.quality_assessment import assess_extraction_quality

        result = assess_extraction_quality(None)  # type: ignore

        assert result.metrics.element_count == 0
        assert result.metrics.unique_tags == []

    def test_metrics_all_hidden_elements(self):
        """All hidden elements produce correct ratios."""
        from app.quality_assessment import assess_extraction_quality

        elements = [
            create_dom_element(is_visible=False, text=f"Hidden {i}")
            for i in range(10)
        ]
        result = assess_extraction_quality(elements)

        assert result.metrics.visible_count == 0
        assert result.metrics.hidden_count == 10
        assert result.metrics.visible_ratio == 0.0
        assert result.metrics.hidden_ratio == 1.0

    def test_metrics_single_tag_type(self):
        """Single tag type produces correct distribution."""
        from app.quality_assessment import assess_extraction_quality

        elements = [
            create_dom_element(tag_name="div", text=f"Div {i}")
            for i in range(20)
        ]
        result = assess_extraction_quality(elements)

        assert result.metrics.unique_tag_count == 1
        assert result.metrics.unique_tags == ["div"]
        assert result.metrics.tag_distribution == {"div": 20}

    def test_metrics_empty_text_elements(self):
        """Elements with empty text produce zero text stats."""
        from app.quality_assessment import assess_extraction_quality

        elements = [
            create_dom_element(text="")
            for _ in range(5)
        ]
        result = assess_extraction_quality(elements)

        assert result.metrics.total_text_length == 0
        assert result.metrics.avg_text_length == 0.0
        assert result.metrics.min_text_length == 0
        assert result.metrics.max_text_length == 0

    # === Performance ===

    def test_metrics_computation_performance(self):
        """Metrics computation adds < 2ms overhead for 100 elements."""
        import time

        from app.quality_assessment import assess_extraction_quality

        elements = create_diverse_elements(100)

        iterations = 10
        total_time = 0
        for _ in range(iterations):
            start = time.perf_counter()
            result = assess_extraction_quality(elements)
            _ = result.metrics  # Access metrics to ensure it's computed
            end = time.perf_counter()
            total_time += (end - start) * 1000

        avg_time = total_time / iterations
        # Original test allows 5ms for 100 elements, we're adding metrics computation
        # Should still be well under 7ms total (5ms + 2ms overhead)
        assert avg_time < 7.0, f"Average time {avg_time:.2f}ms exceeds 7ms threshold"

    def test_metrics_backward_compatibility(self):
        """Existing quality/warnings behavior unchanged."""
        from app.quality_assessment import assess_extraction_quality

        # Test EMPTY quality
        result_empty = assess_extraction_quality([])
        assert result_empty.quality == ExtractionQuality.EMPTY
        assert any(w.code == "NO_ELEMENTS" for w in result_empty.warnings)

        # Test GOOD quality
        elements_good = create_diverse_elements(25)
        result_good = assess_extraction_quality(elements_good)
        assert result_good.quality == ExtractionQuality.GOOD


class TestGenerateVisionHints:
    """Tests for generate_vision_hints() function (Sprint 5.0 Story 02+03).

    AC: 02-01 (Vision AI Model Compatibility)
    AC: 03-01 (Threshold Detection)
    AC: 03-02 (Tile Configuration Generation)
    AC: 03-03 (Recommendation Reasoning)
    """

    # === Function Existence ===

    def test_generate_vision_hints_exists(self):
        """generate_vision_hints function exists and is importable."""
        from app.quality_assessment import generate_vision_hints

        assert callable(generate_vision_hints)

    def test_generate_vision_hints_returns_vision_ai_hints(self):
        """generate_vision_hints returns VisionAIHints model."""
        from app.models import VisionAIHints
        from app.quality_assessment import generate_vision_hints

        result = generate_vision_hints(
            image_width=1280, image_height=720, image_size_bytes=150000
        )
        assert isinstance(result, VisionAIHints)

    # === Model Compatibility: Claude (1568px) ===

    def test_claude_compatible_when_within_limit(self):
        """Claude compatible when max dimension <= 1568px."""
        from app.quality_assessment import generate_vision_hints

        result = generate_vision_hints(
            image_width=1280, image_height=720, image_size_bytes=150000
        )
        assert result.claude_compatible is True

    def test_claude_not_compatible_when_exceeds_limit(self):
        """Claude not compatible when max dimension > 1568px."""
        from app.quality_assessment import generate_vision_hints

        result = generate_vision_hints(
            image_width=1920, image_height=1080, image_size_bytes=200000
        )
        assert result.claude_compatible is False

    def test_claude_compatible_at_exactly_1568(self):
        """Claude compatible at exactly 1568px boundary."""
        from app.quality_assessment import generate_vision_hints

        result = generate_vision_hints(
            image_width=1568, image_height=1000, image_size_bytes=150000
        )
        assert result.claude_compatible is True

    # === Model Compatibility: Gemini (3072px) ===

    def test_gemini_compatible_when_within_limit(self):
        """Gemini compatible when max dimension <= 3072px."""
        from app.quality_assessment import generate_vision_hints

        result = generate_vision_hints(
            image_width=2048, image_height=1536, image_size_bytes=300000
        )
        assert result.gemini_compatible is True

    def test_gemini_not_compatible_when_exceeds_limit(self):
        """Gemini not compatible when max dimension > 3072px."""
        from app.quality_assessment import generate_vision_hints

        result = generate_vision_hints(
            image_width=4000, image_height=3000, image_size_bytes=500000
        )
        assert result.gemini_compatible is False

    # === Model Compatibility: GPT-4V (2048px) ===

    def test_gpt4v_compatible_when_within_limit(self):
        """GPT-4V compatible when max dimension <= 2048px."""
        from app.quality_assessment import generate_vision_hints

        result = generate_vision_hints(
            image_width=1920, image_height=1080, image_size_bytes=200000
        )
        assert result.gpt4v_compatible is True

    def test_gpt4v_not_compatible_when_exceeds_limit(self):
        """GPT-4V not compatible when max dimension > 2048px."""
        from app.quality_assessment import generate_vision_hints

        result = generate_vision_hints(
            image_width=2560, image_height=1440, image_size_bytes=300000
        )
        assert result.gpt4v_compatible is False

    # === Model Compatibility: Qwen-VL (4096px) ===

    def test_qwen_compatible_when_within_limit(self):
        """Qwen-VL compatible when max dimension <= 4096px."""
        from app.quality_assessment import generate_vision_hints

        result = generate_vision_hints(
            image_width=3840, image_height=2160, image_size_bytes=400000
        )
        assert result.qwen_compatible is True

    def test_qwen_not_compatible_when_exceeds_limit(self):
        """Qwen-VL not compatible when max dimension > 4096px."""
        from app.quality_assessment import generate_vision_hints

        result = generate_vision_hints(
            image_width=5000, image_height=3000, image_size_bytes=600000
        )
        assert result.qwen_compatible is False

    # === Portrait Orientation (Height > Width) ===

    def test_uses_max_dimension_for_portrait(self):
        """Uses max dimension (height) for portrait orientation."""
        from app.quality_assessment import generate_vision_hints

        # Height is 2000px which exceeds Claude's 1568px
        result = generate_vision_hints(
            image_width=1000, image_height=2000, image_size_bytes=200000
        )
        assert result.claude_compatible is False
        assert result.gpt4v_compatible is True  # 2048 limit

    # === Resize Factor Calculation ===

    def test_resize_factor_is_1_when_all_compatible(self):
        """Resize factor is 1.0 when image fits all models."""
        from app.quality_assessment import generate_vision_hints

        result = generate_vision_hints(
            image_width=1280, image_height=720, image_size_bytes=150000
        )
        assert result.estimated_resize_factor == 1.0
        assert result.coordinate_accuracy == 1.0

    def test_resize_factor_for_claude_target(self):
        """Resize factor calculated for Claude target model."""
        from app.quality_assessment import generate_vision_hints

        # 1920px image, Claude limit is 1568px
        # Expected factor: 1568 / 1920 = 0.816...
        result = generate_vision_hints(
            image_width=1920,
            image_height=1080,
            image_size_bytes=200000,
            target_model="claude",
        )
        assert 0.8 <= result.estimated_resize_factor <= 0.82
        assert 0.8 <= result.coordinate_accuracy <= 0.82

    def test_resize_factor_for_gpt4v_target(self):
        """Resize factor calculated for GPT-4V target model."""
        from app.quality_assessment import generate_vision_hints

        # 4096px image, GPT-4V limit is 2048px
        # Expected factor: 2048 / 4096 = 0.5
        result = generate_vision_hints(
            image_width=4096,
            image_height=2160,
            image_size_bytes=400000,
            target_model="gpt4v",
        )
        assert result.estimated_resize_factor == 0.5

    # === Tiling Recommendations ===

    def test_tiling_not_recommended_for_small_images(self):
        """Tiling not recommended for images within all limits."""
        from app.quality_assessment import generate_vision_hints

        result = generate_vision_hints(
            image_width=1280, image_height=720, image_size_bytes=150000
        )
        assert result.tiling_recommended is False
        assert result.suggested_tile_count == 1
        assert result.suggested_tile_size is None
        assert result.tiling_reason is None

    def test_tiling_recommended_for_very_large_images(self):
        """Tiling recommended for images exceeding all model limits."""
        from app.quality_assessment import generate_vision_hints

        # 5000px exceeds all model limits including Qwen-VL's 4096px
        result = generate_vision_hints(
            image_width=5000, image_height=8000, image_size_bytes=2000000
        )
        assert result.tiling_recommended is True
        assert result.suggested_tile_count >= 2
        assert result.tiling_reason is not None

    def test_tile_count_increases_with_image_size(self):
        """Larger images get more tiles recommended."""
        from app.quality_assessment import generate_vision_hints

        result_medium = generate_vision_hints(
            image_width=5000, image_height=5000, image_size_bytes=1000000
        )
        result_large = generate_vision_hints(
            image_width=10000, image_height=10000, image_size_bytes=4000000
        )

        if result_medium.tiling_recommended and result_large.tiling_recommended:
            assert result_large.suggested_tile_count >= result_medium.suggested_tile_count

    def test_suggested_tile_size_has_width_and_height(self):
        """Suggested tile size contains width and height."""
        from app.quality_assessment import generate_vision_hints

        result = generate_vision_hints(
            image_width=8000, image_height=6000, image_size_bytes=2000000
        )

        if result.tiling_recommended and result.suggested_tile_size:
            assert "width" in result.suggested_tile_size
            assert "height" in result.suggested_tile_size
            assert result.suggested_tile_size["width"] > 0
            assert result.suggested_tile_size["height"] > 0

    # === Tiling Reason Text ===

    def test_tiling_reason_mentions_exceeding_limits(self):
        """Tiling reason explains why tiling is needed."""
        from app.quality_assessment import generate_vision_hints

        result = generate_vision_hints(
            image_width=6000, image_height=8000, image_size_bytes=2000000
        )

        if result.tiling_recommended:
            assert result.tiling_reason is not None
            # Reason should mention model or limit
            reason_lower = result.tiling_reason.lower()
            assert any(
                keyword in reason_lower
                for keyword in ["exceed", "limit", "large", "model"]
            )

    # === Image Dimensions in Result ===

    def test_result_includes_image_dimensions(self):
        """Result includes original image dimensions."""
        from app.quality_assessment import generate_vision_hints

        result = generate_vision_hints(
            image_width=1920, image_height=1080, image_size_bytes=200000
        )
        assert result.image_width == 1920
        assert result.image_height == 1080
        assert result.image_size_bytes == 200000

    # === Default Target Model Behavior ===

    def test_default_uses_most_restrictive_model(self):
        """Without target_model, uses most restrictive (Claude) for resize."""
        from app.quality_assessment import generate_vision_hints

        # 1920px exceeds Claude's 1568px
        result = generate_vision_hints(
            image_width=1920, image_height=1080, image_size_bytes=200000
        )
        # Resize factor should be based on Claude's limit
        assert result.estimated_resize_factor < 1.0

    # === VISION_MODEL_LIMITS Constant ===

    def test_vision_model_limits_constant_exists(self):
        """VISION_MODEL_LIMITS constant is defined."""
        from app.quality_assessment import VISION_MODEL_LIMITS

        assert isinstance(VISION_MODEL_LIMITS, dict)
        assert "claude" in VISION_MODEL_LIMITS
        assert "gemini" in VISION_MODEL_LIMITS
        assert "gpt4v" in VISION_MODEL_LIMITS
        assert "qwen-vl-max" in VISION_MODEL_LIMITS

    def test_vision_model_limits_has_correct_values(self):
        """VISION_MODEL_LIMITS has expected threshold values."""
        from app.quality_assessment import VISION_MODEL_LIMITS

        assert VISION_MODEL_LIMITS["claude"] == 1568
        assert VISION_MODEL_LIMITS["gemini"] == 3072
        assert VISION_MODEL_LIMITS["gpt4v"] == 2048
        assert VISION_MODEL_LIMITS["qwen-vl-max"] == 4096

    # === Target Model Parameter Handling ===

    def test_target_model_gemini_uses_gemini_limit(self):
        """target_model='gemini' uses Gemini's 3072px limit."""
        from app.quality_assessment import generate_vision_hints

        # 3072px exactly at Gemini limit
        result = generate_vision_hints(
            image_width=3072,
            image_height=2048,
            image_size_bytes=400000,
            target_model="gemini",
        )
        assert result.estimated_resize_factor == 1.0

    def test_target_model_qwen_uses_qwen_limit(self):
        """target_model='qwen-vl-max' uses Qwen's 4096px limit."""
        from app.quality_assessment import generate_vision_hints

        # 4096px exactly at Qwen limit
        result = generate_vision_hints(
            image_width=4096,
            image_height=2048,
            image_size_bytes=400000,
            target_model="qwen-vl-max",
        )
        assert result.estimated_resize_factor == 1.0

    def test_unknown_target_model_uses_claude_limit(self):
        """Unknown target_model falls back to Claude (most restrictive)."""
        from app.quality_assessment import generate_vision_hints

        # 1920px exceeds Claude's 1568px
        result = generate_vision_hints(
            image_width=1920,
            image_height=1080,
            image_size_bytes=200000,
            target_model="unknown-model",
        )
        # Should use Claude's limit (1568 / 1920 ≈ 0.816)
        assert 0.8 <= result.estimated_resize_factor <= 0.82

    def test_none_target_model_uses_claude_limit(self):
        """None target_model uses Claude (most restrictive)."""
        from app.quality_assessment import generate_vision_hints

        # 1920px exceeds Claude's 1568px
        result = generate_vision_hints(
            image_width=1920,
            image_height=1080,
            image_size_bytes=200000,
            target_model=None,
        )
        # Should use Claude's limit
        assert result.estimated_resize_factor < 1.0
