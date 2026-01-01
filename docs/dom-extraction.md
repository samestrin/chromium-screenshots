# DOM Extraction

> Extract text and bounding boxes from the same render frame as your screenshot.

DOM extraction enables **Zero-Drift** captures where the screenshot pixels and DOM coordinates are guaranteed to match. This is essential for Vision AI applications that need ground-truth text content.

---

## Quick Start

```bash
curl -X POST "http://localhost:8000/screenshot/json" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "extract_dom": {
      "enabled": true,
      "selectors": ["h1", "p", "a"],
      "max_elements": 100
    }
  }' | jq '.dom_extraction'
```

---

## Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `false` | Enable DOM extraction |
| `selectors` | array | (default list) | CSS selectors to match |
| `include_hidden` | boolean | `false` | Include `visibility:hidden` or `display:none` elements |
| `min_text_length` | integer | `1` | Skip elements with less text |
| `max_elements` | integer | `500` | Cap on returned elements |
| `include_metrics` | boolean | `false` | Include detailed quality metrics |
| `include_vision_hints` | boolean | `false` | Include Vision AI optimization hints |
| `target_vision_model` | string | `null` | Target model: `claude`, `gemini`, `gpt4v`, `qwen-vl-max` |

### Default Selectors

When `selectors` is not specified:

```
h1, h2, h3, h4, h5, h6, p, span, a, li, button, label,
td, th, caption, figcaption, blockquote
```

### Selector Examples

```json
// Headlines only
{"selectors": ["h1", "h2", "h3"]}

// Navigation links
{"selectors": ["nav a", "header a"]}

// Form elements
{"selectors": ["input", "button", "label"]}

// All text containers
{"selectors": ["*"]}  // Use with max_elements!
```

---

## Response Schema

When `extract_dom.enabled` is true, the response includes:

```json
{
  "dom_extraction": {
    "elements": [...],
    "viewport": {
      "width": 1920,
      "height": 1080,
      "deviceScaleFactor": 1
    },
    "extraction_time_ms": 23.45,
    "element_count": 47,
    "quality": "good",
    "warnings": []
  }
}
```

### DomExtractionResult Fields

| Field | Type | Description |
|-------|------|-------------|
| `elements` | array | List of [DomElement](#domelement-fields) objects |
| `viewport` | object | Page dimensions and scale |
| `extraction_time_ms` | float | Extraction duration |
| `element_count` | integer | Total elements returned |
| `quality` | string | `good`, `low`, `poor`, or `empty` |
| `warnings` | array | Quality warnings (see [Quality Assessment](quality-assessment.md)) |
| `metrics` | object | Detailed quality metrics (when `include_metrics: true`) |
| `vision_hints` | object | Vision AI optimization hints (when `include_vision_hints: true`) |

---

## DomElement Fields

Each element in the `elements` array:

```json
{
  "selector": "body > main > h1:nth-child(1)",
  "xpath": "/html/body/main/h1[1]",
  "tag_name": "h1",
  "text": "Welcome to Example",
  "rect": {
    "x": 100,
    "y": 50,
    "width": 400,
    "height": 32
  },
  "computed_style": {
    "color": "rgb(0, 0, 0)",
    "backgroundColor": "rgba(0, 0, 0, 0)",
    "fontSize": "32px",
    "fontWeight": "700"
  },
  "is_visible": true,
  "z_index": 0,
  "is_fixed": false,
  "tile_index": null,
  "tile_relative_rect": null
}
```

| Field | Type | Description |
|-------|------|-------------|
| `selector` | string | Unique CSS selector (uses `CSS.escape` for special chars) |
| `xpath` | string | Full XPath from document root |
| `tag_name` | string | HTML tag (lowercase) |
| `text` | string | Text content (trimmed) |
| `rect` | object | Bounding box with `x`, `y`, `width`, `height` |
| `computed_style` | object | 4 key CSS properties |
| `is_visible` | boolean | Visibility state at capture time |
| `z_index` | integer | Stacking order |
| `is_fixed` | boolean | True if element has `position: fixed` or `position: sticky` |
| `tile_index` | integer | Index of tile containing this element (tiled captures only) |
| `tile_relative_rect` | object | Original tile-relative position before coordinate adjustment (tiled captures only) |

### Fixed Element Detection

Elements with `position: fixed` or `position: sticky` CSS are marked with `is_fixed: true`. This helps identify elements that appear in multiple tiles (like sticky headers or floating navigation):

```json
{
  "tag_name": "nav",
  "text": "Home | Products | Contact",
  "is_fixed": true,
  "rect": {"x": 0, "y": 0, "width": 1920, "height": 60}
}
```

**Use case**: When processing tiled screenshots, filter out duplicates by checking `is_fixed`. Keep fixed elements only from the first tile to avoid counting them multiple times.

### Tiled Capture Metadata

When using `/screenshot/tiled`, each element includes tile metadata:

- **`tile_index`**: Which tile (0-based) this element was extracted from
- **`tile_relative_rect`**: The element's position within its tile (before coordinate adjustment)
- **`rect`**: Absolute full-page coordinates (tile offset already applied)

```json
{
  "tag_name": "p",
  "text": "Content in tile 2",
  "tile_index": 2,
  "tile_relative_rect": {"x": 100, "y": 200, "width": 300, "height": 20},
  "rect": {"x": 100, "y": 1768, "width": 300, "height": 20}
}
```

**Coordinate conversion**: `rect.y = tile_relative_rect.y + tile.bounds.y`

### Bounding Box

The `rect` object uses **viewport coordinates**:

- `x`: Distance from left edge of viewport
- `y`: Distance from top edge of viewport
- `width`: Element width in pixels
- `height`: Element height in pixels

For full-page screenshots, coordinates are relative to the full page, not the visible viewport.

### Computed Style

Four CSS properties are captured:

| Property | Example |
|----------|---------|
| `color` | `rgb(0, 0, 0)` |
| `backgroundColor` | `rgba(255, 255, 255, 1)` |
| `fontSize` | `16px` |
| `fontWeight` | `400` |

---

## Use Cases

### Vision AI Ground Truth

```python
# Capture screenshot + DOM
response = requests.post(
    "http://localhost:8000/screenshot/json",
    json={
        "url": "https://example.com",
        "extract_dom": {"enabled": True}
    }
)
data = response.json()

# Vision AI detects bounding box at (105, 48, 398, 30)
# Find matching DOM element
for el in data["dom_extraction"]["elements"]:
    if abs(el["rect"]["x"] - 105) < 10 and abs(el["rect"]["y"] - 48) < 10:
        print(f"Ground truth: {el['text']}")
```

### Accessibility Testing

```bash
# Extract all interactive elements
curl -X POST "http://localhost:8000/screenshot/json" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "extract_dom": {
      "enabled": true,
      "selectors": ["a", "button", "input", "[role=button]", "[tabindex]"]
    }
  }'
```

### Content Verification

```bash
# Check headline hierarchy
curl -X POST "http://localhost:8000/screenshot/json" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "extract_dom": {
      "enabled": true,
      "selectors": ["h1", "h2", "h3", "h4", "h5", "h6"]
    }
  }' | jq '.dom_extraction.elements[] | {tag: .tag_name, text: .text}'
```

### Vision AI Optimization

Get detailed metrics and Vision AI hints to optimize image sizing:

```bash
# Get quality metrics and Vision AI hints
curl -X POST "http://localhost:8000/screenshot/json" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "extract_dom": {
      "enabled": true,
      "include_metrics": true,
      "include_vision_hints": true,
      "target_vision_model": "claude"
    }
  }' | jq '{metrics: .dom_extraction.metrics, hints: .vision_hints}'
```

Example response with Vision AI hints:

```json
{
  "metrics": {
    "element_count": 47,
    "visible_count": 45,
    "visible_ratio": 0.957,
    "unique_tags": ["h1", "h2", "p", "a", "span"],
    "has_headings": true
  },
  "hints": {
    "image_width": 1920,
    "image_height": 1080,
    "claude_compatible": true,
    "gemini_compatible": true,
    "gpt4v_compatible": true,
    "tiling_recommended": false,
    "estimated_resize_factor": 1.0
  }
}
```

### Target Specific Vision Models

When targeting a specific Vision AI model, set `target_vision_model` to get optimized hints:

```bash
# Optimize for Claude Vision
curl -X POST "http://localhost:8000/screenshot/json" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "screenshot_type": "full_page",
    "extract_dom": {
      "enabled": true,
      "include_vision_hints": true,
      "target_vision_model": "claude"
    }
  }'
```

Model thresholds:

| Model | Max Dimension | Best For |
|-------|---------------|----------|
| `claude` | 1568px | General analysis, code review |
| `gemini` | 3072px | Large documents, dashboards |
| `gpt4v` | 2048px | Detailed image understanding |
| `qwen-vl-max` | 4096px | Very large screenshots |

---

## Performance

DOM extraction adds minimal overhead:

| Elements | Typical Time |
|----------|--------------|
| 50 | ~10ms |
| 100 | ~20ms |
| 500 | ~50ms |

Extraction happens in the same Playwright context as the screenshot, ensuring zero drift between pixels and coordinates.

---

## Troubleshooting

### No elements returned

1. Check `quality` field - if `empty`, the selectors didn't match
2. Verify page has loaded (add `wait_for_timeout`)
3. Try broader selectors (`["*"]` with low `max_elements`)

### Elements have wrong positions

1. Check `screenshot_type` - `full_page` uses page coordinates, not viewport
2. Verify no CSS transforms are affecting layout
3. Check `deviceScaleFactor` in viewport

### Hidden elements included

Set `include_hidden: false` (default) to exclude elements with:
- `visibility: hidden`
- `display: none`
- Zero dimensions
