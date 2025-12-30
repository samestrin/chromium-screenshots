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
| `X-Capture-Time` | Capture time in ms |
| `X-Quality` | Extraction quality (if `extract_dom` enabled) |

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
  "max_elements": 500
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | boolean | false | Enable DOM extraction |
| `selectors` | array | (see below) | CSS selectors to extract |
| `include_hidden` | boolean | false | Include hidden elements |
| `min_text_length` | integer | 1 | Minimum text length |
| `max_elements` | integer | 500 | Maximum elements to return |

**Default selectors:**
```
h1, h2, h3, h4, h5, h6, p, span, a, li, button, label,
td, th, caption, figcaption, blockquote
```

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
