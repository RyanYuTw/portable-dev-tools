#!/usr/bin/env python3
"""
自動化投影片生成腳本（無互動確認版）
供 youtube-auto-creator pipeline 的 Tier 2 呼叫。

用法：
  python generate_slides.py --script '{"title":"...","scenes":[...]}' \
                             --output slides/output.html

輸出：
  stdout: JSON scenes 陣列（供 pipeline 解析成 video scenes）
  --output: Reveal.js HTML 完整投影片（可選）
"""
import argparse
import json
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Groq 投影片大綱生成
# ---------------------------------------------------------------------------

SLIDES_SCHEMA = """{
  "slides": [
    {
      "title": "投影片標題（繁體中文）",
      "bullets": ["要點一", "要點二", "要點三"],
      "visual": "image search keywords in English",
      "note": "講者備注（選填）"
    }
  ]
}"""


def generate_slide_outline(script: dict, api_key: str) -> list[dict]:
    """用 Groq 把腳本轉換為投影片大綱，回傳 slides list。"""
    from groq import Groq

    client = Groq(api_key=api_key)
    scenes_text = "\n".join(
        f"場景{i+1}：{s['text']}" for i, s in enumerate(script.get("scenes", []))
    )
    n = len(script.get("scenes", []))

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "你是一位簡報設計師，擅長將影片腳本轉化為清晰易懂的投影片大綱。"
                    "每張投影片聚焦單一重點，用精簡的要點呈現，不超過 4 個要點。"
                    "visual 欄位填英文關鍵字，用於搜尋代表性圖片。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"請將以下影片腳本重整為 {n} 張投影片的大綱。\n\n"
                    f"腳本：\n{scenes_text}\n\n"
                    f"只輸出 JSON，結構如下：\n{SLIDES_SCHEMA}"
                ),
            },
        ],
        temperature=0.5,
        max_tokens=2000,
    )

    raw = response.choices[0].message.content.strip()
    if "```json" in raw:
        raw = raw[raw.index("```json") + 7 : raw.rindex("```")].strip()
    elif "```" in raw:
        raw = raw[raw.index("```") + 3 : raw.rindex("```")].strip()
    elif not raw.startswith("{"):
        start = raw.find("{")
        if start != -1:
            raw = raw[start:]

    return json.loads(raw).get("slides", [])


# ---------------------------------------------------------------------------
# Reveal.js HTML 生成
# ---------------------------------------------------------------------------

_CSS = """
    :root {
      --accent:  #e8643a;
      --accent2: #4fc3f7;
      --success: #81c784;
      --warn:    #ffb74d;
    }
    .reveal { font-family: 'Segoe UI', 'Noto Sans TC', sans-serif; }
    .reveal h1, .reveal h2, .reveal h3 {
      font-family: 'Segoe UI', 'Noto Sans TC', sans-serif;
      font-weight: 700;
    }
    .reveal h2 { color: var(--accent2); font-size: 1.4em; }
    .reveal ul { text-align: left; }
    .reveal li { margin: 0.4em 0; line-height: 1.5; }
    .reveal .progress { color: var(--accent); }
    .cover-title { font-size: 2em; font-weight: 800; }
    .cover-sub { font-size: 0.7em; color: #aaa; margin-top: 0.5em; }
"""

_REVEAL_INIT = """
  <script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.js"></script>
  <script>
    Reveal.initialize({
      hash: true,
      transition: 'fade',
      transitionSpeed: 'fast',
      controls: true,
      progress: true,
      slideNumber: true,
    });
  </script>
"""


def build_html(title: str, slides: list[dict]) -> str:
    sections = []

    # 封面
    sections.append(f"""
    <section>
      <p class="cover-title">{title}</p>
    </section>""")

    # 內容投影片
    for slide in slides:
        slide_title = slide.get("title", "")
        bullets = slide.get("bullets", [])
        note = slide.get("note", "")

        bullet_html = "\n".join(
            f"        <li class='fragment'>{b}</li>" for b in bullets
        )
        note_html = f"<aside class='notes'>{note}</aside>" if note else ""

        sections.append(f"""
    <section>
      <h2>{slide_title}</h2>
      <ul>
{bullet_html}
      </ul>
      {note_html}
    </section>""")

    sections_html = "\n".join(sections)

    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reset.css" />
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.css" />
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/theme/night.css" />
  <style>{_CSS}</style>
</head>
<body>
  <div class="reveal">
    <div class="slides">
{sections_html}
    </div>
  </div>
{_REVEAL_INIT}
</body>
</html>
"""


# ---------------------------------------------------------------------------
# 主程式
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="自動生成投影片（無互動確認）")
    parser.add_argument("--script", required=True, help="腳本 JSON 字串或 JSON 檔案路徑")
    parser.add_argument("--output", help="Reveal.js HTML 輸出路徑（選填）")
    parser.add_argument("--api-key", default=os.getenv("GROQ_API_KEY"), help="Groq API Key")
    args = parser.parse_args()

    # 讀取腳本（優先視為 JSON 字串，再嘗試當作檔案路徑）
    script_input = args.script
    if script_input.strip().startswith("{"):
        script = json.loads(script_input)
    else:
        script = json.loads(Path(script_input).read_text())

    if not args.api_key:
        print("ERROR: 未提供 GROQ_API_KEY", file=sys.stderr)
        sys.exit(1)

    # 生成投影片大綱
    slides = generate_slide_outline(script, args.api_key)
    if not slides:
        print("ERROR: 投影片大綱生成失敗", file=sys.stderr)
        sys.exit(1)

    # 轉換為 pipeline scenes 格式並輸出到 stdout
    scenes = []
    for slide in slides:
        t = slide.get("title", "")
        bullets = slide.get("bullets", [])
        visual = slide.get("visual", t)
        text = t + ("\n" + "\n".join(f"・{b}" for b in bullets) if bullets else "")
        scenes.append({"text": text, "visual": visual})

    print(json.dumps({"scenes": scenes, "slides": slides}, ensure_ascii=False))

    # 選擇性輸出 HTML
    if args.output:
        html = build_html(script.get("title", "簡報"), slides)
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html, encoding="utf-8")
        print(f"HTML 已輸出：{out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
