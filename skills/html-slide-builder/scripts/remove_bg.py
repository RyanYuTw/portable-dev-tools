#!/usr/bin/env python3
"""
remove_bg.py — PIL 亮度閾值去背腳本
用法：python remove_bg.py [--dir <目錄>] [<檔案> ...]

預設：處理當前目錄下所有 images/icon_*.png
指定 --dir：處理該目錄下所有 icon_*.png
指定檔案：直接處理指定的 PNG 檔
"""
import sys
import argparse
from pathlib import Path
from PIL import Image

DARK_THRESHOLD = 45   # 亮度 < 此值 → 完全透明
FADE_THRESHOLD = 80   # 亮度介於 DARK~FADE → 漸變透明


def remove_bg(path: Path) -> None:
    img = Image.open(path).convert("RGBA")
    data = img.load()
    w, h = img.size

    for y in range(h):
        for x in range(w):
            r, g, b, a = data[x, y]
            lum = r * 0.299 + g * 0.587 + b * 0.114
            if lum < DARK_THRESHOLD:
                data[x, y] = (r, g, b, 0)
            elif lum < FADE_THRESHOLD:
                ratio = (lum - DARK_THRESHOLD) / (FADE_THRESHOLD - DARK_THRESHOLD)
                data[x, y] = (r, g, b, int(255 * ratio))

    img.save(path)
    print(f"  去背完成：{path.name}")


def main():
    parser = argparse.ArgumentParser(description="PNG 圖示去背（亮度閾值）")
    parser.add_argument("files", nargs="*", help="指定要處理的 PNG 檔案")
    parser.add_argument("--dir", default=None, help="批次處理該目錄下的 icon_*.png")
    args = parser.parse_args()

    targets = []

    if args.files:
        targets = [Path(f) for f in args.files]
    elif args.dir:
        targets = sorted(Path(args.dir).glob("icon_*.png"))
    else:
        targets = sorted(Path("images").glob("icon_*.png"))

    if not targets:
        print("找不到符合條件的 PNG 檔案。")
        sys.exit(0)

    print(f"共 {len(targets)} 個檔案待處理…")
    for p in targets:
        if p.exists():
            remove_bg(p)
        else:
            print(f"  跳過（找不到）：{p}")

    print("全部完成。")


if __name__ == "__main__":
    main()
