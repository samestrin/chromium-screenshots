# Screenshot API

A fast, containerized screenshot service using Chrome (Chromium via Playwright) with support for viewport and full-page captures. Available as both an HTTP API and an MCP server for AI agent integration.

## Features

- **Chrome-based**: Uses Chromium for fast, reliable headless rendering
- **Viewport & Full-page**: Capture visible area or entire scrollable page
- **Multiple formats**: PNG and JPEG output with quality control
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
docker build -t screenshot-api .

# Run the container
docker run -d \
  --name screenshot-api \
  -p 8000:8000 \
  --memory=2g \
  screenshot-api
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

### Response Headers

Successful responses include these headers:
- `X-Capture-Time-Ms`: Time taken to capture (ms)
- `X-Screenshot-Type`: viewport or full_page
- `Content-Disposition`: Suggested filename

## MCP Server (AI Agent Integration)

The screenshot service can also run as an MCP (Model Context Protocol) server, allowing AI agents like Claude Code to capture screenshots directly.

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

Capture a screenshot and return base64-encoded image data.

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
```

#### `screenshot_to_file`

Capture a screenshot and save it to disk.

```
Parameters:
- url (required): URL to capture
- output_path (required): Path to save the screenshot
- (all other parameters same as screenshot)
```

### Why MCP?

- **No HTTP overhead**: Direct in-process capture
- **AI-native**: Designed for Claude Code and other AI agents
- **Handles edge cases**: Long pages, custom dimensions that block other tools
- **Simple setup**: One config entry, works immediately

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
  name: screenshot-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: screenshot-api
  template:
    metadata:
      labels:
        app: screenshot-api
    spec:
      containers:
      - name: screenshot-api
        image: screenshot-api:latest
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
  name: screenshot-api
spec:
  selector:
    app: screenshot-api
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
docker run --memory=4g screenshot-api
```

### Slow captures

- Reduce viewport size for faster rendering
- Use JPEG format with lower quality for smaller files
- Enable `block_ads` to reduce network requests

## License

MIT
