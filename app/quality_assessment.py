"""Quality assessment for DOM extraction results.

This module provides quality assessment for DOM extraction results,
generating quality levels and actionable warnings to help users
understand extraction quality and debug issues.
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Sequence

from app.models import DomElement, ExtractionQuality, QualityWarning


def _load_model_config() -> Optional[dict]:
    """Load vision model configuration from JSON file if it exists.

    Looks for vision_model_config.json in the app directory.
    Returns None if file doesn't exist or can't be parsed.
    """
    config_path = Path(__file__).parent / "vision_model_config.json"
    if not config_path.exists():
        return None

    try:
        with open(config_path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


# Load JSON config at module level (optional)
_MODEL_CONFIG = _load_model_config()

if TYPE_CHECKING:
    from app.models import VisionAIHints

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


# Vision AI model dimension limits (max dimension in pixels)
# Configurable via environment variables or JSON config with sensible defaults
def _get_model_limit(model: str, default: int) -> int:
    """Get model limit from environment variable, JSON config, or use default.

    Priority: 1. Environment variable, 2. JSON config, 3. Default value
    """
    # Check environment variable first
    env_key = f"VISION_{model.upper().replace('-', '_')}_MAX_DIMENSION"
    env_value = os.getenv(env_key)
    if env_value is not None:
        return int(env_value)

    # Check JSON config
    if _MODEL_CONFIG and "models" in _MODEL_CONFIG:
        model_data = _MODEL_CONFIG["models"].get(model, {})
        if "max_dimension" in model_data:
            return int(model_data["max_dimension"])

    return default


def _get_model_constraints_from_config(model: str) -> dict[str, float]:
    """Get model constraints from JSON config if available."""
    if _MODEL_CONFIG and "models" in _MODEL_CONFIG:
        model_data = _MODEL_CONFIG["models"].get(model, {})
        return {
            "max_pixels": model_data.get("max_pixels", float("inf")),
            "max_aspect_ratio": model_data.get("max_aspect_ratio", float("inf")),
        }
    return {"max_pixels": float("inf"), "max_aspect_ratio": float("inf")}


# Model limit defaults (can be overridden via environment variables)
# Environment variable format: VISION_<MODEL>_MAX_DIMENSION
# Examples:
#   VISION_CLAUDE_MAX_DIMENSION=1568
#   VISION_GEMINI_MAX_DIMENSION=3072
#   VISION_GPT4V_MAX_DIMENSION=2048
#   VISION_QWEN_VL_MAX_MAX_DIMENSION=4096
VISION_MODEL_LIMITS: dict[str, int] = {
    "claude": _get_model_limit("claude", 1568),
    "gemini": _get_model_limit("gemini", 3072),
    "gpt4v": _get_model_limit("gpt4v", 2048),
    "qwen-vl-max": _get_model_limit("qwen-vl-max", 4096),
}

# Additional model constraints (max_pixels, max_aspect_ratio)
# Format: model -> {max_pixels: int, max_aspect_ratio: float}
VISION_MODEL_CONSTRAINTS: dict[str, dict[str, float]] = {
    "claude": {"max_pixels": 1_568 * 1_568, "max_aspect_ratio": 4.0},
    "gemini": {"max_pixels": 3_072 * 3_072, "max_aspect_ratio": 5.0},
    "gpt4v": {"max_pixels": 2_048 * 2_048, "max_aspect_ratio": 4.0},
    "qwen-vl-max": {"max_pixels": 4_096 * 4_096, "max_aspect_ratio": 6.0},
}

# Default Vision AI model (configurable via VISION_DEFAULT_MODEL env var or JSON config)
def _get_default_model() -> str:
    """Get default model from env var, JSON config, or use 'claude'."""
    env_value = os.getenv("VISION_DEFAULT_MODEL")
    if env_value:
        return env_value
    if _MODEL_CONFIG and "defaults" in _MODEL_CONFIG:
        return _MODEL_CONFIG["defaults"].get("target_model", "claude")
    return "claude"


VISION_DEFAULT_MODEL: str = _get_default_model()


# Default tile overlap percentage (configurable via VISION_TILE_OVERLAP_PERCENT or JSON config)
def _get_tile_overlap() -> float:
    """Get tile overlap from env var, JSON config, or use 15%."""
    env_value = os.getenv("VISION_TILE_OVERLAP_PERCENT")
    if env_value:
        return float(env_value)
    if _MODEL_CONFIG and "defaults" in _MODEL_CONFIG:
        return float(_MODEL_CONFIG["defaults"].get("tile_overlap_percent", 15))
    return 15.0


VISION_TILE_OVERLAP_PERCENT: float = _get_tile_overlap()


def _calculate_resize_impact(max_dimension: int, model_limit: int) -> float:
    """Calculate resize impact percentage for a model.

    Formula: (max(width, height) - limit) / max(width, height) * 100
    Returns 0.0 if no resize is needed.
    """
    if max_dimension <= model_limit:
        return 0.0
    return ((max_dimension - model_limit) / max_dimension) * 100


def _calculate_recommended_dimensions(
    width: int, height: int, target_limit: int
) -> tuple[Optional[int], Optional[int]]:
    """Calculate recommended dimensions to fit within target limit.

    Maintains aspect ratio while scaling to fit within the limit.
    Returns (None, None) if no resize is needed.
    """
    max_dim = max(width, height)
    if max_dim <= target_limit:
        return None, None

    scale = target_limit / max_dim
    return int(width * scale), int(height * scale)


def _check_model_compatibility(
    width: int, height: int, model: str
) -> tuple[bool, Optional[str]]:
    """Check if image is compatible with a model, including all constraints.

    Returns (is_compatible, reason_if_not_compatible).
    """
    max_dimension = max(width, height)
    limit = VISION_MODEL_LIMITS.get(model, 0)

    if max_dimension > limit:
        return False, f"max dimension {max_dimension}px exceeds {model} limit of {limit}px"

    constraints = VISION_MODEL_CONSTRAINTS.get(model, {})

    # Check max_pixels constraint
    total_pixels = width * height
    max_pixels = constraints.get("max_pixels", float("inf"))
    if total_pixels > max_pixels:
        return False, (
            f"total pixels ({total_pixels:,}) exceeds "
            f"{model} max_pixels ({int(max_pixels):,})"
        )

    # Check aspect ratio constraint
    aspect_ratio = max(width, height) / min(width, height) if min(width, height) > 0 else 1.0
    max_aspect = constraints.get("max_aspect_ratio", float("inf"))
    if aspect_ratio > max_aspect:
        return False, f"aspect ratio ({aspect_ratio:.2f}) exceeds {model} max ({max_aspect:.1f})"

    return True, None


def generate_vision_hints(
    image_width: int,
    image_height: int,
    image_size_bytes: int,
    target_model: Optional[str] = None,
    document_width: Optional[int] = None,
    document_height: Optional[int] = None,
) -> "VisionAIHints":
    """Generate Vision AI optimization hints for an image.

    Calculates compatibility with various Vision AI models based on
    image dimensions, and provides resize impact estimation and
    tiling recommendations.

    Args:
        image_width: Image width in pixels
        image_height: Image height in pixels
        image_size_bytes: Image file size in bytes
        target_model: Optional specific model to optimize for.
                      If None, uses VISION_DEFAULT_MODEL env var or 'claude'.
        document_width: Full document width for full_page screenshots
        document_height: Full document height for full_page screenshots

    Returns:
        VisionAIHints with compatibility flags, resize factors, and
        tiling recommendations.
    """
    from app.models import VisionAIHints

    # Use document dimensions for tiling if available (full_page screenshots)
    tiling_width = document_width if document_width else image_width
    tiling_height = document_height if document_height else image_height

    max_dimension = max(image_width, image_height)
    max_tiling_dimension = max(tiling_width, tiling_height)

    # Calculate compatibility for each model (using image dimensions)
    claude_compat, claude_reason = _check_model_compatibility(image_width, image_height, "claude")
    gemini_compat, gemini_reason = _check_model_compatibility(image_width, image_height, "gemini")
    gpt4v_compat, gpt4v_reason = _check_model_compatibility(image_width, image_height, "gpt4v")
    qwen_compat, qwen_reason = _check_model_compatibility(image_width, image_height, "qwen-vl-max")

    # Calculate per-model resize impact percentages
    resize_impact_claude = _calculate_resize_impact(max_dimension, VISION_MODEL_LIMITS["claude"])
    resize_impact_gemini = _calculate_resize_impact(max_dimension, VISION_MODEL_LIMITS["gemini"])
    resize_impact_gpt4v = _calculate_resize_impact(max_dimension, VISION_MODEL_LIMITS["gpt4v"])
    resize_impact_qwen = _calculate_resize_impact(max_dimension, VISION_MODEL_LIMITS["qwen-vl-max"])

    # Determine target model for resize calculations
    effective_target = target_model if target_model in VISION_MODEL_LIMITS else VISION_DEFAULT_MODEL
    target_limit = VISION_MODEL_LIMITS.get(effective_target, VISION_MODEL_LIMITS["claude"])

    # Calculate resize factor and recommended dimensions
    if max_dimension <= target_limit:
        estimated_resize_factor = 1.0
        coordinate_accuracy = 1.0
        recommended_width = None
        recommended_height = None
    else:
        estimated_resize_factor = target_limit / max_dimension
        coordinate_accuracy = estimated_resize_factor
        recommended_width, recommended_height = _calculate_recommended_dimensions(
            image_width, image_height, target_limit
        )

    # Determine tiling recommendations using document dimensions for full_page
    # Tiling is recommended if image exceeds target model limit
    target_exceeded = max_tiling_dimension > target_limit

    if target_exceeded:
        tiling_recommended = True
        # Calculate suggested tile count based on target model limit
        # Account for overlap
        overlap_factor = 1.0 - (VISION_TILE_OVERLAP_PERCENT / 100.0)
        effective_tile_dim = int(target_limit * overlap_factor)

        tiles_x = max(1, (tiling_width + effective_tile_dim - 1) // effective_tile_dim)
        tiles_y = max(1, (tiling_height + effective_tile_dim - 1) // effective_tile_dim)
        suggested_tile_count = tiles_x * tiles_y

        # Calculate tile size (before overlap)
        tile_width = min(target_limit, (tiling_width + tiles_x - 1) // tiles_x)
        tile_height = min(target_limit, (tiling_height + tiles_y - 1) // tiles_y)
        suggested_tile_size = {"width": tile_width, "height": tile_height}

        # Build specific reasoning message
        dimension_info = f"{tiling_width}x{tiling_height}"
        if document_width and document_height:
            dimension_info = f"document size {dimension_info}"
        else:
            dimension_info = f"image size {dimension_info}"

        # Determine which thresholds are exceeded
        exceeded_models = []
        if not claude_compat:
            exceeded_models.append(f"Claude ({VISION_MODEL_LIMITS['claude']}px)")
        if not gemini_compat:
            exceeded_models.append(f"Gemini ({VISION_MODEL_LIMITS['gemini']}px)")
        if not gpt4v_compat:
            exceeded_models.append(f"GPT-4V ({VISION_MODEL_LIMITS['gpt4v']}px)")
        if not qwen_compat:
            exceeded_models.append(f"Qwen-VL ({VISION_MODEL_LIMITS['qwen-vl-max']}px)")

        if exceeded_models:
            models_str = ", ".join(exceeded_models)
            tiling_reason = (
                f"The {dimension_info} exceeds limits for: {models_str}. "
                f"Recommended {tiles_x}x{tiles_y} grid ({suggested_tile_count} tiles) "
                f"with {VISION_TILE_OVERLAP_PERCENT:.0f}% overlap for {effective_target}."
            )
        else:
            tiling_reason = (
                f"The {dimension_info} exceeds {effective_target} limit ({target_limit}px). "
                f"Recommended {tiles_x}x{tiles_y} grid ({suggested_tile_count} tiles) "
                f"with {VISION_TILE_OVERLAP_PERCENT:.0f}% overlap."
            )
    else:
        tiling_recommended = False
        suggested_tile_count = 1
        suggested_tile_size = None
        tiling_reason = None

    return VisionAIHints(
        image_width=image_width,
        image_height=image_height,
        image_size_bytes=image_size_bytes,
        document_width=document_width,
        document_height=document_height,
        claude_compatible=claude_compat,
        gemini_compatible=gemini_compat,
        gpt4v_compatible=gpt4v_compat,
        qwen_compatible=qwen_compat,
        estimated_resize_factor=estimated_resize_factor,
        coordinate_accuracy=coordinate_accuracy,
        resize_impact_claude=resize_impact_claude,
        resize_impact_gemini=resize_impact_gemini,
        resize_impact_gpt4v=resize_impact_gpt4v,
        resize_impact_qwen=resize_impact_qwen,
        recommended_width=recommended_width,
        recommended_height=recommended_height,
        tiling_recommended=tiling_recommended,
        suggested_tile_count=suggested_tile_count,
        suggested_tile_size=suggested_tile_size,
        tile_overlap_percent=VISION_TILE_OVERLAP_PERCENT,
        tiling_reason=tiling_reason,
    )
