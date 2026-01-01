"""DOM extraction JavaScript script for page.evaluate().

This module provides the JavaScript code that runs inside the browser context
to extract DOM element information including positions, text, and styles.
"""

# JavaScript functions for DOM extraction
_EXTRACTION_JS = '''
// Generate a unique CSS selector for an element
function getUniqueSelector(el) {
    if (!el || el.nodeType !== Node.ELEMENT_NODE) {
        return '';
    }

    // If element has an ID, use it (most unique)
    if (el.id) {
        // Escape special characters in ID
        const escapedId = CSS.escape(el.id);
        return '#' + escapedId;
    }

    // Build path from element up to a unique ancestor
    const path = [];
    let current = el;

    while (current && current.nodeType === Node.ELEMENT_NODE) {
        let selector = current.tagName.toLowerCase();

        // If current has an ID, use it and stop
        if (current.id) {
            selector = '#' + CSS.escape(current.id);
            path.unshift(selector);
            break;
        }

        // Add classes for specificity
        if (current.className && typeof current.className === 'string') {
            const classes = current.className.trim().split(/\\s+/).filter(c => c);
            if (classes.length > 0) {
                selector += '.' + classes.map(c => CSS.escape(c)).join('.');
            }
        }

        // Check if we need nth-of-type for disambiguation
        const parent = current.parentElement;
        if (parent) {
            const siblings = Array.from(parent.children).filter(
                c => c.tagName === current.tagName
            );
            if (siblings.length > 1) {
                const index = siblings.indexOf(current) + 1;
                selector += ':nth-of-type(' + index + ')';
            }
        }

        path.unshift(selector);

        // Stop at body
        if (current.tagName.toLowerCase() === 'body') {
            break;
        }

        current = current.parentElement;
    }

    return path.join(' > ');
}

// Generate XPath for an element
function getXPath(el) {
    if (!el || el.nodeType !== Node.ELEMENT_NODE) {
        return '';
    }

    const parts = [];
    let current = el;

    while (current && current.nodeType === Node.ELEMENT_NODE) {
        let part = current.tagName.toLowerCase();

        // Get sibling index
        const parent = current.parentElement;
        if (parent) {
            const siblings = Array.from(parent.children).filter(
                c => c.tagName === current.tagName
            );
            if (siblings.length > 1) {
                const index = siblings.indexOf(current) + 1;
                part += '[' + index + ']';
            }
        }

        parts.unshift(part);
        current = current.parentElement;
    }

    return '/' + parts.join('/');
}

// Check if an element is visible
function isVisible(el) {
    if (!el) return false;

    const style = window.getComputedStyle(el);

    // Check display
    if (style.display === 'none') {
        return false;
    }

    // Check visibility
    if (style.visibility === 'hidden') {
        return false;
    }

    // Check opacity
    if (parseFloat(style.opacity) === 0) {
        return false;
    }

    // Check dimensions
    const rect = el.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) {
        return false;
    }

    return true;
}

// Get z-index of an element
function getZIndex(el) {
    if (!el) return 0;

    const style = window.getComputedStyle(el);
    const zIndex = style.zIndex;

    if (zIndex === 'auto' || zIndex === '') {
        return 0;
    }

    return parseInt(zIndex, 10) || 0;
}

// Check if an element has fixed or sticky positioning
function isFixed(el) {
    if (!el) return false;

    const style = window.getComputedStyle(el);
    const position = style.position;

    // Elements with position:fixed or position:sticky need special handling
    // in tiled capture as they appear in the same position across all tiles
    return position === 'fixed' || position === 'sticky';
}

// Main extraction function
function extractDomElements(options) {
    const startTime = performance.now();

    const {
        selectors = ['h1', 'h2', 'h3', 'p', 'span', 'a', 'li', 'button', 'label'],
        includeHidden = false,
        minTextLength = 1,
        maxElements = 500
    } = options;

    const elements = [];
    const selectorString = selectors.join(', ');
    const allMatches = document.querySelectorAll(selectorString);

    for (const el of allMatches) {
        if (elements.length >= maxElements) {
            break;
        }

        // Check visibility
        const visible = isVisible(el);
        if (!includeHidden && !visible) {
            continue;
        }

        // Get text content
        const text = (el.textContent || '').trim();
        if (text.length < minTextLength) {
            continue;
        }

        // Get bounding rect
        const rect = el.getBoundingClientRect();

        // Get computed style (just a few key properties)
        const computedStyle = window.getComputedStyle(el);

        elements.push({
            selector: getUniqueSelector(el),
            xpath: getXPath(el),
            tag_name: el.tagName.toLowerCase(),
            text: text,
            rect: {
                x: rect.x,
                y: rect.y,
                width: rect.width,
                height: rect.height
            },
            computed_style: {
                color: computedStyle.color,
                backgroundColor: computedStyle.backgroundColor,
                fontSize: computedStyle.fontSize,
                fontWeight: computedStyle.fontWeight
            },
            is_visible: visible,
            z_index: getZIndex(el),
            is_fixed: isFixed(el)
        });
    }

    const endTime = performance.now();

    return {
        elements: elements,
        viewport: {
            width: window.innerWidth,
            height: window.innerHeight,
            deviceScaleFactor: window.devicePixelRatio || 1,
            document_width: document.documentElement.scrollWidth,
            document_height: document.documentElement.scrollHeight
        },
        extraction_time_ms: endTime - startTime,
        element_count: elements.length
    };
}
'''


def get_extraction_script() -> str:
    """Return the JavaScript extraction script for use with page.evaluate().

    Returns:
        JavaScript code string containing getUniqueSelector, getXPath,
        isVisible, getZIndex, and extractDomElements functions.
    """
    return _EXTRACTION_JS
