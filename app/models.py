"""Pydantic models for screenshot requests and responses."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class ScreenshotType(str, Enum):
    """Screenshot capture type."""

    VIEWPORT = "viewport"
    FULL_PAGE = "full_page"


class ImageFormat(str, Enum):
    """Output image format."""

    PNG = "png"
    JPEG = "jpeg"


class ScreenshotRequest(BaseModel):
    """Request model for screenshot capture."""

    url: HttpUrl = Field(..., description="URL to capture")
    screenshot_type: ScreenshotType = Field(
        default=ScreenshotType.VIEWPORT,
        description="Type of screenshot: viewport (visible area) or full_page (entire page)",
    )
    format: ImageFormat = Field(
        default=ImageFormat.PNG, description="Output image format"
    )
    width: int = Field(
        default=1920, ge=320, le=3840, description="Viewport width in pixels"
    )
    height: int = Field(
        default=1080, ge=240, le=2160, description="Viewport height in pixels"
    )
    quality: int = Field(
        default=90,
        ge=1,
        le=100,
        description="Image quality (1-100, only applies to JPEG)",
    )
    wait_for_timeout: int = Field(
        default=0,
        ge=0,
        le=30000,
        description="Additional wait time in ms after page load (0-30000)",
    )
    wait_for_selector: Optional[str] = Field(
        default=None, description="CSS selector to wait for before capture"
    )
    delay: int = Field(
        default=0,
        ge=0,
        le=10000,
        description="Delay in ms before taking screenshot (0-10000)",
    )
    dark_mode: bool = Field(
        default=False, description="Emulate dark color scheme preference"
    )
    block_ads: bool = Field(
        default=False, description="Block common ad domains"
    )


class ScreenshotResponse(BaseModel):
    """Response model for successful screenshot."""

    success: bool = True
    url: str
    screenshot_type: ScreenshotType
    format: ImageFormat
    width: int
    height: int
    file_size_bytes: int
    capture_time_ms: float


class ErrorResponse(BaseModel):
    """Response model for errors."""

    success: bool = False
    error: str
    detail: Optional[str] = None
