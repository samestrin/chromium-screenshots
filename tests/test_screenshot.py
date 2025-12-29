"""Tests for screenshot service - domain extraction, cookie injection, DOM extraction."""

import pytest



class TestDomainExtraction:
    """Tests for extracting domain from URL for cookie injection."""

    def test_extract_domain_from_https_url(self):
        """Extract domain from standard HTTPS URL."""
        from app.screenshot import extract_domain_from_url

        domain = extract_domain_from_url("https://example.com/page")
        assert domain == "example.com"

    def test_extract_domain_from_http_url(self):
        """Extract domain from HTTP URL."""
        from app.screenshot import extract_domain_from_url

        domain = extract_domain_from_url("http://example.com/page")
        assert domain == "example.com"

    def test_extract_domain_from_url_with_port(self):
        """Extract domain from URL with port - port should NOT be included."""
        from app.screenshot import extract_domain_from_url

        domain = extract_domain_from_url("http://192.168.68.99:3000/dashboard")
        assert domain == "192.168.68.99"

    def test_extract_domain_from_ip_address(self):
        """Extract domain from IP address URL."""
        from app.screenshot import extract_domain_from_url

        domain = extract_domain_from_url("http://192.168.1.1/admin")
        assert domain == "192.168.1.1"

    def test_extract_domain_from_localhost(self):
        """Extract domain from localhost URL."""
        from app.screenshot import extract_domain_from_url

        domain = extract_domain_from_url("http://localhost:8080/api")
        assert domain == "localhost"

    def test_extract_domain_from_subdomain(self):
        """Extract full domain including subdomain."""
        from app.screenshot import extract_domain_from_url

        domain = extract_domain_from_url("https://app.staging.example.com/login")
        assert domain == "app.staging.example.com"

    def test_extract_domain_returns_none_for_invalid_url(self):
        """Return None for invalid URLs."""
        from app.screenshot import extract_domain_from_url

        assert extract_domain_from_url("not-a-url") is None
        assert extract_domain_from_url("") is None

    def test_extract_domain_from_url_with_auth(self):
        """Extract domain from URL with authentication."""
        from app.screenshot import extract_domain_from_url

        domain = extract_domain_from_url("https://user:pass@example.com/page")
        assert domain == "example.com"


class TestCookieDomainInference:
    """Tests for inferring domain when not specified in cookie."""

    def test_infer_domain_for_cookie_without_domain(self):
        """Cookie without domain gets domain inferred from URL."""
        from app.models import Cookie
        from app.screenshot import prepare_cookies_for_playwright

        cookies = [Cookie(name="session", value="abc123")]
        url = "https://example.com/page"

        prepared = prepare_cookies_for_playwright(cookies, url)

        assert len(prepared) == 1
        assert prepared[0]["name"] == "session"
        assert prepared[0]["value"] == "abc123"
        assert prepared[0]["domain"] == "example.com"

    def test_preserve_explicit_domain(self):
        """Cookie with explicit domain should not be modified."""
        from app.models import Cookie
        from app.screenshot import prepare_cookies_for_playwright

        cookies = [Cookie(name="session", value="abc123", domain=".example.com")]
        url = "https://subdomain.example.com/page"

        prepared = prepare_cookies_for_playwright(cookies, url)

        assert prepared[0]["domain"] == ".example.com"

    def test_infer_domain_for_ip_address(self):
        """Infer domain from IP address URL."""
        from app.models import Cookie
        from app.screenshot import prepare_cookies_for_playwright

        cookies = [Cookie(name="auth", value="token123")]
        url = "http://192.168.68.99:3000/dashboard"

        prepared = prepare_cookies_for_playwright(cookies, url)

        assert prepared[0]["domain"] == "192.168.68.99"

    def test_multiple_cookies_with_mixed_domains(self):
        """Handle multiple cookies - some with domain, some without."""
        from app.models import Cookie
        from app.screenshot import prepare_cookies_for_playwright

        cookies = [
            Cookie(name="session", value="abc"),  # Needs inference
            Cookie(name="tracking", value="xyz", domain=".analytics.com"),  # Explicit
        ]
        url = "https://app.example.com/page"

        prepared = prepare_cookies_for_playwright(cookies, url)

        assert prepared[0]["domain"] == "app.example.com"
        assert prepared[1]["domain"] == ".analytics.com"

    def test_prepare_cookies_includes_all_fields(self):
        """Prepared cookies include all specified fields."""
        from app.models import Cookie
        from app.screenshot import prepare_cookies_for_playwright

        cookies = [
            Cookie(
                name="session",
                value="abc123",
                path="/app",
                httpOnly=True,
                secure=True,
                sameSite="Strict",
                expires=1735689600,
            )
        ]
        url = "https://example.com/page"

        prepared = prepare_cookies_for_playwright(cookies, url)

        assert prepared[0]["name"] == "session"
        assert prepared[0]["value"] == "abc123"
        assert prepared[0]["domain"] == "example.com"
        assert prepared[0]["path"] == "/app"
        assert prepared[0]["httpOnly"] is True
        assert prepared[0]["secure"] is True
        assert prepared[0]["sameSite"] == "Strict"
        assert prepared[0]["expires"] == 1735689600

    def test_prepare_cookies_omits_none_values(self):
        """Prepared cookies should omit fields that are None."""
        from app.models import Cookie
        from app.screenshot import prepare_cookies_for_playwright

        cookies = [Cookie(name="session", value="abc123")]
        url = "https://example.com/page"

        prepared = prepare_cookies_for_playwright(cookies, url)

        # Should have name, value, domain (inferred)
        assert "name" in prepared[0]
        assert "value" in prepared[0]
        assert "domain" in prepared[0]
        # Should NOT have httpOnly, secure, etc. since they're None
        assert "httpOnly" not in prepared[0]
        assert "secure" not in prepared[0]

    def test_prepare_cookies_empty_list(self):
        """Empty cookie list returns empty list."""
        from app.screenshot import prepare_cookies_for_playwright

        prepared = prepare_cookies_for_playwright([], "https://example.com")
        assert prepared == []

    def test_prepare_cookies_none_returns_empty(self):
        """None cookies returns empty list."""
        from app.screenshot import prepare_cookies_for_playwright

        prepared = prepare_cookies_for_playwright(None, "https://example.com")
        assert prepared == []


class TestConditionalDomExtraction:
    """Tests for conditional DOM extraction in ScreenshotService.

    AC: 04-01 - Conditional Extraction
    """

    @pytest.mark.asyncio
    async def test_no_extraction_when_extract_dom_is_none(self):
        """No DOM extraction when extract_dom is None."""
        from app.models import ScreenshotRequest
        from app.screenshot import ScreenshotService

        service = ScreenshotService()
        await service.initialize()

        try:
            request = ScreenshotRequest(url="https://example.com")
            result = await service.capture(request)

            # Result should be (bytes, time) without DOM extraction
            assert isinstance(result, tuple)
            assert len(result) == 2
            screenshot_bytes, capture_time = result
            assert isinstance(screenshot_bytes, bytes)
            assert isinstance(capture_time, float)
        finally:
            await service.shutdown()

    @pytest.mark.asyncio
    async def test_no_extraction_when_enabled_is_false(self):
        """No DOM extraction when extract_dom.enabled is False."""
        from app.models import DomExtractionOptions, ScreenshotRequest
        from app.screenshot import ScreenshotService

        service = ScreenshotService()
        await service.initialize()

        try:
            request = ScreenshotRequest(
                url="https://example.com",
                extract_dom=DomExtractionOptions(enabled=False),
            )
            result = await service.capture(request)

            # Result should be (bytes, time) without DOM extraction
            assert isinstance(result, tuple)
            assert len(result) == 2
        finally:
            await service.shutdown()

    @pytest.mark.asyncio
    async def test_extraction_runs_when_enabled(self):
        """DOM extraction runs when extract_dom.enabled is True."""
        from app.models import DomExtractionOptions, ScreenshotRequest
        from app.screenshot import ScreenshotService

        service = ScreenshotService()
        await service.initialize()

        try:
            request = ScreenshotRequest(
                url="https://example.com",
                extract_dom=DomExtractionOptions(enabled=True),
            )
            result = await service.capture(request)

            # Result should include DOM extraction data
            assert isinstance(result, tuple)
            # When extraction is enabled, result is (bytes, time, dom_result)
            assert len(result) == 3
            screenshot_bytes, capture_time, dom_result = result
            assert isinstance(screenshot_bytes, bytes)
            assert isinstance(capture_time, float)
            assert dom_result is not None
            assert "elements" in dom_result
            assert "viewport" in dom_result
        finally:
            await service.shutdown()


class TestDomExtractionOptionsPassthrough:
    """Tests for passing extraction options to JavaScript.

    AC: 04-03 - Options Passthrough
    """

    @pytest.mark.asyncio
    async def test_selectors_passed_to_extraction(self):
        """Custom selectors are passed to extraction script."""
        from app.models import DomExtractionOptions, ScreenshotRequest
        from app.screenshot import ScreenshotService

        service = ScreenshotService()
        await service.initialize()

        try:
            request = ScreenshotRequest(
                url="https://example.com",
                extract_dom=DomExtractionOptions(
                    enabled=True,
                    selectors=["h1"],  # Only h1 elements
                ),
            )
            result = await service.capture(request)

            assert len(result) == 3
            _, _, dom_result = result

            # All elements should be h1
            for el in dom_result["elements"]:
                assert el["tag_name"].lower() == "h1"
        finally:
            await service.shutdown()

    @pytest.mark.asyncio
    async def test_max_elements_limit_respected(self):
        """maxElements limit is passed and respected."""
        from app.models import DomExtractionOptions, ScreenshotRequest
        from app.screenshot import ScreenshotService

        service = ScreenshotService()
        await service.initialize()

        try:
            request = ScreenshotRequest(
                url="https://example.com",
                extract_dom=DomExtractionOptions(
                    enabled=True,
                    selectors=["h1", "h2", "p", "span", "a", "div"],
                    max_elements=5,
                ),
            )
            result = await service.capture(request)

            assert len(result) == 3
            _, _, dom_result = result
            assert len(dom_result["elements"]) <= 5
        finally:
            await service.shutdown()


class TestDomExtractionResultConversion:
    """Tests for converting JS results to Pydantic models.

    AC: 04-04 - Result Conversion
    """

    @pytest.mark.asyncio
    async def test_result_has_all_fields(self):
        """Extraction result has all required fields."""
        from app.models import DomExtractionOptions, ScreenshotRequest
        from app.screenshot import ScreenshotService

        service = ScreenshotService()
        await service.initialize()

        try:
            request = ScreenshotRequest(
                url="https://example.com",
                extract_dom=DomExtractionOptions(enabled=True),
            )
            result = await service.capture(request)

            assert len(result) == 3
            _, _, dom_result = result

            # Check result structure
            assert "elements" in dom_result
            assert "viewport" in dom_result
            assert "extraction_time_ms" in dom_result
            assert "element_count" in dom_result

            # Check viewport structure
            assert "width" in dom_result["viewport"]
            assert "height" in dom_result["viewport"]
        finally:
            await service.shutdown()

    @pytest.mark.asyncio
    async def test_element_has_required_fields(self):
        """Each element has all required fields."""
        from app.models import DomExtractionOptions, ScreenshotRequest
        from app.screenshot import ScreenshotService

        service = ScreenshotService()
        await service.initialize()

        try:
            request = ScreenshotRequest(
                url="https://example.com",
                extract_dom=DomExtractionOptions(
                    enabled=True,
                    selectors=["h1"],
                ),
            )
            result = await service.capture(request)

            assert len(result) == 3
            _, _, dom_result = result

            if dom_result["elements"]:
                element = dom_result["elements"][0]
                assert "selector" in element
                assert "xpath" in element
                assert "tag_name" in element
                assert "text" in element
                assert "rect" in element
                assert "computed_style" in element
                assert "is_visible" in element
                assert "z_index" in element
        finally:
            await service.shutdown()
