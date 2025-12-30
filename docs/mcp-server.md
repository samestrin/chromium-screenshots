# MCP Server

> Model Context Protocol server for AI agent integration.

The MCP server allows AI tools like Claude Desktop to capture screenshots directly. It provides the same capabilities as the REST API through the standardized MCP protocol.

---

## Quick Start

### With Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

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

### Standalone

```bash
cd /path/to/chromium-screenshots
python -m screenshot_mcp.server
```

---

## Available Tools

### screenshot

Capture a screenshot and return base64-encoded image data.

**Input Schema:**

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
  "extract_dom": {
    "enabled": true,
    "selectors": ["h1", "p"],
    "max_elements": 100
  }
}
```

**Output:**

Returns text containing:
- Capture metadata (format, size, time)
- DOM extraction results (if enabled)
- Base64 image data
- DOM elements as JSON (if enabled)

### screenshot_to_file

Capture a screenshot and save it to a file.

**Input Schema:**

```json
{
  "url": "https://example.com",
  "output_path": "~/screenshots/capture.png",
  "screenshot_type": "viewport",
  "format": "png"
}
```

**Output:**

Returns text with:
- File path where screenshot was saved
- Capture metadata
- DOM extraction results (if enabled)

---

## Parameters

All parameters from the REST API are supported:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | string | *required* | URL to capture |
| `output_path` | string | *required for file* | Save path (file tool only) |
| `screenshot_type` | string | `viewport` | `viewport` or `full_page` |
| `format` | string | `png` | `png` or `jpeg` |
| `width` | integer | 1920 | Viewport width (320-3840) |
| `height` | integer | 1080 | Viewport height (240-2160) |
| `quality` | integer | 90 | JPEG quality (1-100) |
| `wait_for_timeout` | integer | 0 | Wait after load (0-30000ms) |
| `wait_for_selector` | string | null | CSS selector to wait for |
| `delay` | integer | 0 | Delay before capture (0-10000ms) |
| `dark_mode` | boolean | false | Dark color scheme |
| `block_ads` | boolean | false | Block ad domains |
| `cookies` | array | null | Cookies to inject |
| `localStorage` | object | null | localStorage pairs |
| `sessionStorage` | object | null | sessionStorage pairs |
| `extract_dom` | object | null | DOM extraction options |

### Cookie Format

```json
{
  "cookies": [
    {
      "name": "session_id",
      "value": "abc123",
      "domain": ".example.com",
      "path": "/",
      "httpOnly": true,
      "secure": true,
      "sameSite": "Lax"
    }
  ]
}
```

### DOM Extraction Format

```json
{
  "extract_dom": {
    "enabled": true,
    "selectors": ["h1", "h2", "p", "a"],
    "include_hidden": false,
    "min_text_length": 1,
    "max_elements": 500
  }
}
```

---

## Usage Examples

### Claude Desktop Prompts

**Basic Screenshot:**
> Take a screenshot of https://news.ycombinator.com

**Authenticated Dashboard:**
> Take a screenshot of https://app.example.com/dashboard with these cookies: session_id=abc123

**DOM Extraction:**
> Capture https://example.com with DOM extraction enabled. Show me all the headings.

**Save to File:**
> Save a screenshot of https://github.com to ~/Desktop/github.png

---

## Output Format

### screenshot Tool Response

```
Screenshot captured successfully.
Format: png
Size: 145,832 bytes
Capture time: 1234.56ms
Dimensions: 1920x1080
Type: viewport

DOM Extraction:
  Elements: 47
  Quality: good
  Extraction time: 23.45ms
  Warnings:
    - [NO_HEADINGS] No heading elements (h1-h6) found.

Base64 image data:
iVBORw0KGgoAAAANSUhEUgAA...

DOM Elements (JSON):
{
  "elements": [...],
  "viewport": {"width": 1920, "height": 1080},
  "element_count": 47,
  "quality": "good",
  "warnings": []
}
```

### screenshot_to_file Tool Response

```
Screenshot saved successfully.
Path: /Users/you/screenshots/capture.png
Format: png
Size: 145,832 bytes
Capture time: 1234.56ms
Dimensions: 1920x1080
Type: viewport
```

---

## Requirements

- Python 3.11+
- Playwright with Chromium
- MCP Python SDK

### Installation

```bash
pip install -r requirements.txt
playwright install chromium
```

---

## Troubleshooting

### Server not starting

1. Verify Python path in Claude Desktop config
2. Check `cwd` points to project root
3. Ensure dependencies are installed

### Tool not appearing

1. Restart Claude Desktop after config changes
2. Check Claude Desktop logs for errors
3. Verify JSON config syntax

### Screenshots timing out

1. Use `wait_for_timeout` for slow pages
2. Check network connectivity
3. Verify URL is accessible

### Cookie injection not working

1. Set correct `domain` for cookies
2. Use `secure: true` for HTTPS sites
3. Check `sameSite` policy matches site requirements
