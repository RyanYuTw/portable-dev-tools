#!/usr/bin/env python3
"""
crawl4ai batch crawl helper — crawl multiple URLs concurrently.

Usage:
  python batch_crawl.py <url1> <url2> ... [options]
  echo '["url1","url2"]' | python batch_crawl.py --stdin [options]

Options:
  --output-dir DIR     Save results to DIR (default: ./crawl_results)
  --max-concurrent N   Max concurrent crawlers (default: 5)
  --wait MS            Wait N ms after page load
  --verbose            Show progress

Output: JSON summary written to stdout, files saved to output-dir
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse


def parse_args():
    parser = argparse.ArgumentParser(description="Batch crawl URLs using crawl4ai")
    parser.add_argument("urls", nargs="*", help="URLs to crawl")
    parser.add_argument("--stdin", action="store_true", help="Read URLs as JSON array from stdin")
    parser.add_argument("--output-dir", default="./crawl_results")
    parser.add_argument("--max-concurrent", type=int, default=5)
    parser.add_argument("--wait", type=int, default=0)
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


async def crawl_one(crawler, url, run_config, output_dir, verbose):
    parsed = urlparse(url)
    safe_name = (parsed.netloc + parsed.path).replace("/", "_").strip("_") or "page"
    safe_name = "".join(c if c.isalnum() or c in "-_." else "_" for c in safe_name)[:60]

    result = await crawler.arun(url=url, config=run_config)

    if not result.success:
        return {"url": url, "success": False, "error": result.error_message}

    md_path = output_dir / f"{safe_name}.md"
    md_content = result.markdown or ""
    md_path.write_text(md_content, encoding="utf-8")

    if verbose:
        print(f"✓ {url} → {md_path.name}", file=sys.stderr)

    return {
        "url": url,
        "success": True,
        "title": result.metadata.get("title", "") if result.metadata else "",
        "word_count": len(md_content.split()),
        "file": str(md_path),
    }


async def run_batch(args, urls):
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    browser_config = BrowserConfig(headless=True, verbose=False)
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.ENABLED,
        wait_for=f"js:() => new Promise(r => setTimeout(r, {args.wait}))" if args.wait > 0 else None,
    )

    semaphore = asyncio.Semaphore(args.max_concurrent)

    async def bounded_crawl(crawler, url):
        async with semaphore:
            return await crawl_one(crawler, url, run_config, output_dir, args.verbose)

    async with AsyncWebCrawler(config=browser_config) as crawler:
        tasks = [bounded_crawl(crawler, url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    final = []
    for r in results:
        if isinstance(r, Exception):
            final.append({"success": False, "error": str(r)})
        else:
            final.append(r)

    summary = {
        "total": len(urls),
        "succeeded": sum(1 for r in final if r.get("success")),
        "failed": sum(1 for r in final if not r.get("success")),
        "output_dir": str(output_dir),
        "results": final,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def main():
    args = parse_args()
    urls = list(args.urls)
    if args.stdin:
        urls += json.loads(sys.stdin.read())
    if not urls:
        print("ERROR: No URLs provided", file=sys.stderr)
        sys.exit(1)
    asyncio.run(run_batch(args, urls))


if __name__ == "__main__":
    main()
