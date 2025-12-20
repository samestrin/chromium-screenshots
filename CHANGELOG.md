# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
