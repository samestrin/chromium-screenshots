# Vision AI Optimization Guide

> Optimize screenshots for Vision AI models with detailed metrics and tiling recommendations.

This guide covers how to use the Vision AI optimization features to ensure your screenshots work optimally with Claude, Gemini, GPT-4V, and Qwen-VL models.

---

## Quick Start

```bash
curl -X POST "http://localhost:8000/screenshot/json" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "extract_dom": {
      "enabled": true,
      "include_vision_hints": true,
      "target_vision_model": "claude"
    }
  }' | jq '.vision_hints'
```

---

## Model Dimension Limits

Each Vision AI model has specific dimension constraints:

| Model | Max Dimension | Max Pixels | Max Aspect Ratio |
|-------|---------------|------------|------------------|
| Claude | 1568px | ~2.5M | 4:1 |
| Gemini | 3072px | ~9.4M | 5:1 |
| GPT-4V | 2048px | ~4.2M | 4:1 |
| Qwen-VL | 4096px | ~16.8M | 6:1 |

### Environment Variable Configuration

Override default limits using environment variables:

```bash
# Set custom model limits
export VISION_CLAUDE_MAX_DIMENSION=1568
export VISION_GEMINI_MAX_DIMENSION=3072
export VISION_GPT4V_MAX_DIMENSION=2048
export VISION_QWEN_VL_MAX_MAX_DIMENSION=4096

# Set default target model
export VISION_DEFAULT_MODEL=claude

# Set tile overlap percentage (default 15%)
export VISION_TILE_OVERLAP_PERCENT=15
```

---

## VisionAIHints Response

When `include_vision_hints: true`, the response includes detailed optimization data:

```json
{
  "vision_hints": {
    "image_width": 1920,
    "image_height": 1080,
    "image_size_bytes": 524288,
    "document_width": null,
    "document_height": null,
    "claude_compatible": false,
    "gemini_compatible": true,
    "gpt4v_compatible": true,
    "qwen_compatible": true,
    "estimated_resize_factor": 0.817,
    "coordinate_accuracy": 0.817,
    "resize_impact_claude": 18.33,
    "resize_impact_gemini": 0.0,
    "resize_impact_gpt4v": 0.0,
    "resize_impact_qwen": 0.0,
    "recommended_width": 1568,
    "recommended_height": 882,
    "tiling_recommended": false,
    "suggested_tile_count": 1,
    "suggested_tile_size": null,
    "tile_overlap_percent": 15.0,
    "tiling_reason": null
  }
}
```

### Field Reference

| Field | Description |
|-------|-------------|
| `image_width/height` | Actual image dimensions |
| `document_width/height` | Full document size (for full_page screenshots) |
| `*_compatible` | Whether image fits within model limits |
| `resize_impact_*` | Percentage of detail loss if resized for model |
| `recommended_width/height` | Optimal dimensions for target model |
| `tiling_recommended` | Whether tiling is needed |
| `suggested_tile_count` | Number of tiles if tiling is recommended |
| `tile_overlap_percent` | Overlap between tiles (default 15%) |
| `tiling_reason` | Explanation of why tiling is recommended |

---

## Resize Impact Calculation

The resize impact shows percentage of detail loss when resizing for a model:

```
resize_impact = (max_dimension - model_limit) / max_dimension * 100
```

**Example:** 1920px image for Claude (1568px limit):
- `(1920 - 1568) / 1920 * 100 = 18.33%` detail loss

---

## Tiling Recommendations

For large images exceeding model limits, tiling is recommended:

```bash
# Full-page screenshot with tiling hints
curl -X POST "http://localhost:8000/screenshot/json" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/long-page",
    "screenshot_type": "full_page",
    "extract_dom": {
      "enabled": true,
      "include_vision_hints": true,
      "target_vision_model": "claude"
    }
  }'
```

Example tiling response:

```json
{
  "vision_hints": {
    "image_width": 1920,
    "image_height": 5000,
    "document_width": 1920,
    "document_height": 5000,
    "tiling_recommended": true,
    "suggested_tile_count": 4,
    "suggested_tile_size": {"width": 1568, "height": 1250},
    "tile_overlap_percent": 15.0,
    "tiling_reason": "The document size 1920x5000 exceeds limits for: Claude (1568px). Recommended 1x4 grid (4 tiles) with 15% overlap for claude."
  }
}
```

### Tile Overlap

Tiles overlap by default (15%) to ensure no content is lost at boundaries. Configure via:

```bash
export VISION_TILE_OVERLAP_PERCENT=20  # 20% overlap
```

---

## Best Practices

### 1. Choose the Right Model

```bash
# For quick analysis, use Claude (smallest limit)
"target_vision_model": "claude"

# For large dashboards, use Gemini or Qwen-VL
"target_vision_model": "gemini"
```

### 2. Check Compatibility Before Processing

```python
import requests

response = requests.post(
    "http://localhost:8000/screenshot/json",
    json={
        "url": "https://example.com",
        "extract_dom": {
            "enabled": True,
            "include_vision_hints": True,
            "target_vision_model": "claude"
        }
    }
)

hints = response.json()["vision_hints"]

if hints["claude_compatible"]:
    # Process directly
    pass
elif hints["tiling_recommended"]:
    # Implement tiling strategy
    tile_count = hints["suggested_tile_count"]
    tile_size = hints["suggested_tile_size"]
else:
    # Resize to recommended dimensions
    new_width = hints["recommended_width"]
    new_height = hints["recommended_height"]
```

### 3. Monitor Resize Impact

If `resize_impact_*` exceeds 30%, consider:
- Using a model with higher limits
- Implementing tiling
- Capturing at lower resolution

### 4. Full-Page Screenshots

For full-page screenshots, document dimensions are used for tiling calculations:

```json
{
  "screenshot_type": "full_page",
  "extract_dom": {
    "enabled": true,
    "include_vision_hints": true
  }
}
```

---

## Integration Examples

### Python: Auto-Resize for Claude

```python
from PIL import Image
import io
import requests

def capture_for_claude(url: str) -> bytes:
    """Capture screenshot optimized for Claude Vision."""
    response = requests.post(
        "http://localhost:8000/screenshot/json",
        json={
            "url": url,
            "extract_dom": {
                "enabled": True,
                "include_vision_hints": True,
                "target_vision_model": "claude"
            }
        }
    )
    data = response.json()
    hints = data["vision_hints"]
    
    if hints["claude_compatible"]:
        return base64.b64decode(data["image_base64"])
    
    # Resize to recommended dimensions
    img_bytes = base64.b64decode(data["image_base64"])
    img = Image.open(io.BytesIO(img_bytes))
    
    new_size = (hints["recommended_width"], hints["recommended_height"])
    img = img.resize(new_size, Image.LANCZOS)
    
    output = io.BytesIO()
    img.save(output, format="PNG")
    return output.getvalue()
```

### JavaScript: Tiling Implementation

```javascript
async function captureWithTiling(url, targetModel = 'claude') {
  const response = await fetch('http://localhost:8000/screenshot/json', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      url,
      screenshot_type: 'full_page',
      extract_dom: {
        enabled: true,
        include_vision_hints: true,
        target_vision_model: targetModel
      }
    })
  });
  
  const data = await response.json();
  const hints = data.vision_hints;
  
  if (!hints.tiling_recommended) {
    return [data.image_base64];
  }
  
  // Implement tiling based on suggested_tile_size
  const { width, height } = hints.suggested_tile_size;
  const overlap = hints.tile_overlap_percent / 100;
  
  // Return array of tile requests or implement client-side tiling
  console.log(`Tiling recommended: ${hints.suggested_tile_count} tiles`);
  console.log(`Tile size: ${width}x${height} with ${hints.tile_overlap_percent}% overlap`);
  
  return data;
}
```

---

## See Also

- [API Reference](api-reference.md) - Full endpoint documentation
- [DOM Extraction](dom-extraction.md) - Ground-truth element extraction
- [Quality Assessment](quality-assessment.md) - Extraction quality metrics
