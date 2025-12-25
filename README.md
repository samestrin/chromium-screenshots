# Chromium Screenshots

A fast, containerized screenshot service using Chromium (via Playwright) with support for viewport and full-page captures. Available as both an **HTTP API and an MCP server** for AI agent integration.

**Repository:** [github.com/samestrin/chromium-screenshots](https://github.com/samestrin/chromium-screenshots)

## Features

- **Chrome-based**: Uses Chromium for fast, reliable headless rendering
- **Viewport & Full-page**: Capture visible area or entire scrollable page
- **Multiple formats**: PNG and JPEG output with quality control
- **Cookie injection**: Capture authenticated pages with session cookies
- **localStorage/sessionStorage injection**: Capture authenticated SPA pages (Wasp, OpenSaaS, Firebase, etc.)
- **Dark mode**: Emulate dark color scheme preference
- **Ad blocking**: Optional blocking of common ad/tracking domains
- **Wait controls**: Wait for page load, specific selectors, or custom delays
- **Docker-ready**: Production-ready container with health checks
- **MCP Server**: Model Context Protocol support for AI agents (Claude Code, etc.)

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Build and start the service
docker compose up -d

# Check logs
docker compose logs -f

# Stop the service
docker compose down
```

### Using Docker directly

```bash
# Build the image
docker build -t chromium-screenshots .

# Run the container
docker run -d \
  --name chromium-screenshots \
  -p 8000:8000 \
  --memory=2g \
  chromium-screenshots
```

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Install Chromium browser
playwright install chromium

# Run the server
uvicorn app.main:app --reload
```

## API Usage

### Interactive Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Endpoints

#### GET /screenshot (Simple)

Quick screenshots via query parameters:

```bash
# Basic viewport screenshot
curl "http://localhost:8000/screenshot?url=https://example.com" -o screenshot.png

# Full-page screenshot
curl "http://localhost:8000/screenshot?url=https://example.com&type=full_page" -o full.png

# Custom viewport with dark mode
curl "http://localhost:8000/screenshot?url=https://github.com&width=1280&height=720&dark=true" -o github.png

# JPEG with quality setting
curl "http://localhost:8000/screenshot?url=https://example.com&format=jpeg&quality=85" -o screenshot.jpg

# Screenshot with cookies for authenticated pages
curl "http://localhost:8000/screenshot?url=https://dashboard.example.com&cookies=session=abc123;auth=token456" -o dashboard.png

# Screenshot with localStorage for SPA authentication (Wasp, Firebase, etc.)
curl "http://localhost:8000/screenshot?url=https://app.example.com/dashboard&localStorage=wasp:sessionId=abc123;theme=dark" -o spa-dashboard.png

# Screenshot with both cookies and localStorage
curl "http://localhost:8000/screenshot?url=https://app.example.com&cookies=tracking=xyz&localStorage=authToken=secret123" -o authenticated.png
```

#### POST /screenshot (Full Control)

Full control via JSON body:

```bash
curl -X POST "http://localhost:8000/screenshot" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "screenshot_type": "full_page",
    "format": "png",
    "width": 1920,
    "height": 1080,
    "wait_for_timeout": 2000,
    "dark_mode": true,
    "block_ads": true
  }' \
  -o screenshot.png

# With cookies for authenticated pages
curl -X POST "http://localhost:8000/screenshot" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://dashboard.example.com",
    "cookies": [
      {"name": "session", "value": "abc123"},
      {"name": "auth", "value": "token456", "httpOnly": true, "secure": true}
    ]
  }' \
  -o authenticated.png

# With localStorage for SPA authentication (Wasp, OpenSaaS, Firebase)
curl -X POST "http://localhost:8000/screenshot" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://app.example.com/dashboard",
    "localStorage": {
      "wasp:sessionId": "ic3t2fnhclk3pe46zu3d5ml5dnx5ng3u5fbh7h23",
      "color-theme": "dark"
    }
  }' \
  -o spa-authenticated.png

# With combined cookies + localStorage + sessionStorage
curl -X POST "http://localhost:8000/screenshot" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://app.example.com/dashboard",
    "cookies": [{"name": "tracking", "value": "xyz"}],
    "localStorage": {"wasp:sessionId": "abc123"},
    "sessionStorage": {"temp-data": "form-state"}
  }' \
  -o full-auth.png
```

#### POST /screenshot/json (Metadata Only)

Get capture metadata without the image:

```bash
curl -X POST "http://localhost:8000/screenshot/json" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "screenshot_type": "full_page"}'
```

Response:
```json
{
  "success": true,
  "url": "https://example.com",
  "screenshot_type": "full_page",
  "format": "png",
  "width": 1920,
  "height": 1080,
  "file_size_bytes": 245678,
  "capture_time_ms": 2345.67
}
```

#### GET /health

Health check for container orchestration:

```bash
curl http://localhost:8000/health
```

### Request Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | string | required | URL to capture |
| `screenshot_type` | string | `viewport` | `viewport` or `full_page` |
| `format` | string | `png` | `png` or `jpeg` |
| `width` | int | 1920 | Viewport width (320-3840) |
| `height` | int | 1080 | Viewport height (240-2160) |
| `quality` | int | 90 | JPEG quality (1-100) |
| `wait_for_timeout` | int | 0 | Wait after load in ms (0-30000) |
| `wait_for_selector` | string | null | CSS selector to wait for |
| `delay` | int | 0 | Delay before capture in ms (0-10000) |
| `dark_mode` | bool | false | Emulate dark color scheme |
| `block_ads` | bool | false | Block common ad domains |
| `cookies` | array/string | null | Cookies to inject (see below) |
| `localStorage` | object/string | null | localStorage to inject (see below) |
| `sessionStorage` | object/string | null | sessionStorage to inject (see below) |

### Cookie Parameters

For authenticated pages, you can inject session cookies using either format:

**GET (query string format):**
```
cookies=name=value;name2=value2
```

**POST (JSON array format):**
```json
{
  "cookies": [
    {"name": "session", "value": "abc123"},
    {"name": "auth", "value": "token456", "domain": "example.com", "httpOnly": true}
  ]
}
```

**Cookie object fields:**
| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Cookie name |
| `value` | Yes | Cookie value |
| `domain` | No | Cookie domain (inferred from URL if not specified) |
| `path` | No | Cookie path |
| `httpOnly` | No | HTTP-only flag |
| `secure` | No | Secure flag |
| `sameSite` | No | "Strict", "Lax", or "None" |
| `expires` | No | Unix timestamp for expiration |

### Storage Parameters (localStorage/sessionStorage)

For SPAs using localStorage-based authentication (Wasp, OpenSaaS, Firebase, etc.), you can inject storage values:

**GET (query string format):**
```
localStorage=key=value;key2=value2
sessionStorage=tempKey=tempValue
```

**POST (JSON object format):**
```json
{
  "localStorage": {
    "wasp:sessionId": "abc123",
    "user-preferences": "{\"theme\":\"dark\",\"lang\":\"en\"}"
  },
  "sessionStorage": {
    "temp-form-data": "draft-content"
  }
}
```

**How it works:**
1. Browser navigates to the target origin first
2. Storage values are injected via JavaScript
3. Browser navigates to the full target URL
4. Page loads with authentication in place
5. Screenshot is captured

**Performance note:** Storage injection adds ~500ms due to the two-step navigation required (origin → inject → target URL).

**Security notes:**
- Each request uses a fresh browser context (no storage persistence between requests)
- Storage values are never logged
- Storage is origin-scoped (browser-enforced security)

### Response Headers

Successful responses include these headers:
- `X-Capture-Time-Ms`: Time taken to capture (ms)
- `X-Screenshot-Type`: viewport or full_page
- `Content-Disposition`: Suggested filename

## MCP Server (AI Agent Integration)

The screenshot service can also run as an MCP (Model Context Protocol) server, allowing AI agents like Claude Code to capture screenshots directly.

### When to Use MCP vs HTTP API

| Approach | Best For | Context Impact |
|----------|----------|----------------|
| **HTTP API (Recommended)** | Production workflows, automated testing, bulk captures | **Minimal** - images save to disk |
| **MCP `screenshot_to_file`** | AI agent workflows needing file output | **Minimal** - images save to disk |
| **MCP `screenshot`** | Quick previews, one-off captures | **High** - base64 data in context |

**Context Warning:** The MCP `screenshot` tool returns base64-encoded image data directly in the response. A single full-page screenshot can easily exceed 500KB+ of base64 text, which will rapidly consume your AI agent's context window. For most AI agent workflows, use one of these context-friendly approaches:

1. **HTTP API via curl/fetch** (best for automated workflows):
   ```bash
   curl "http://localhost:8000/screenshot?url=https://example.com" -o screenshot.png
   ```

2. **MCP `screenshot_to_file`** (best for AI agent file-based workflows):
   ```
   screenshot_to_file(url="https://example.com", output_path="./screenshot.png")
   ```

Both approaches save images to disk rather than loading them into context, making them suitable for capturing multiple screenshots without context overflow.

### Installation

```bash
# Install with MCP support
pip install chromium-screenshots[mcp]

# Or install all features
pip install chromium-screenshots[all]

# Install Chromium browser
playwright install chromium
```

### Claude Code Configuration

Add to your Claude Code MCP settings (`~/.claude/settings.json`):

```json
{
  "mcpServers": {
    "chromium-screenshots": {
      "command": "chromium-screenshots-mcp",
      "args": []
    }
  }
}
```

Or if running from source:

```json
{
  "mcpServers": {
    "chromium-screenshots": {
      "command": "python",
      "args": ["-m", "screenshot_mcp.server"],
      "cwd": "/path/to/chromium-screenshots"
    }
  }
}
```

### Available Tools

#### `screenshot`

Capture a screenshot and return base64-encoded image data. Supports cookie and storage injection for authenticated pages.

```
Parameters:
- url (required): URL to capture
- screenshot_type: "viewport" or "full_page" (default: viewport)
- format: "png" or "jpeg" (default: png)
- width: Viewport width, 320-3840 (default: 1920)
- height: Viewport height, 240-2160 (default: 1080)
- quality: JPEG quality, 1-100 (default: 90)
- wait_for_timeout: Wait after load in ms (default: 0)
- wait_for_selector: CSS selector to wait for
- delay: Delay before capture in ms (default: 0)
- dark_mode: Emulate dark mode (default: false)
- block_ads: Block ad domains (default: false)
- cookies: Array of cookie objects [{name, value, domain?, ...}]
- localStorage: Object of key-value pairs to inject into localStorage
- sessionStorage: Object of key-value pairs to inject into sessionStorage
```

#### `screenshot_to_file`

Capture a screenshot and save it to disk. Supports cookie and storage injection for authenticated pages.

```
Parameters:
- url (required): URL to capture
- output_path (required): Path to save the screenshot
- cookies: Array of cookie objects [{name, value, domain?, ...}]
- localStorage: Object of key-value pairs to inject into localStorage
- sessionStorage: Object of key-value pairs to inject into sessionStorage
- (all other parameters same as screenshot)
```

### Why MCP?

The MCP server is useful when:
- You need AI agents to capture screenshots without setting up HTTP infrastructure
- You want `screenshot_to_file` for context-efficient file-based captures
- You need to handle edge cases like long pages or custom dimensions that block other screenshot tools
- You prefer simple setup (one config entry) over running a separate HTTP service

**Note:** For bulk screenshot operations or automated testing pipelines, the HTTP API is generally more efficient and doesn't require MCP client support.

## Deployment

### Production Considerations

1. **Resource Limits**: Chromium needs memory. Allocate at least 512MB, recommend 2GB.

2. **Scaling**: For high throughput, run multiple containers behind a load balancer.

3. **Security**: The container runs as non-root. Consider network policies to restrict outbound traffic.

4. **Timeouts**: Default page timeout is 30 seconds. Adjust based on your needs.

### Kubernetes Example

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chromium-screenshots
spec:
  replicas: 3
  selector:
    matchLabels:
      app: chromium-screenshots
  template:
    metadata:
      labels:
        app: chromium-screenshots
    spec:
      containers:
      - name: chromium-screenshots
        image: chromium-screenshots:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 15
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: chromium-screenshots
spec:
  selector:
    app: chromium-screenshots
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `UVICORN_WORKERS` | 1 | Number of worker processes |

## Architecture

```
chromium-screenshots/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI HTTP API
│   ├── models.py        # Pydantic request/response models
│   └── screenshot.py    # Core Playwright screenshot service
├── screenshot_mcp/
│   ├── __init__.py
│   └── server.py        # MCP server wrapper
├── Dockerfile           # Container definition
├── docker-compose.yml   # Docker Compose config
├── pyproject.toml       # Python package configuration
├── requirements.txt     # HTTP API dependencies
├── requirements-mcp.txt # MCP server dependencies
├── CHANGELOG.md         # Version history
└── README.md
```

```
                  ┌─────────────────────────┐
                  │   app/screenshot.py     │
                  │   (core capture logic)  │
                  └───────────┬─────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
              ▼                               ▼
      ┌───────────────┐               ┌───────────────┐
      │  app/main.py  │               │screenshot_mcp/│
      │  (HTTP API)   │               │ (MCP server)  │
      └───────────────┘               └───────────────┘
              │                               │
              ▼                               ▼
         curl/fetch                      Claude Code
         browsers                        AI agents
```

### Technology Stack

- **Python 3.12**: Runtime
- **FastAPI**: Web framework
- **Playwright**: Browser automation
- **Chromium**: Browser engine (faster headless performance than Firefox)
- **Uvicorn**: ASGI server

### Why Chrome/Chromium?

- **Faster headless mode**: Optimized for automation workloads
- **Lower memory footprint**: More efficient than Firefox in containers
- **Better community support**: Most automation examples use Chrome
- **Native Playwright support**: Well-tested integration

## Troubleshooting

### Container won't start

Check if port 8000 is available:
```bash
lsof -i :8000
```

### Screenshots are blank

Some sites block headless browsers. Try:
- Adding a `wait_for_timeout` of 2000-5000ms
- Using a `wait_for_selector` for a key element

### Out of memory errors

Increase container memory limit:
```bash
docker run --memory=4g chromium-screenshots
```

### Slow captures

- Reduce viewport size for faster rendering
- Use JPEG format with lower quality for smaller files
- Enable `block_ads` to reduce network requests

## License

MIT
