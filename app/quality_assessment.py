"""Quality assessment for DOM extraction results.

This module provides quality assessment for DOM extraction results,
generating quality levels and actionable warnings to help users
understand extraction quality and debug issues.
"""

from dataclasses import dataclass
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
class QualityAssessmentResult:
    """Result of quality assessment.

    Contains the quality level and any warnings generated
    during assessment.
    """
    quality: ExtractionQuality
    warnings: list[QualityWarning]


def assess_extraction_quality(
    elements: Optional[Sequence[DomElement]],
) -> QualityAssessmentResult:
    """Assess the quality of DOM extraction results.

    Analyzes the extracted elements and returns a quality level
    (GOOD, LOW, POOR, EMPTY) along with any warnings about
    potential issues.

    Args:
        elements: List of DomElement objects from extraction.
                  Can be None or empty list.

    Returns:
        QualityAssessmentResult with quality level and warnings.

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
        return QualityAssessmentResult(
            quality=ExtractionQuality.EMPTY,
            warnings=warnings,
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
    unique_tags: set[str] = set()
    has_heading = False
    visible_count = 0
    total_text_length = 0

    for element in elements:
        # Safe attribute access
        tag_name = getattr(element, "tag_name", "") or ""
        tag_lower = tag_name.lower()
        unique_tags.add(tag_lower)

        if tag_lower in HEADING_TAGS:
            has_heading = True

        is_visible = getattr(element, "is_visible", True)
        if is_visible:
            visible_count += 1

        text = getattr(element, "text", "") or ""
        total_text_length += len(text)

    # === Tag Diversity Check ===
    tag_diversity = len(unique_tags)
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
    if element_count > 0:
        hidden_count = element_count - visible_count
        hidden_ratio = hidden_count / element_count
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
    if element_count > 0:
        avg_text_length = total_text_length / element_count
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

    return QualityAssessmentResult(
        quality=quality,
        warnings=warnings,
    )
