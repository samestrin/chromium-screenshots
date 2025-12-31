"""Quality assessment for DOM extraction results.

This module provides quality assessment for DOM extraction results,
generating quality levels and actionable warnings to help users
understand extraction quality and debug issues.
"""

from dataclasses import dataclass, field
from typing import Optional, Sequence

from app.models import DomElement, ExtractionQuality, QualityWarning

# Thresholds for quality levels
THRESHOLD_EMPTY = 0
THRESHOLD_POOR = 4
THRESHOLD_LOW = 20
THRESHOLD_GOOD = 21
THRESHOLD_TAG_DIVERSITY = 3
THRESHOLD_HIDDEN_RATIO = 0.5
THRESHOLD_MIN_TEXT_LENGTH = 10

# Heading tags for detection
HEADING_TAGS = frozenset({"h1", "h2", "h3", "h4", "h5", "h6"})

# Example URLs for verification suggestions
VERIFICATION_URLS = [
    "https://example.com",
    "https://httpbin.org/html",
]


@dataclass
class QualityMetricsData:
    """Internal dataclass for computed quality metrics.

    Contains all computed metrics from DOM extraction analysis.
    Field names match the QualityMetrics Pydantic model.
    """

    # Element counts
    element_count: int = 0
    visible_count: int = 0
    hidden_count: int = 0
    heading_count: int = 0
    unique_tag_count: int = 0

    # Visibility ratios
    visible_ratio: float = 0.0
    hidden_ratio: float = 0.0

    # Tag analysis
    unique_tags: list[str] = field(default_factory=list)
    has_headings: bool = False
    tag_distribution: dict[str, int] = field(default_factory=dict)

    # Text statistics
    total_text_length: int = 0
    avg_text_length: float = 0.0
    min_text_length: int = 0
    max_text_length: int = 0


@dataclass
class QualityAssessmentResult:
    """Result of quality assessment.

    Contains the quality level, warnings, and detailed metrics
    generated during assessment.
    """

    quality: ExtractionQuality
    warnings: list[QualityWarning]
    metrics: QualityMetricsData = field(default_factory=QualityMetricsData)


def assess_extraction_quality(
    elements: Optional[Sequence[DomElement]],
) -> QualityAssessmentResult:
    """Assess the quality of DOM extraction results.

    Analyzes the extracted elements and returns a quality level
    (GOOD, LOW, POOR, EMPTY) along with any warnings about
    potential issues and detailed metrics.

    Args:
        elements: List of DomElement objects from extraction.
                  Can be None or empty list.

    Returns:
        QualityAssessmentResult with quality level, warnings, and metrics.

    Performance: O(n) - single pass through elements.
    """
    # Handle None input
    if elements is None:
        elements = []

    warnings: list[QualityWarning] = []
    element_count = len(elements)

    # === Element Count Analysis ===
    if element_count == 0:
        warnings.append(QualityWarning(
            code="NO_ELEMENTS",
            message="No DOM elements were extracted from the page.",
            suggestion=(
                "Verify the page has loaded completely and contains "
                "the expected content. Try testing with a simple URL like "
                f"{VERIFICATION_URLS[0]} to confirm extraction is working."
            ),
        ))
        # Return empty metrics for zero elements
        empty_metrics = QualityMetricsData(
            element_count=0,
            visible_count=0,
            hidden_count=0,
            heading_count=0,
            unique_tag_count=0,
            visible_ratio=0.0,
            hidden_ratio=0.0,
            unique_tags=[],
            has_headings=False,
            tag_distribution={},
            total_text_length=0,
            avg_text_length=0.0,
            min_text_length=0,
            max_text_length=0,
        )
        return QualityAssessmentResult(
            quality=ExtractionQuality.EMPTY,
            warnings=warnings,
            metrics=empty_metrics,
        )

    if element_count <= THRESHOLD_POOR:
        warnings.append(QualityWarning(
            code="LOW_ELEMENT_COUNT",
            message=f"Only {element_count} element(s) extracted, which is very sparse.",
            suggestion=(
                "Check if the page has finished loading, or expand the extraction "
                f"selectors. Test with {VERIFICATION_URLS[0]} to verify setup."
            ),
        ))

    # === Tag Analysis (single pass) ===
    unique_tags_set: set[str] = set()
    tag_distribution: dict[str, int] = {}
    has_heading = False
    heading_count = 0
    visible_count = 0
    total_text_length = 0
    min_text_length = float("inf")
    max_text_length = 0

    for element in elements:
        # Safe attribute access
        tag_name = getattr(element, "tag_name", "") or ""
        tag_lower = tag_name.lower()
        unique_tags_set.add(tag_lower)

        # Track tag distribution
        tag_distribution[tag_lower] = tag_distribution.get(tag_lower, 0) + 1

        if tag_lower in HEADING_TAGS:
            has_heading = True
            heading_count += 1

        is_visible = getattr(element, "is_visible", True)
        if is_visible:
            visible_count += 1

        text = getattr(element, "text", "") or ""
        text_len = len(text)
        total_text_length += text_len
        if text_len < min_text_length:
            min_text_length = text_len
        if text_len > max_text_length:
            max_text_length = text_len

    # Handle case where min_text_length was never updated (shouldn't happen with elements)
    if min_text_length == float("inf"):
        min_text_length = 0

    # === Compute derived metrics ===
    hidden_count = element_count - visible_count
    tag_diversity = len(unique_tags_set)
    visible_ratio = visible_count / element_count
    hidden_ratio = hidden_count / element_count
    avg_text_length = total_text_length / element_count

    # === Tag Diversity Check ===
    if tag_diversity < THRESHOLD_TAG_DIVERSITY and element_count >= THRESHOLD_GOOD:
        warnings.append(QualityWarning(
            code="LOW_TAG_DIVERSITY",
            message=f"Only {tag_diversity} unique tag type(s) found "
            f"among {element_count} elements.",
            suggestion=(
                "Consider expanding extraction selectors to capture a broader "
                "variety of content (headings, paragraphs, links, etc.)."
            ),
        ))

    # === Heading Check ===
    if not has_heading and element_count >= THRESHOLD_LOW // 2:
        warnings.append(QualityWarning(
            code="NO_HEADINGS",
            message="No heading elements (h1-h6) found in the extraction.",
            suggestion=(
                "Heading elements often contain important structural information. "
                "Consider adding h1-h6 to your extraction selectors."
            ),
        ))

    # === Hidden Elements Check ===
    if hidden_ratio > THRESHOLD_HIDDEN_RATIO:
        warnings.append(QualityWarning(
            code="MANY_HIDDEN",
            message=f"{int(hidden_ratio * 100)}% of elements are hidden "
            f"({hidden_count}/{element_count}).",
            suggestion=(
                "Many hidden elements may indicate the page hasn't rendered fully "
                "or content is behind user interaction. Consider adding wait time "
                "or check for dynamic content loading."
            ),
        ))

    # === Text Length Check ===
    if avg_text_length < THRESHOLD_MIN_TEXT_LENGTH:
        warnings.append(QualityWarning(
            code="MINIMAL_TEXT",
            message=f"Average text length is only "
            f"{avg_text_length:.1f} characters per element.",
            suggestion=(
                "Elements have minimal text content. This may indicate extraction "
                "of UI elements rather than content, or the page may have limited text."
            ),
        ))

    # === Determine Quality Level ===
    if element_count <= THRESHOLD_POOR:
        quality = ExtractionQuality.POOR
    elif element_count <= THRESHOLD_LOW:
        quality = ExtractionQuality.LOW
    else:
        # 21+ elements: Check for GOOD eligibility
        # Requires diversity AND headings
        if tag_diversity >= THRESHOLD_TAG_DIVERSITY and has_heading:
            quality = ExtractionQuality.GOOD
        else:
            quality = ExtractionQuality.LOW

    # === Build metrics dataclass ===
    metrics = QualityMetricsData(
        element_count=element_count,
        visible_count=visible_count,
        hidden_count=hidden_count,
        heading_count=heading_count,
        unique_tag_count=tag_diversity,
        visible_ratio=visible_ratio,
        hidden_ratio=hidden_ratio,
        unique_tags=sorted(unique_tags_set),
        has_headings=has_heading,
        tag_distribution=tag_distribution,
        total_text_length=total_text_length,
        avg_text_length=avg_text_length,
        min_text_length=int(min_text_length),
        max_text_length=max_text_length,
    )

    return QualityAssessmentResult(
        quality=quality,
        warnings=warnings,
        metrics=metrics,
    )
