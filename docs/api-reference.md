# API Reference

> Full parameter and response documentation for the chromium-screenshots API.

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/screenshot` | GET | Quick capture via query params |
| `/screenshot` | POST | Full control via JSON body |
| `/screenshot/json` | POST | Returns metadata + base64 image |
| `/health` | GET | Service health check |
| `/docs` | GET | Swagger UI |
| `/redoc` | GET | ReDoc UI |

---

## GET /health

Service health check endpoint for container orchestration.

### Response

```json
{
  "status": "healthy",
  "version": "1.2.0",
  "browser": "chromium"
}
```

| Field | Description |
|-------|-------------|
| `status` | `healthy` when browser is available |
| `version` | Current API version from pyproject.toml |
| `browser` | Browser engine (`chromium`) |

Returns `503 Service Unavailable` if browser is not available.

---

## POST /screenshot

Full-featured screenshot capture with JSON body.

### Request Body

```json
{
  "url": "https://example.com",
  "screenshot_type": "viewport",
  "format": "png",
  "width": 1920,
  "height": 1080,
  "quality": 90,
  "wait_for_timeout": 0,
  "wait_for_selector": ".content",
  "delay": 0,
  "dark_mode": false,
  "block_ads": false,
  "cookies": [],
  "localStorage": {},
  "sessionStorage": {},
  "extract_dom": {}
}
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | string | *required* | URL to capture (must include protocol) |
| `screenshot_type` | string | `viewport` | `viewport` or `full_page` |
| `format` | string | `png` | `png` or `jpeg` |
| `width` | integer | 1920 | Viewport width (320-3840) |
| `height` | integer | 1080 | Viewport height (240-2160) |
| `quality` | integer | 90 | JPEG quality (1-100, ignored for PNG) |
| `wait_for_timeout` | integer | 0 | Extra wait after load (0-30000ms) |
| `wait_for_selector` | string | null | CSS selector to wait for |
| `delay` | integer | 0 | Delay before capture (0-10000ms) |
| `dark_mode` | boolean | false | Emulate dark color scheme |
| `block_ads` | boolean | false | Block common ad domains |
| `cookies` | array | null | Cookies to inject ([Cookie](#cookie-object)) |
| `localStorage` | object | null | localStorage key-value pairs |
| `sessionStorage` | object | null | sessionStorage key-value pairs |
| `extract_dom` | object | null | DOM extraction options ([DomExtractionOptions](#domextractionoptions)) |

### Response

Returns the screenshot image directly with headers:

| Header | Description |
|--------|-------------|
| `Content-Type` | `image/png` or `image/jpeg` |
| `X-Capture-Time-Ms` | Capture time in milliseconds |
| `X-Screenshot-Type` | `viewport` or `full_page` |

---

## POST /screenshot/json

Returns JSON metadata with base64-encoded image.

### Response Body

```json
{
  "success": true,
  "url": "https://example.com",
  "screenshot_type": "viewport",
  "format": "png",
  "width": 1920,
  "height": 1080,
  "file_size_bytes": 145832,
  "capture_time_ms": 1234.56,
  "image_base64": "iVBORw0KGgo...",
  "dom_extraction": {}
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Always `true` on success |
| `url` | string | Captured URL |
| `screenshot_type` | string | `viewport` or `full_page` |
| `format` | string | `png` or `jpeg` |
| `width` | integer | Viewport width |
| `height` | integer | Viewport height |
| `file_size_bytes` | integer | Image size in bytes |
| `capture_time_ms` | float | Total capture time |
| `image_base64` | string | Base64-encoded image data |
| `dom_extraction` | object | DOM extraction result (if enabled) |

---

## GET /screenshot

Quick capture via query parameters.

### Example

```bash
curl "http://localhost:8000/screenshot?url=https://example.com&width=1280&format=jpeg" -o screenshot.jpg
```

### Query Parameters

Same as POST body parameters, but as query string.

---

## Object Schemas

### Cookie Object

```json
{
  "name": "session_id",
  "value": "abc123",
  "domain": ".example.com",
  "path": "/",
  "httpOnly": true,
  "secure": true,
  "sameSite": "Lax",
  "expires": 1735689600
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Cookie name |
| `value` | string | Yes | Cookie value |
| `domain` | string | No | Cookie domain (inferred from URL if not set) |
| `path` | string | No | Cookie path (defaults to `/`) |
| `httpOnly` | boolean | No | HTTP-only flag |
| `secure` | boolean | No | Secure flag (HTTPS only) |
| `sameSite` | string | No | `Strict`, `Lax`, or `None` |
| `expires` | integer | No | Unix timestamp expiration |

### DomExtractionOptions

See [DOM Extraction](dom-extraction.md) for full details.

```json
{
  "enabled": true,
  "selectors": ["h1", "h2", "p", "a"],
  "include_hidden": false,
  "min_text_length": 1,
  "max_elements": 500,
  "include_metrics": false,
  "include_vision_hints": false,
  "target_vision_model": null
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | boolean | false | Enable DOM extraction |
| `selectors` | array | (see below) | CSS selectors to extract |
| `include_hidden` | boolean | false | Include hidden elements |
| `min_text_length` | integer | 1 | Minimum text length |
| `max_elements` | integer | 500 | Maximum elements to return |
| `include_metrics` | boolean | false | Include detailed [QualityMetrics](#qualitymetrics) |
| `include_vision_hints` | boolean | false | Include [VisionAIHints](#visionaihints) for AI optimization |
| `target_vision_model` | string | null | Target model: `claude`, `gemini`, `gpt4v`, `qwen-vl-max` |

**Default selectors:**
```
h1, h2, h3, h4, h5, h6, p, span, a, li, button, label,
td, th, caption, figcaption, blockquote
```

### QualityMetrics

Detailed quality metrics returned when `include_metrics: true`.

```json
{
  "element_count": 47,
  "visible_count": 45,
  "hidden_count": 2,
  "heading_count": 5,
  "unique_tag_count": 8,
  "visible_ratio": 0.957,
  "hidden_ratio": 0.043,
  "unique_tags": ["h1", "h2", "p", "a", "span", "li", "button", "label"],
  "has_headings": true,
  "tag_distribution": {"h1": 1, "h2": 4, "p": 15, "a": 12, "span": 8, "li": 5, "button": 1, "label": 1},
  "total_text_length": 2847,
  "avg_text_length": 60.6,
  "min_text_length": 3,
  "max_text_length": 256
}
```

| Field | Type | Description |
|-------|------|-------------|
| `element_count` | integer | Total elements extracted |
| `visible_count` | integer | Visible elements (not hidden via CSS) |
| `hidden_count` | integer | Hidden elements (display:none or visibility:hidden) |
| `heading_count` | integer | Number of heading elements (h1-h6) |
| `unique_tag_count` | integer | Count of unique HTML tag types |
| `visible_ratio` | float | Ratio of visible elements (0.0 to 1.0) |
| `hidden_ratio` | float | Ratio of hidden elements (0.0 to 1.0) |
| `unique_tags` | array | List of unique HTML tag names |
| `has_headings` | boolean | Whether any headings (h1-h6) were found |
| `tag_distribution` | object | Count of each tag type |
| `total_text_length` | integer | Total character count of all text |
| `avg_text_length` | float | Average text length per element |
| `min_text_length` | integer | Minimum text length among elements |
| `max_text_length` | integer | Maximum text length among elements |

### VisionAIHints

Vision AI optimization hints returned when `include_vision_hints: true`. See the [Vision AI Optimization Guide](vision-ai-optimization.md) for detailed usage.

```json
{
  "image_width": 1920,
  "image_height": 1080,
  "image_size_bytes": 145832,
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
```

| Field | Type | Description |
|-------|------|-------------|
| `image_width` | integer | Image width in pixels |
| `image_height` | integer | Image height in pixels |
| `image_size_bytes` | integer | Image file size in bytes |
| `document_width` | integer | Full document width (for full_page screenshots) |
| `document_height` | integer | Full document height (for full_page screenshots) |
| `claude_compatible` | boolean | Compatible with Claude Vision (max 1568px) |
| `gemini_compatible` | boolean | Compatible with Gemini Vision (max 3072px) |
| `gpt4v_compatible` | boolean | Compatible with GPT-4V (max 2048px) |
| `qwen_compatible` | boolean | Compatible with Qwen-VL (max 4096px) |
| `estimated_resize_factor` | float | Resize factor for target model (1.0 = no resize) |
| `coordinate_accuracy` | float | Coordinate accuracy after resize (1.0 = full) |
| `resize_impact_claude` | float | Detail loss % if resized for Claude |
| `resize_impact_gemini` | float | Detail loss % if resized for Gemini |
| `resize_impact_gpt4v` | float | Detail loss % if resized for GPT-4V |
| `resize_impact_qwen` | float | Detail loss % if resized for Qwen-VL |
| `recommended_width` | integer | Optimal width for target model (null if no resize needed) |
| `recommended_height` | integer | Optimal height for target model (null if no resize needed) |
| `tiling_recommended` | boolean | Whether tiling is recommended |
| `suggested_tile_count` | integer | Suggested number of tiles |
| `suggested_tile_size` | object | Suggested tile dimensions `{width, height}` |
| `tile_overlap_percent` | float | Tile overlap percentage (default 15%) |
| `tiling_reason` | string | Reason for tiling recommendation |

**Model Thresholds:**

| Model | Max Dimension | Max Pixels | Max Aspect Ratio |
|-------|---------------|------------|------------------|
| Claude | 1568px | ~2.5M | 4:1 |
| GPT-4V | 2048px | ~4.2M | 4:1 |
| Gemini | 3072px | ~9.4M | 5:1 |
| Qwen-VL | 4096px | ~16.8M | 6:1 |

**Environment Variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `VISION_CLAUDE_MAX_DIMENSION` | 1568 | Claude Vision max dimension |
| `VISION_GEMINI_MAX_DIMENSION` | 3072 | Gemini Vision max dimension |
| `VISION_GPT4V_MAX_DIMENSION` | 2048 | GPT-4V max dimension |
| `VISION_QWEN_VL_MAX_MAX_DIMENSION` | 4096 | Qwen-VL max dimension |
| `VISION_DEFAULT_MODEL` | claude | Default target model |
| `VISION_TILE_OVERLAP_PERCENT` | 15 | Tile overlap percentage |

---

## Error Responses

```json
{
  "success": false,
  "error": "Invalid URL",
  "detail": "URL must include protocol (http:// or https://)"
}
```

| Status | Description |
|--------|-------------|
| 400 | Bad request (invalid parameters) |
| 422 | Validation error (Pydantic) |
| 500 | Server error (capture failed) |
| 504 | Timeout (page took too long) |
