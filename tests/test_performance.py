"""Performance tests for DOM extraction.

Phase 4: Validation tests to ensure DOM extraction meets <100ms target.
"""

import pytest


class TestDomExtractionPerformance:
    """Test DOM extraction performance meets targets."""

    @pytest.mark.asyncio
    async def test_extraction_time_under_100ms(self):
        """DOM extraction should complete in less than 100ms.

        Target: <100ms extraction time for typical page complexity.
        """
        from app.models import DomExtractionOptions, ScreenshotRequest
        from app.screenshot import ScreenshotService

        service = ScreenshotService()
        await service.initialize()

        try:
            request = ScreenshotRequest(
                url="https://example.com",
                extract_dom=DomExtractionOptions(
                    enabled=True,
                    selectors=["h1", "h2", "h3", "p", "span", "a", "li", "button"],
                ),
            )
            result = await service.capture(request)

            assert len(result) == 3
            _, _, dom_result = result

            # Verify extraction time is under 100ms
            extraction_time = dom_result["extraction_time_ms"]
            assert extraction_time < 100, (
                f"Extraction took {extraction_time:.2f}ms, expected <100ms"
            )
        finally:
            await service.shutdown()

    @pytest.mark.asyncio
    async def test_extraction_with_max_elements_stays_fast(self):
        """Extraction with max_elements limit should be fast."""
        from app.models import DomExtractionOptions, ScreenshotRequest
        from app.screenshot import ScreenshotService

        service = ScreenshotService()
        await service.initialize()

        try:
            request = ScreenshotRequest(
                url="https://example.com",
                extract_dom=DomExtractionOptions(
                    enabled=True,
                    selectors=["*"],  # All elements
                    max_elements=500,
                ),
            )
            result = await service.capture(request)

            assert len(result) == 3
            _, _, dom_result = result

            # Even with broad selectors, should stay under 100ms
            extraction_time = dom_result["extraction_time_ms"]
            assert extraction_time < 100, (
                f"Extraction took {extraction_time:.2f}ms with max_elements=500"
            )

            # Verify we respected max_elements limit
            assert dom_result["element_count"] <= 500
        finally:
            await service.shutdown()

    @pytest.mark.asyncio
    async def test_total_capture_overhead_reasonable(self):
        """DOM extraction should add minimal overhead to capture time."""
        from app.models import DomExtractionOptions, ScreenshotRequest
        from app.screenshot import ScreenshotService

        service = ScreenshotService()
        await service.initialize()

        try:
            # Capture without extraction
            request_no_dom = ScreenshotRequest(url="https://example.com")
            result_no_dom = await service.capture(request_no_dom)
            time_no_dom = result_no_dom[1]

            # Capture with extraction
            request_with_dom = ScreenshotRequest(
                url="https://example.com",
                extract_dom=DomExtractionOptions(enabled=True),
            )
            result_with_dom = await service.capture(request_with_dom)
            time_with_dom = result_with_dom[1]

            # DOM extraction overhead should be reasonable (< 200ms added)
            overhead = time_with_dom - time_no_dom
            assert overhead < 200, (
                f"DOM extraction added {overhead:.2f}ms overhead, expected <200ms"
            )
        finally:
            await service.shutdown()
