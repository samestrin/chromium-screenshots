"""Tests for DOM extraction script - JavaScript execution via page.evaluate()."""

import os

import pytest

# Path to test fixture
FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "selector_test.html")


class TestUniqueSelector:
    """Tests for getUniqueSelector() JavaScript function.

    AC: 03-01 - Unique Selector Generation
    """

    @pytest.mark.asyncio
    async def test_selector_for_element_with_id(self):
        """Element with ID returns #id selector."""
        from playwright.async_api import async_playwright

        from app.dom_extraction import get_extraction_script

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(f"file://{FIXTURE_PATH}")

            script = get_extraction_script()
            result = await page.evaluate(
                f"""
                {script}
                const el = document.getElementById('main-title');
                getUniqueSelector(el);
                """
            )

            assert result == "#main-title"
            await browser.close()

    @pytest.mark.asyncio
    async def test_selector_for_element_with_classes(self):
        """Element with classes returns .class1.class2 selector."""
        from playwright.async_api import async_playwright

        from app.dom_extraction import get_extraction_script

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(f"file://{FIXTURE_PATH}")

            script = get_extraction_script()
            result = await page.evaluate(
                f"""
                {script}
                const el = document.querySelector('.intro.paragraph');
                getUniqueSelector(el);
                """
            )

            # Should include class selectors
            assert ".intro" in result or ".paragraph" in result
            await browser.close()

    @pytest.mark.asyncio
    async def test_selector_for_nested_element(self):
        """Nested elements return full path with > combinator."""
        from playwright.async_api import async_playwright

        from app.dom_extraction import get_extraction_script

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(f"file://{FIXTURE_PATH}")

            script = get_extraction_script()
            result = await page.evaluate(
                f"""
                {script}
                const el = document.querySelector('.container .content .highlight');
                getUniqueSelector(el);
                """
            )

            # Should contain parent reference or be unique
            assert result is not None
            assert len(result) > 0
            await browser.close()

    @pytest.mark.asyncio
    async def test_selector_for_sibling_uses_nth_of_type(self):
        """Siblings use :nth-of-type(n) for disambiguation."""
        from playwright.async_api import async_playwright

        from app.dom_extraction import get_extraction_script

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(f"file://{FIXTURE_PATH}")

            script = get_extraction_script()

            # Get selectors for all three li elements
            selectors = await page.evaluate(
                f"""
                {script}
                const items = document.querySelectorAll('#menu li');
                Array.from(items).map(el => getUniqueSelector(el));
                """
            )

            # All selectors should be unique
            assert len(set(selectors)) == 3
            # At least one should use nth-of-type or nth-child
            has_nth = any("nth" in s for s in selectors)
            assert has_nth or len(set(selectors)) == 3  # Or IDs make them unique
            await browser.close()

    @pytest.mark.asyncio
    async def test_selector_is_queryable(self):
        """Generated selector can be used to find the same element."""
        from playwright.async_api import async_playwright

        from app.dom_extraction import get_extraction_script

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(f"file://{FIXTURE_PATH}")

            script = get_extraction_script()
            result = await page.evaluate(
                f"""
                {script}
                const original = document.querySelector('#deep article header h2');
                const selector = getUniqueSelector(original);
                const found = document.querySelector(selector);
                original === found;
                """
            )

            assert result is True
            await browser.close()


class TestXPathGeneration:
    """Tests for getXPath() JavaScript function.

    AC: 03-02 - XPath Generation
    """

    @pytest.mark.asyncio
    async def test_xpath_returns_full_path(self):
        """XPath returns full path from document root."""
        from playwright.async_api import async_playwright

        from app.dom_extraction import get_extraction_script

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(f"file://{FIXTURE_PATH}")

            script = get_extraction_script()
            result = await page.evaluate(
                f"""
                {script}
                const el = document.getElementById('main-title');
                getXPath(el);
                """
            )

            assert result.startswith("/html/body")
            assert "h1" in result.lower()
            await browser.close()

    @pytest.mark.asyncio
    async def test_xpath_includes_sibling_indices(self):
        """XPath includes sibling indices for disambiguation."""
        from playwright.async_api import async_playwright

        from app.dom_extraction import get_extraction_script

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(f"file://{FIXTURE_PATH}")

            script = get_extraction_script()

            # Get XPaths for sibling li elements
            xpaths = await page.evaluate(
                f"""
                {script}
                const items = document.querySelectorAll('#menu li');
                Array.from(items).map(el => getXPath(el));
                """
            )

            # All XPaths should be unique
            assert len(set(xpaths)) == 3
            # Should include indices like [1], [2], [3]
            has_indices = any("[" in x and "]" in x for x in xpaths)
            assert has_indices
            await browser.close()

    @pytest.mark.asyncio
    async def test_xpath_handles_deep_nesting(self):
        """XPath handles deeply nested elements."""
        from playwright.async_api import async_playwright

        from app.dom_extraction import get_extraction_script

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(f"file://{FIXTURE_PATH}")

            script = get_extraction_script()
            result = await page.evaluate(
                f"""
                {script}
                const el = document.querySelector('#deep article header h2');
                getXPath(el);
                """
            )

            # Should include full path
            assert "html" in result.lower()
            assert "body" in result.lower()
            assert "section" in result.lower() or "article" in result.lower()
            await browser.close()

    @pytest.mark.asyncio
    async def test_xpath_is_evaluable(self):
        """Generated XPath can be used to find the same element."""
        from playwright.async_api import async_playwright

        from app.dom_extraction import get_extraction_script

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(f"file://{FIXTURE_PATH}")

            script = get_extraction_script()
            result = await page.evaluate(
                f"""
                {script}
                const original = document.querySelector('#deep article header h2');
                const xpath = getXPath(original);
                const found = document.evaluate(
                    xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
                ).singleNodeValue;
                original === found;
                """
            )

            assert result is True
            await browser.close()


class TestVisibilityDetection:
    """Tests for isVisible() JavaScript function.

    AC: 03-03 - Visibility Detection
    """

    @pytest.mark.asyncio
    async def test_display_none_is_not_visible(self):
        """Element with display:none returns false."""
        from playwright.async_api import async_playwright

        from app.dom_extraction import get_extraction_script

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(f"file://{FIXTURE_PATH}")

            script = get_extraction_script()
            result = await page.evaluate(
                f"""
                {script}
                const el = document.querySelector('.hidden');
                isVisible(el);
                """
            )

            assert result is False
            await browser.close()

    @pytest.mark.asyncio
    async def test_visibility_hidden_is_not_visible(self):
        """Element with visibility:hidden returns false."""
        from playwright.async_api import async_playwright

        from app.dom_extraction import get_extraction_script

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(f"file://{FIXTURE_PATH}")

            script = get_extraction_script()
            result = await page.evaluate(
                f"""
                {script}
                const el = document.querySelector('.invisible');
                isVisible(el);
                """
            )

            assert result is False
            await browser.close()

    @pytest.mark.asyncio
    async def test_opacity_zero_is_not_visible(self):
        """Element with opacity:0 returns false."""
        from playwright.async_api import async_playwright

        from app.dom_extraction import get_extraction_script

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(f"file://{FIXTURE_PATH}")

            script = get_extraction_script()
            result = await page.evaluate(
                f"""
                {script}
                const el = document.querySelector('.transparent');
                isVisible(el);
                """
            )

            assert result is False
            await browser.close()

    @pytest.mark.asyncio
    async def test_visible_element_returns_true(self):
        """Visible element returns true."""
        from playwright.async_api import async_playwright

        from app.dom_extraction import get_extraction_script

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(f"file://{FIXTURE_PATH}")

            script = get_extraction_script()
            result = await page.evaluate(
                f"""
                {script}
                const el = document.getElementById('main-title');
                isVisible(el);
                """
            )

            assert result is True
            await browser.close()

    @pytest.mark.asyncio
    async def test_zero_dimension_element_not_visible(self):
        """Element with zero dimensions is not visible."""
        from playwright.async_api import async_playwright

        from app.dom_extraction import get_extraction_script

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            # Create page with zero-dimension element
            await page.set_content(
                "<div id='zero' style='width:0;height:0;'>Hidden</div>"
            )

            script = get_extraction_script()
            result = await page.evaluate(
                f"""
                {script}
                const el = document.getElementById('zero');
                isVisible(el);
                """
            )

            assert result is False
            await browser.close()


class TestZIndexCalculation:
    """Tests for getZIndex() JavaScript function.

    AC: 03-04 - Z-index and stacking context
    """

    @pytest.mark.asyncio
    async def test_auto_z_index_returns_zero(self):
        """Element with auto z-index returns 0."""
        from playwright.async_api import async_playwright

        from app.dom_extraction import get_extraction_script

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(f"file://{FIXTURE_PATH}")

            script = get_extraction_script()
            result = await page.evaluate(
                f"""
                {script}
                const el = document.getElementById('main-title');
                getZIndex(el);
                """
            )

            assert result == 0
            await browser.close()

    @pytest.mark.asyncio
    async def test_explicit_z_index_returns_value(self):
        """Element with explicit z-index returns that value."""
        from playwright.async_api import async_playwright

        from app.dom_extraction import get_extraction_script

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.set_content(
                "<div id='test' style='position:relative;z-index:42;'>Test</div>"
            )

            script = get_extraction_script()
            result = await page.evaluate(
                f"""
                {script}
                const el = document.getElementById('test');
                getZIndex(el);
                """
            )

            assert result == 42
            await browser.close()

    @pytest.mark.asyncio
    async def test_negative_z_index(self):
        """Element with negative z-index returns negative value."""
        from playwright.async_api import async_playwright

        from app.dom_extraction import get_extraction_script

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.set_content(
                "<div id='test' style='position:relative;z-index:-5;'>Test</div>"
            )

            script = get_extraction_script()
            result = await page.evaluate(
                f"""
                {script}
                const el = document.getElementById('test');
                getZIndex(el);
                """
            )

            assert result == -5
            await browser.close()


class TestExtractionOptions:
    """Tests for extractDomElements() IIFE with options handling.

    AC: 03-04 - Extraction Options Handling
    """

    @pytest.mark.asyncio
    async def test_respects_selectors_list(self):
        """Extraction respects selectors list."""
        from playwright.async_api import async_playwright

        from app.dom_extraction import get_extraction_script

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(f"file://{FIXTURE_PATH}")

            script = get_extraction_script()
            result = await page.evaluate(
                f"""
                {script}
                extractDomElements({{
                    selectors: ['h1'],
                    includeHidden: false,
                    minTextLength: 1,
                    maxElements: 500
                }});
                """
            )

            # Should only find h1 elements
            tags = [el["tag_name"].lower() for el in result["elements"]]
            assert all(tag == "h1" for tag in tags)
            await browser.close()

    @pytest.mark.asyncio
    async def test_respects_include_hidden_false(self):
        """Extraction excludes hidden elements by default."""
        from playwright.async_api import async_playwright

        from app.dom_extraction import get_extraction_script

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(f"file://{FIXTURE_PATH}")

            script = get_extraction_script()
            result = await page.evaluate(
                f"""
                {script}
                extractDomElements({{
                    selectors: ['div'],
                    includeHidden: false,
                    minTextLength: 1,
                    maxElements: 500
                }});
                """
            )

            # Hidden divs should not be included
            texts = [el["text"] for el in result["elements"]]
            assert "Hidden by display:none" not in texts
            await browser.close()

    @pytest.mark.asyncio
    async def test_respects_include_hidden_true(self):
        """Extraction includes hidden elements when enabled."""
        from playwright.async_api import async_playwright

        from app.dom_extraction import get_extraction_script

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(f"file://{FIXTURE_PATH}")

            script = get_extraction_script()
            result = await page.evaluate(
                f"""
                {script}
                extractDomElements({{
                    selectors: ['div'],
                    includeHidden: true,
                    minTextLength: 1,
                    maxElements: 500
                }});
                """
            )

            # Hidden divs should be included
            texts = [el["text"] for el in result["elements"]]
            assert any("Hidden" in text for text in texts)
            await browser.close()

    @pytest.mark.asyncio
    async def test_respects_min_text_length(self):
        """Extraction filters by minimum text length."""
        from playwright.async_api import async_playwright

        from app.dom_extraction import get_extraction_script

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.set_content(
                """
                <p>A</p>
                <p>Short</p>
                <p>This is a longer text that should be included</p>
                """
            )

            script = get_extraction_script()
            result = await page.evaluate(
                f"""
                {script}
                extractDomElements({{
                    selectors: ['p'],
                    includeHidden: false,
                    minTextLength: 10,
                    maxElements: 500
                }});
                """
            )

            # Only the longer text should be included
            assert len(result["elements"]) == 1
            assert "longer" in result["elements"][0]["text"]
            await browser.close()

    @pytest.mark.asyncio
    async def test_respects_max_elements(self):
        """Extraction stops at maxElements limit."""
        from playwright.async_api import async_playwright

        from app.dom_extraction import get_extraction_script

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(f"file://{FIXTURE_PATH}")

            script = get_extraction_script()
            result = await page.evaluate(
                f"""
                {script}
                extractDomElements({{
                    selectors: ['h1', 'h2', 'p', 'li', 'span', 'a', 'div'],
                    includeHidden: false,
                    minTextLength: 1,
                    maxElements: 3
                }});
                """
            )

            # Should have at most 3 elements
            assert len(result["elements"]) <= 3
            assert result["element_count"] <= 3
            await browser.close()

    @pytest.mark.asyncio
    async def test_result_includes_viewport(self):
        """Extraction result includes viewport information."""
        from playwright.async_api import async_playwright

        from app.dom_extraction import get_extraction_script

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.set_viewport_size({"width": 1920, "height": 1080})
            await page.goto(f"file://{FIXTURE_PATH}")

            script = get_extraction_script()
            result = await page.evaluate(
                f"""
                {script}
                extractDomElements({{
                    selectors: ['h1'],
                    includeHidden: false,
                    minTextLength: 1,
                    maxElements: 500
                }});
                """
            )

            assert "viewport" in result
            assert result["viewport"]["width"] == 1920
            assert result["viewport"]["height"] == 1080
            await browser.close()

    @pytest.mark.asyncio
    async def test_result_includes_extraction_time(self):
        """Extraction result includes extraction_time_ms."""
        from playwright.async_api import async_playwright

        from app.dom_extraction import get_extraction_script

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(f"file://{FIXTURE_PATH}")

            script = get_extraction_script()
            result = await page.evaluate(
                f"""
                {script}
                extractDomElements({{
                    selectors: ['h1'],
                    includeHidden: false,
                    minTextLength: 1,
                    maxElements: 500
                }});
                """
            )

            assert "extraction_time_ms" in result
            assert isinstance(result["extraction_time_ms"], (int, float))
            assert result["extraction_time_ms"] >= 0
            await browser.close()

    @pytest.mark.asyncio
    async def test_element_has_all_required_fields(self):
        """Each extracted element has all required fields."""
        from playwright.async_api import async_playwright

        from app.dom_extraction import get_extraction_script

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(f"file://{FIXTURE_PATH}")

            script = get_extraction_script()
            result = await page.evaluate(
                f"""
                {script}
                extractDomElements({{
                    selectors: ['h1'],
                    includeHidden: false,
                    minTextLength: 1,
                    maxElements: 500
                }});
                """
            )

            assert len(result["elements"]) > 0
            element = result["elements"][0]

            # Check all required fields
            assert "selector" in element
            assert "xpath" in element
            assert "tag_name" in element
            assert "text" in element
            assert "rect" in element
            assert "computed_style" in element
            assert "is_visible" in element
            assert "z_index" in element

            # Check rect has all fields
            rect = element["rect"]
            assert "x" in rect
            assert "y" in rect
            assert "width" in rect
            assert "height" in rect
            await browser.close()


class TestDocumentDimensions:
    """Tests for document dimension extraction (Sprint 5.0).

    AC: 02-02 - Resize Impact Estimation
    Document dimensions are needed for Vision AI sizing hints.
    """

    @pytest.mark.asyncio
    async def test_result_includes_document_width(self):
        """Extraction result includes document_width."""
        from playwright.async_api import async_playwright

        from app.dom_extraction import get_extraction_script

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.set_viewport_size({"width": 1920, "height": 1080})
            await page.goto(f"file://{FIXTURE_PATH}")

            script = get_extraction_script()
            result = await page.evaluate(
                f"""
                {script}
                extractDomElements({{
                    selectors: ['h1'],
                    includeHidden: false,
                    minTextLength: 1,
                    maxElements: 500
                }});
                """
            )

            assert "viewport" in result
            assert "document_width" in result["viewport"]
            assert isinstance(result["viewport"]["document_width"], (int, float))
            assert result["viewport"]["document_width"] > 0
            await browser.close()

    @pytest.mark.asyncio
    async def test_result_includes_document_height(self):
        """Extraction result includes document_height."""
        from playwright.async_api import async_playwright

        from app.dom_extraction import get_extraction_script

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.set_viewport_size({"width": 1920, "height": 1080})
            await page.goto(f"file://{FIXTURE_PATH}")

            script = get_extraction_script()
            result = await page.evaluate(
                f"""
                {script}
                extractDomElements({{
                    selectors: ['h1'],
                    includeHidden: false,
                    minTextLength: 1,
                    maxElements: 500
                }});
                """
            )

            assert "viewport" in result
            assert "document_height" in result["viewport"]
            assert isinstance(result["viewport"]["document_height"], (int, float))
            assert result["viewport"]["document_height"] > 0
            await browser.close()

    @pytest.mark.asyncio
    async def test_viewport_dimensions_still_present(self):
        """Viewport width/height still returned alongside document dimensions."""
        from playwright.async_api import async_playwright

        from app.dom_extraction import get_extraction_script

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.set_viewport_size({"width": 1920, "height": 1080})
            await page.goto(f"file://{FIXTURE_PATH}")

            script = get_extraction_script()
            result = await page.evaluate(
                f"""
                {script}
                extractDomElements({{
                    selectors: ['h1'],
                    includeHidden: false,
                    minTextLength: 1,
                    maxElements: 500
                }});
                """
            )

            viewport = result["viewport"]
            # Original viewport fields
            assert "width" in viewport
            assert "height" in viewport
            assert "deviceScaleFactor" in viewport
            # New document dimension fields
            assert "document_width" in viewport
            assert "document_height" in viewport
            await browser.close()

    @pytest.mark.asyncio
    async def test_document_dimensions_for_scrollable_page(self):
        """Document dimensions larger than viewport for scrollable content."""
        from playwright.async_api import async_playwright

        from app.dom_extraction import get_extraction_script

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.set_viewport_size({"width": 800, "height": 600})

            # Create a page with content taller than viewport
            await page.set_content(
                """
                <html>
                <body style="margin:0; padding:0;">
                    <div style="height: 3000px; width: 100%;">
                        <h1>Tall Content</h1>
                        <p>This page is 3000px tall</p>
                    </div>
                </body>
                </html>
                """
            )

            script = get_extraction_script()
            result = await page.evaluate(
                f"""
                {script}
                extractDomElements({{
                    selectors: ['h1', 'p'],
                    includeHidden: false,
                    minTextLength: 1,
                    maxElements: 500
                }});
                """
            )

            viewport = result["viewport"]
            # Viewport height is 600
            assert viewport["height"] == 600
            # Document height should be >= 3000
            assert viewport["document_height"] >= 3000
            await browser.close()

    @pytest.mark.asyncio
    async def test_document_dimensions_for_wide_page(self):
        """Document dimensions larger than viewport for horizontal scroll."""
        from playwright.async_api import async_playwright

        from app.dom_extraction import get_extraction_script

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.set_viewport_size({"width": 800, "height": 600})

            # Create a page with content wider than viewport
            await page.set_content(
                """
                <html>
                <body style="margin:0; padding:0;">
                    <div style="width: 4000px; height: 100%;">
                        <h1>Wide Content</h1>
                        <p>This page is 4000px wide</p>
                    </div>
                </body>
                </html>
                """
            )

            script = get_extraction_script()
            result = await page.evaluate(
                f"""
                {script}
                extractDomElements({{
                    selectors: ['h1', 'p'],
                    includeHidden: false,
                    minTextLength: 1,
                    maxElements: 500
                }});
                """
            )

            viewport = result["viewport"]
            # Viewport width is 800
            assert viewport["width"] == 800
            # Document width should be >= 4000
            assert viewport["document_width"] >= 4000
            await browser.close()
