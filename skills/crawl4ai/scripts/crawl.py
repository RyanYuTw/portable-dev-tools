#!/usr/bin/env python3
"""
crawl4ai helper script — used by the crawl4ai Claude Code skill.

Usage:
  python crawl.py <url> [options]

Options:
  --output-dir DIR     Save output files to DIR (default: current dir)
  --format markdown|json|both   Output format (default: markdown)
  --css-selector SEL   Extract only elements matching CSS selector
  --wait MS            Wait N milliseconds after page load (for JS-heavy pages)
  --screenshot         Save a screenshot of the page
  --no-cache           Bypass cache, always fetch fresh
  --verbose            Show detailed progress

Examples:
  python crawl.py https://example.com
  python crawl.py https://example.com --format both --output-dir ./results
  python crawl.py https://news.ycombinator.com --css-selector ".athing"
  python crawl.py https://spa-app.com --wait 2000
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime


def parse_args():
    parser = argparse.ArgumentParser(description="Crawl a URL using crawl4ai")
    parser.add_argument("url", help="URL to crawl")
    parser.add_argument("--output-dir", default=".", help="Directory to save output files")
    parser.add_argument("--format", choices=["markdown", "json", "both"], default="markdown")
    parser.add_argument("--css-selector", default=None, help="CSS selector to extract specific content")
    parser.add_argument("--wait", type=int, default=0, help="Wait N ms after page load (for JS pages)")
    parser.add_argument("--screenshot", action="store_true", help="Save a page screenshot")
    parser.add_argument("--no-cache", action="store_true", help="Bypass cache")
    parser.add_argument("--verbose", action="store_true", help="Show detailed progress")
    return parser.parse_args()


async def run_crawl(args):
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename base from URL
    from urllib.parse import urlparse
    parsed = urlparse(args.url)
    safe_name = (parsed.netloc + parsed.path).replace("/", "_").strip("_") or "page"
    safe_name = "".join(c if c.isalnum() or c in "-_." else "_" for c in safe_name)[:80]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"{safe_name}_{timestamp}"

    browser_config = BrowserConfig(headless=True, verbose=args.verbose)

    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS if args.no_cache else CacheMode.ENABLED,
        css_selector=args.css_selector,
        screenshot=args.screenshot,
        wait_for=f"js:() => new Promise(r => setTimeout(r, {args.wait}))" if args.wait > 0 else None,
        verbose=args.verbose,
    )

    if args.verbose:
        print(f"[crawl4ai] Fetching: {args.url}", file=sys.stderr)

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=args.url, config=run_config)

    if not result.success:
        print(f"ERROR: Crawl failed — {result.error_message}", file=sys.stderr)
        sys.exit(1)

    saved_files = []

    # Save Markdown
    if args.format in ("markdown", "both"):
        md_path = output_dir / f"{base_name}.md"
        md_content = str(result.markdown) if result.markdown else ""
        md_path.write_text(md_content or "", encoding="utf-8")
        saved_files.append(str(md_path))
        if args.verbose:
            print(f"[crawl4ai] Markdown saved: {md_path}", file=sys.stderr)

    # Save JSON metadata
    if args.format in ("json", "both"):
        json_path = output_dir / f"{base_name}.json"
        meta = {
            "url": args.url,
            "title": result.metadata.get("title", "") if result.metadata else "",
            "crawled_at": timestamp,
            "success": result.success,
            "links": {
                "internal": [l["href"] for l in (result.links.get("internal", []) or [])],
                "external": [l["href"] for l in (result.links.get("external", []) or [])],
            },
            "media": {
                "images": [img.get("src", "") for img in (result.media.get("images", []) or [])],
            },
            "word_count": len(str(result.markdown or "").split()),
        }
        json_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        saved_files.append(str(json_path))
        if args.verbose:
            print(f"[crawl4ai] JSON metadata saved: {json_path}", file=sys.stderr)

    # Save screenshot
    if args.screenshot and result.screenshot:
        import base64
        img_path = output_dir / f"{base_name}.png"
        img_path.write_bytes(base64.b64decode(result.screenshot))
        saved_files.append(str(img_path))
        if args.verbose:
            print(f"[crawl4ai] Screenshot saved: {img_path}", file=sys.stderr)

    # Print summary to stdout (for Claude to read)
    summary = {
        "url": args.url,
        "success": True,
        "title": result.metadata.get("title", "") if result.metadata else "",
        "word_count": len(str(result.markdown or "").split()),
        "saved_files": saved_files,
        "internal_links_count": len(result.links.get("internal", []) or []),
        "external_links_count": len(result.links.get("external", []) or []),
    }

    # If markdown format and output-dir is current dir, also print content to stdout
    if args.format == "markdown" and args.output_dir == ".":
        md_content = Path(saved_files[0]).read_text(encoding="utf-8") if saved_files else ""
        print(md_content)
    else:
        print(json.dumps(summary, ensure_ascii=False, indent=2))


def main():
    args = parse_args()
    asyncio.run(run_crawl(args))


if __name__ == "__main__":
    main()
