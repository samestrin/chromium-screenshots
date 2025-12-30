# Quality Assessment

> Automatic quality detection for DOM extraction results.

Quality assessment analyzes extraction results and provides actionable feedback. Use it to:

- **Abort early** in pipelines when extraction quality is poor
- **Debug** why certain pages produce sparse results
- **Monitor** extraction quality across many URLs

---

## Quality Levels

| Level | Element Count | Additional Criteria |
|-------|---------------|---------------------|
| `good` | 21+ elements | 3+ unique tag types AND has headings |
| `low` | 5-20 elements | - |
| `poor` | 1-4 elements | - |
| `empty` | 0 elements | - |

### Thresholds

```
EMPTY:  0 elements
POOR:   1-4 elements
LOW:    5-20 elements
GOOD:   21+ elements (with diversity requirements)
```

To achieve `good` quality, you need:
1. At least 21 elements
2. At least 3 different tag types (e.g., h1, p, a)
3. At least one heading element (h1-h6)

---

## Warning Codes

| Code | Trigger | Suggestion |
|------|---------|------------|
| `NO_ELEMENTS` | 0 elements extracted | Verify page loaded, test with example.com |
| `LOW_ELEMENT_COUNT` | 1-4 elements | Expand selectors, check page load |
| `NO_HEADINGS` | No h1-h6 found (10+ elements) | Add h1-h6 to selectors |
| `LOW_TAG_DIVERSITY` | <3 unique tags (21+ elements) | Broaden selector variety |
| `MANY_HIDDEN` | >50% elements hidden | Add wait time, check dynamic content |
| `MINIMAL_TEXT` | Avg text <10 chars | May be extracting UI elements |

---

## Response Format

Quality data appears in `dom_extraction`:

```json
{
  "dom_extraction": {
    "elements": [...],
    "element_count": 47,
    "quality": "good",
    "warnings": [
      {
        "code": "NO_HEADINGS",
        "message": "No heading elements (h1-h6) found in the extraction.",
        "suggestion": "Consider adding h1-h6 to your extraction selectors."
      }
    ]
  }
}
```

### HTTP Header

The quality level is also returned as an HTTP header:

```
X-Quality: good
```

---

## Decision Logic

```
if elements == 0:
    return EMPTY + NO_ELEMENTS warning

if elements <= 4:
    return POOR + LOW_ELEMENT_COUNT warning

if elements <= 20:
    return LOW

if elements >= 21:
    if unique_tags >= 3 AND has_heading:
        return GOOD
    else:
        return LOW + diversity/heading warnings
```

---

## Using Quality in Pipelines

### Early Abort Pattern

```python
response = requests.post(
    "http://localhost:8000/screenshot/json",
    json={"url": url, "extract_dom": {"enabled": True}}
)
data = response.json()

quality = data["dom_extraction"]["quality"]

if quality == "empty":
    raise Exception(f"Extraction failed for {url}")

if quality == "poor":
    warnings = data["dom_extraction"]["warnings"]
    log.warning(f"Low quality extraction: {warnings}")
```

### Quality Monitoring

```python
import json

def analyze_quality(urls):
    results = {"good": 0, "low": 0, "poor": 0, "empty": 0}

    for url in urls:
        resp = requests.post(
            "http://localhost:8000/screenshot/json",
            json={"url": url, "extract_dom": {"enabled": True}}
        )
        quality = resp.json()["dom_extraction"]["quality"]
        results[quality] += 1

    return results
```

### Warning Analysis

```bash
# Extract all warnings from a capture
curl -s -X POST "http://localhost:8000/screenshot/json" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "extract_dom": {"enabled": true}}' \
  | jq '.dom_extraction.warnings[] | "\(.code): \(.suggestion)"'
```

---

## Improving Quality

### From EMPTY to POOR+

1. Verify the page loads correctly
2. Add `wait_for_timeout` for slow pages
3. Test with `https://example.com` first

### From POOR to LOW

1. Check if page has loaded completely
2. Expand selectors to match more content
3. Verify JavaScript has executed

### From LOW to GOOD

1. Include heading selectors (h1-h6)
2. Add variety: paragraphs, links, lists
3. Ensure 21+ elements match

---

## Performance

Quality assessment runs in O(n) time with a single pass through elements:

| Elements | Assessment Time |
|----------|-----------------|
| 100 | <2ms |
| 500 | <5ms |

Zero additional network requests or DOM queries are needed.
