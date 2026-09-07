#!/usr/bin/env python3
"""
每日 Google 新聞（台灣）爬取腳本 — Obsidian 格式輸出

Usage:
  python3 google_news_tw.py --vault-dir ~/Documents/Obsidian/Daily
  python3 google_news_tw.py --vault-dir ~/Documents/Obsidian/Daily --topics 台灣 國際 科技
  python3 google_news_tw.py --dry-run   ← 只印到畫面，不存檔

輸出檔名格式: YYYY-MM-DD-google-news.md
"""

import argparse
import asyncio
import re
import sys
from datetime import datetime
from pathlib import Path

TOPICS = {
    "焦點": "https://news.google.com/home?hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
    "台灣": "https://news.google.com/topics/CAAqJQgKIh9DQkFTRVFvSUwyMHZNRFptTXpJU0JYcG9MVlJYS0FBUAE?hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
    "國際": "https://news.google.com/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRGx1YlY4U0JYcG9MVlJYR2dKVVZ5Z0FQAQ?hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
    "商業": "https://news.google.com/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRGx6TVdZU0JYcG9MVlJYR2dKVVZ5Z0FQAQ?hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
    "科技": "https://news.google.com/topics/CAAqLAgKIiZDQkFTRmdvSkwyMHZNR1ptZHpWbUVnVjZhQzFVVnhvQ1ZGY29BQVAB?hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
    "健康": "https://news.google.com/topics/CAAqJQgKIh9DQkFTRVFvSUwyMHZNR3QwTlRFU0JYcG9MVlJYS0FBUAE?hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
}


def parse_args():
    parser = argparse.ArgumentParser(description="每日 Google 新聞台灣 → Obsidian Markdown")
    parser.add_argument("--vault-dir", default="~/Documents/Obsidian/Daily",
                        help="Obsidian vault 目錄（預設：~/Documents/Obsidian/Daily）")
    parser.add_argument("--topics", nargs="+", default=["焦點", "台灣", "國際", "科技"],
                        choices=list(TOPICS.keys()),
                        help="要爬取的主題（預設：焦點 台灣 國際 科技）")
    parser.add_argument("--dry-run", action="store_true", help="只印出內容，不存檔")
    parser.add_argument("--date", default=None, help="指定日期 YYYY-MM-DD（預設：今天）")
    return parser.parse_args()


def clean_news_markdown(raw_md: str) -> list[dict]:
    """從 raw markdown 中解析出新聞條目"""
    items = []
    lines = raw_md.split("\n")

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # 尋找新聞標題 pattern: [標題](url) 或 ## [標題](url)
        link_pattern = re.search(r'\[([^\]]{5,})\]\((https://news\.google\.com/read/[^\)]+)\)', line)
        if link_pattern:
            title = link_pattern.group(1).strip()
            url = link_pattern.group(2)

            # 過濾掉非新聞的導覽連結
            skip_keywords = ["下載", "登入", "設定", "說明", "隱私權", "Google 新聞", "更多"]
            if not any(kw in title for kw in skip_keywords) and len(title) > 8:
                # 嘗試找來源（前後行）
                source = ""
                time_ago = ""
                for j in range(max(0, i-2), min(len(lines), i+3)):
                    t = lines[j].strip()
                    if re.match(r'\d+ (分鐘|小時|天)前', t):
                        time_ago = t
                    # 來源通常是短文字（2-10個字）
                    elif 3 < len(t) < 20 and not t.startswith("[") and not t.startswith("!") and not t.startswith("#"):
                        if t not in ["更多", "Google 新聞", "新聞"]:
                            source = t

                items.append({
                    "title": title,
                    "url": url,
                    "source": source,
                    "time": time_ago,
                })
        i += 1

    # 去重（同標題只保留第一筆）
    seen = set()
    unique = []
    for item in items:
        if item["title"] not in seen:
            seen.add(item["title"])
            unique.append(item)

    return unique


async def crawl_topic(topic_name: str, url: str) -> list[dict]:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

    browser_config = BrowserConfig(headless=True, verbose=False)
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        wait_for="js:() => new Promise(r => setTimeout(r, 3000))",
        verbose=False,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=run_config)

    if not result.success:
        print(f"  ⚠️  [{topic_name}] 爬取失敗：{result.error_message}", file=sys.stderr)
        return []

    items = clean_news_markdown(str(result.markdown))
    print(f"  ✓  [{topic_name}] 找到 {len(items)} 則新聞", file=sys.stderr)
    return items


def build_obsidian_md(date_str: str, topics_data: dict[str, list[dict]]) -> str:
    today = datetime.strptime(date_str, "%Y-%m-%d")
    weekday = ["一", "二", "三", "四", "五", "六", "日"][today.weekday()]

    lines = [
        "---",
        f"date: {date_str}",
        "tags: [新聞, Google新聞, 台灣]",
        "source: Google News TW",
        "---",
        "",
        f"# 📰 {date_str}（週{weekday}）Google 新聞",
        "",
    ]

    for topic, items in topics_data.items():
        if not items:
            continue
        lines.append(f"## {topic}")
        lines.append("")
        for item in items[:15]:  # 每主題最多 15 則
            source_str = f" *({item['source']})*" if item["source"] else ""
            time_str = f" `{item['time']}`" if item["time"] else ""
            lines.append(f"- [{item['title']}]({item['url']}){source_str}{time_str}")
        lines.append("")

    lines.append("---")
    lines.append(f"*自動生成於 {datetime.now().strftime('%Y-%m-%d %H:%M')}*")

    return "\n".join(lines)


async def main():
    args = parse_args()
    date_str = args.date or datetime.now().strftime("%Y-%m-%d")

    print(f"[google-news-tw] 開始爬取 {date_str} 的新聞…", file=sys.stderr)

    # 依序爬取各主題
    topics_data = {}
    for topic in args.topics:
        url = TOPICS[topic]
        items = await crawl_topic(topic, url)
        topics_data[topic] = items

    # 建立 Obsidian Markdown
    content = build_obsidian_md(date_str, topics_data)

    if args.dry_run:
        print(content)
        return

    # 存檔
    vault_dir = Path(args.vault_dir).expanduser()
    vault_dir.mkdir(parents=True, exist_ok=True)
    output_path = vault_dir / f"{date_str}-google-news.md"
    output_path.write_text(content, encoding="utf-8")

    total = sum(len(v) for v in topics_data.values())
    print(f"[google-news-tw] 完成！共 {total} 則新聞 → {output_path}", file=sys.stderr)
    print(str(output_path))  # stdout 輸出路徑供呼叫者使用


if __name__ == "__main__":
    asyncio.run(main())
