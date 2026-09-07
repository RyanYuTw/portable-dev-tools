---
name: crawl4ai
description: Use this skill whenever the user wants to scrape, crawl, or fetch web page content — even if they just say "get me the content of this URL", "grab this page", "read this website", "scrape this", "download this page", or paste a URL and ask what's on it. Uses crawl4ai Python library (not Docker) to handle both static and JavaScript-rendered pages. Returns clean Markdown, structured data, links, or screenshots. Also use when user mentions "web scraping", "extract data from a website", "crawl multiple pages", or "fetch content from a URL". Trigger proactively whenever a URL appears in context and the user seems to want its content.
---

# crawl4ai Web Crawling Skill

Use crawl4ai to fetch and process web page content. It handles JavaScript-rendered pages (SPAs, React/Vue/Angular apps) automatically using a headless Chromium browser.

## Scripts location

All scripts are in `~/.claude/skills/crawl4ai/scripts/`.

```bash
SKILL_DIR=~/.claude/skills/crawl4ai/scripts
# Always use the dedicated venv's python (crawl4ai is installed there, not in system python3)
PY=~/.claude/skills/crawl4ai/venv/bin/python3
```

## Core operations

### 1. Fetch a single page as Markdown

The default and most common operation — outputs clean Markdown to stdout:

```bash
$PY $SKILL_DIR/crawl.py https://example.com
```

To save to a file instead:
```bash
$PY $SKILL_DIR/crawl.py https://example.com --output-dir ./output --format markdown
```

### 2. Extract specific content with CSS selector

When you only need part of a page (articles, tables, listings):
```bash
$PY $SKILL_DIR/crawl.py https://news.ycombinator.com --css-selector ".athing"
$PY $SKILL_DIR/crawl.py https://example.com --css-selector "article, main, .content"
```

### 3. Handle JavaScript / SPA pages

For pages that load content dynamically, add a wait time (milliseconds):
```bash
$PY $SKILL_DIR/crawl.py https://spa-app.com --wait 2000
```

### 4. Get page metadata + links (JSON)

```bash
$PY $SKILL_DIR/crawl.py https://example.com --format json --output-dir ./output
```

### 5. Both Markdown + JSON metadata

```bash
$PY $SKILL_DIR/crawl.py https://example.com --format both --output-dir ./output
```

### 6. Take a screenshot

```bash
$PY $SKILL_DIR/crawl.py https://example.com --screenshot --output-dir ./output
```

### 7. Crawl multiple URLs (batch)

Pass URLs as arguments:
```bash
$PY $SKILL_DIR/batch_crawl.py https://url1.com https://url2.com https://url3.com --output-dir ./results
```

Or pipe a JSON array:
```bash
echo '["https://url1.com","https://url2.com"]' | $PY $SKILL_DIR/batch_crawl.py --stdin --output-dir ./results
```

## Common patterns

**User says "scrape this URL"** → Run `crawl.py <url>` and show the Markdown output inline.

**User wants to read a doc page** → Run `crawl.py <url>` and summarize/answer from the content.

**User wants links from a page** → Run `crawl.py <url> --format json`, read the `links` field.

**User wants to scrape a list page** → Use `--css-selector` to target the list items.

**User pastes multiple URLs** → Use `batch_crawl.py` for efficiency.

**Page seems empty or JS-driven** → Add `--wait 2000` (or higher if needed).

## What crawl4ai returns

- **`result.markdown`** — clean Markdown of the page body (noise-filtered)  
- **`result.links`** — `internal` and `external` link lists  
- **`result.media`** — images, videos, audio found on the page  
- **`result.metadata`** — title, description, keywords  
- **`result.screenshot`** — base64 PNG if requested  

## Caching

crawl4ai caches results by default (~/.crawl4ai/). Add `--no-cache` to bypass this if you need fresh content.

## When inline display makes sense

After crawling, if the content is short enough (< ~300 lines), display the Markdown directly in the conversation so the user can immediately read it. For longer pages, save to file and summarize the key points.
