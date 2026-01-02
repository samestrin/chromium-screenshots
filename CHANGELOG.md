# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.0] - 2026-01-02

### Added

#### Viewport Tiling for Vision AI (Sprint 6.0)
- **`/screenshot/tiled` endpoint** - Capture tall pages as multiple tiles optimized for Vision AI
- **Vision AI presets** - Pre-configured tile sizes for Claude (1568px), Gemini (3072px), GPT-4V (2048px)
- **Tile grid calculation** - Automatic optimal grid with configurable overlap
- **Coordinate mapping** - Transform Vision AI bounding boxes back to full-page coordinates
- **Per-tile DOM extraction** - Extract elements from each tile with adjusted coordinates
- **Fixed element detection** - Detect `position:fixed` and `position:sticky` elements
- **Lazy loading support** - Configurable per-tile wait for dynamic content

#### Enhanced Quality Metrics & Vision AI Optimization (Sprint 5.0)
- **QualityMetrics model** - Exposes 14+ computed values (element counts, visibility ratios, tag analysis, text statistics)
- **VisionAIHints model** - Model compatibility flags and tiling recommendations for Claude/Gemini/GPT-4V/Qwen
- **Opt-in request flags** - `include_metrics`, `include_vision_hints`, `target_vision_model`
- **JSON configuration** - `app/vision_model_config.json` for model profiles
- **Documentation** - `docs/vision-ai-optimization.md` guide

### Fixed
- CI workflow now properly installs Playwright system dependencies on Linux
- Added test timeouts to prevent CI hangs

## [1.4.0] - 2025-12-31

### Added
- `image_base64` field in `/screenshot/json` response for inline image data
- Version info in `/health` endpoint response

### Fixed
- Container renamed from `firefox` to `chromium` in docker-compose

### Documentation
- Added `/health` endpoint response documentation
- Added "Comparison with Alternatives" table to README

## [1.3.0] - 2025-12-29

### Added

#### DOM Extraction Quality Detection (Sprint 4.0)
- **Quality assessment engine** - Automatic detection of extraction quality (good/low/poor/empty)
- **Quality warnings** - Actionable warnings for common issues (few elements, many hidden, no headings)
- **ExtractionQuality enum** - Structured quality levels
- **QualityWarning model** - Detailed warning messages with severity

### Documentation
- Complete API reference (`docs/api-reference.md`)
- DOM extraction guide (`docs/dom-extraction.md`)
- Quality assessment guide (`docs/quality-assessment.md`)
- MCP server documentation (`docs/mcp-server.md`)

## [1.2.0] - 2025-12-27

### Added

#### DOM-Enhanced Screenshot (Sprint 3.0)
- **`/screenshot/json` endpoint** - Returns screenshot with DOM extraction data
- **DOM extraction** - Extract text and bounding boxes from rendered pages
- **Zero-drift capture** - Screenshot and DOM extracted from same render frame
- **Configurable selectors** - Target specific elements with CSS selectors
- **Computed styles** - Color, background, font-size, font-weight for each element
- **Element visibility** - Track `is_visible` and `z_index` for each element

## [1.1.1] - 2025-12-25

### Added

#### localStorage and sessionStorage Support (Sprint 2.0)
- **localStorage injection** - Pre-populate localStorage before page load
- **sessionStorage injection** - Pre-populate sessionStorage before page load
- Auth token injection for SPA frameworks (Wasp, Firebase, Supabase)

#### Cookie Support (Sprint 1.0)
- **Cookie injection** - Set cookies before navigation
- **Domain inference** - Automatic domain detection from URL
- **Full cookie attributes** - path, httpOnly, secure, sameSite, expires

## [1.1.0] - 2025-12-20

### Added

- **MCP Server Support**: New Model Context Protocol server for AI agent integration
  - `screenshot` tool: Capture screenshots and return base64-encoded image data
  - `screenshot_to_file` tool: Capture screenshots and save directly to disk
  - Lazy browser initialization for fast startup
  - Graceful shutdown with resource cleanup
- `pyproject.toml` for modern Python packaging
- Optional dependency groups: `api`, `mcp`, `all`, `dev`
- `chromium-screenshots-mcp` CLI entry point for running the MCP server
- `requirements-mcp.txt` for MCP-specific dependencies
- `screenshot_mcp/` package (named to avoid collision with `mcp` package)

### Changed

- Project now supports dual interfaces: HTTP API and MCP server
- Core screenshot logic (`app/screenshot.py`) shared between both interfaces

## [1.0.0] - 2025-12-20

### Added

- Initial release
- FastAPI-based HTTP screenshot service
- Chromium/Playwright browser automation
- Viewport and full-page screenshot capture
- PNG and JPEG output formats with quality control
- Dark mode emulation
- Ad/tracking domain blocking
- Wait controls: timeout, selector, delay
- Docker and Docker Compose support
- Kubernetes deployment manifests
- Health check endpoint for container orchestration
- GET endpoint with query parameters for simple usage
- POST endpoints for full control and metadata-only responses

[Unreleased]: https://github.com/samestrin/chromium-screenshots/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/samestrin/chromium-screenshots/compare/v1.4.0...v2.0.0
[1.4.0]: https://github.com/samestrin/chromium-screenshots/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/samestrin/chromium-screenshots/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/samestrin/chromium-screenshots/compare/v1.1.1...v1.2.0
[1.1.1]: https://github.com/samestrin/chromium-screenshots/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/samestrin/chromium-screenshots/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/samestrin/chromium-screenshots/releases/tag/v1.0.0
