---
name: html-slide-builder
description: |
  給定任何教材（文字、課程大綱、PDF、講義、口述主題），自動生成完整的 Reveal.js HTML 互動簡報並部署至 GitHub Pages。

  自動處理四大視覺/互動強化：
  1. AI 生成背景底圖（draw 技能，data-background-image）
  2. 扁平化圖標（draw 技能 + PIL 裁切去背，取代 emoji）
  3. Firebase 即時互動元件（文字雲、單選投票，Firestore 串接）
  4. 滑桿視覺化演示（clip-path 揭露，適合前後對比內容）

  當使用者說「幫我做 HTML 簡報」「把這份教材轉成互動簡報」「做 Reveal.js 簡報」「做成投影片」「做一份課程簡報」，或提供教材並要求轉成簡報格式時，務必使用此 Skill。即使使用者未明確說「互動」或「HTML」，只要目的是從教材產出可展示的簡報，也應觸發此 Skill。
---

# HTML 智慧簡報生成器

教材 → 分析 → 確認大綱 → 生成 Reveal.js 簡報 → 強化（底圖/圖標/互動/視覺化）→ GitHub Pages 部署

---

## 0. 讀取教材

接受任何形式的輸入：

- **文字 / Markdown**：直接分析
- **PDF**：用 Read 工具讀取（若有多頁先讀摘要頁）
- **口述主題**：自行根據標準教學邏輯設計（引言→概念→範例→互動→結論）

若教材資訊不足，不要詢問，直接用教學慣例補充。

---

## 1. 分析大綱，等使用者確認

分析完畢後輸出大綱表格，**等使用者確認後才繼續**：

```
## 📋 簡報大綱草稿（共 N 頁）

| 頁碼 | 標題 | 內容摘要 | 功能標記 |
|------|------|----------|----------|
| 1    | 封面 | 課程名稱、講師 | [BG] |
| 2    | 破冰提問 | 文字雲收集學員想法 | [INTERACT:wordcloud] |
| 3    | 三大重點 | 並列說明三個核心概念 | [ICON] |
| 4    | 前後對比 | A 方案 vs B 方案演進 | [VIZ] |
...

**功能標記說明**
- [BG] 背景底圖（draw 技能，暗色風格）
- [ICON] 扁平化圖標（draw + PIL 去背）
- [INTERACT:wordcloud] Firebase 即時文字雲
- [INTERACT:poll] Firebase 單選投票
- [VIZ] 滑桿視覺化演示（clip-path）

請確認大綱，或說明要調整的地方。
```

### 功能標記的決策原則

| 標記 | 觸發條件 | 每份簡報目標數量 |
|------|----------|-----------------|
| [BG] | 封面、封底、章節轉換、高衝擊結論 | 3–5 頁 |
| [ICON] | 頁面有 3–6 個並列項目（優缺點、步驟、特性） | 1–3 頁 |
| [INTERACT:wordcloud] | 開場破冰、先備知識調查、課尾反思 | 1 頁（通常第 2 頁） |
| [INTERACT:poll] | 概念確認、意見調查、前測/後測 | 0–1 頁 |
| [VIZ] | 「前後對比」「格式轉換」「A 到 B 的演進」 | 0–1 頁 |

---

## 2. 建立專案目錄與基礎 HTML

使用者確認後：

1. 建立專案目錄：`<當前工作目錄>/<簡報英文短名>/`
2. 建立 `images/` 子目錄
3. 生成 `index.html`（完整 Reveal.js 骨架）

讀取 `references/reveal-template.md` 獲得：完整 CSS 變數、元件樣式、Reveal.js 初始化程式碼。

**命名規則：**
- 專案目錄：kebab-case 英文（`ai-course`、`math-lesson`）
- Firestore 集合：`<slug>_wordcloud`、`<slug>_poll`（避免不同簡報資料混用）

**調色盤（所有簡報統一使用）：**
```
--accent:  #e8643a   橘紅（主強調）
--accent2: #4fc3f7   青（次強調）
--success: #81c784   綠（正面）
--warn:    #ffb74d   琥珀（提示）
背景：     #0d1117 ~ #1a1a2e（深暗色）
```

---

## 3. 生成背景底圖 [BG]

對每個 [BG] 頁面呼叫 draw 技能，可平行執行：

```bash
python "{{DRAW_SKILL_PATH}}" \
  "<底圖 prompt>" \
  --size 1536x1024 --quality low \
  --name <slide-slug> \
  --outdir "<專案目錄>/images"
```

> `{{DRAW_SKILL_PATH}}` 在安裝時由 install.py 自動替換為 draw.py 的實際路徑。

**底圖 Prompt 設計原則：**
- 深暗色系（deep navy、dark space、#0d1117 背景）
- 無文字
- 與投影片主題有關但抽象（概念視覺化，非字面圖示）
- 霓虹/發光效果，配合主題色
- 例：AI 課程封面 → `"deep navy background, glowing neural network nodes and light trails, cinematic wide, no text, abstract tech art"`

在 HTML section 加上：
```html
<section data-background-image="images/<slug>.png"
         data-background-opacity="0.3"
         data-background-size="cover">
```

透明度建議：封面 0.3–0.4；一般頁 0.12–0.18。

---

## 4. 圖標系統 [ICON]

### 4-1 生成圖標總表（一次生成所有頁面需要的圖標）

```bash
python "{{DRAW_SKILL_PATH}}" \
  "A clean icon sheet with exactly N flat neon icons in a single horizontal row on pure dark navy (#0d1117) background. [逐一描述每個圖標，從左到右]. Each icon large, bold, centered in equal column, no text." \
  --size 1536x1024 --quality low \
  --name icon_sheet \
  --outdir "<專案目錄>/images"
```

用 Read 工具先確認圖標總表品質，再裁切。

### 4-2 裁切 + 去背

執行（複製 `scripts/remove_bg.py` 到專案目錄，或用內聯 Python）：

```python
from PIL import Image
from pathlib import Path

img = Image.open("images/icon_sheet.png").convert("RGBA")
w, h = img.size
n = <圖標數量>
icons = ["icon_a", "icon_b", ...]  # 對應名稱

for i, name in enumerate(icons):
    x0 = i * (w // n)
    x1 = (i + 1) * (w // n) if i < n-1 else w
    col_w = x1 - x0
    sq = min(col_w, h)
    cx, cy = x0 + col_w // 2, h // 2
    crop = img.crop((cx-sq//2, cy-sq//2, cx+sq//2, cy+sq//2))
    crop = crop.resize((256, 256), Image.LANCZOS)
    crop.save(f"images/{name}.png")
```

然後執行去背（`scripts/remove_bg.py`）。

### 4-3 嵌入 HTML

- 用 `<img src="images/icon_name.png">` 取代 emoji
- adv-card 統一用 `border-top: 4px solid var(--accent2)` + `text-align: center`
- 圖標 img 加 `filter: drop-shadow(0 0 10px rgba(79,195,247,0.6))`

---

## 5. 互動元件 [INTERACT]

詳見 `references/firebase-config.md`，含完整的文字雲和投票 HTML 程式碼片段。

**通用原則：**
- 互動 section 加 `id="slide-<slug>"`
- 使用 `Reveal.on('slidechanged', e => { if (e.currentSlide?.id === '...') { /* 重繪 */ }})` 確保切頁後正確渲染
- Firestore 集合：`<簡報slug>_wordcloud` / `<簡報slug>_poll`（每份簡報獨立集合）
- 樣式：配合暗色主題，輸入框 `background: rgba(255,255,255,0.08)`

---

## 6. 視覺化演示 [VIZ]

clip-path 滑桿揭露效果，適合「格式轉換」「前後對比」「A→B 演進」。

**核心 CSS/JS 邏輯：**
```html
<div style="position:relative; height:390px; border-radius:12px; overflow:hidden;">
  <div id="viz-before" style="position:absolute;inset:0;..."></div>
  <div id="viz-after" style="position:absolute;inset:0;clip-path:inset(0 100% 0 0);"></div>
  <div id="viz-divider" style="position:absolute;top:0;left:0;width:3px;height:100%;
    background:linear-gradient(to bottom,transparent,#4fc3f7,transparent);
    box-shadow:0 0 12px #4fc3f7;pointer-events:none;"></div>
</div>
<input id="viz-slider" type="range" min="0" max="100" value="0">
<script>
document.getElementById('viz-slider').addEventListener('input', function() {
  const v = +this.value;
  document.getElementById('viz-after').style.clipPath = `inset(0 ${100-v}% 0 0)`;
  document.getElementById('viz-divider').style.left = v + '%';
});
</script>
```

左右各加標籤（`position:absolute; top:8px`），接近邊界時用 JS 淡出。

---

## 7. 部署到 GitHub Pages

```bash
cd "<專案目錄>"
git init
git config user.email "<你的 GitHub email>"
git config user.name "<你的 GitHub 帳號>"
git add .
git commit -m "初始化：<簡報名稱>"
gh repo create <帳號>/<repo-name> --public --source=. --push \
  --description "<簡報一句話描述>"
gh api repos/<帳號>/<repo-name>/pages \
  --method POST -f "source[branch]=master" -f "source[path]=/"
```

回傳給使用者：
```
✅ 簡報已部署！
🔗 GitHub Pages：https://<帳號>.github.io/<repo-name>/
（首次約 1–3 分鐘生效）
📦 原始碼：https://github.com/<帳號>/<repo-name>
```

---

## 執行順序與平行化建議

```
Phase 0: 讀取教材
Phase 1: 輸出大綱 → 等待確認 ← 必須停在這裡
Phase 2: 生成 HTML 骨架
Phase 3+4+5: 可平行（底圖生成 + 圖標生成同時跑）
Phase 6: VIZ 寫入 HTML
Phase 7: 確認一切完成後才 push
```

---

## 參考資源

| 檔案 | 用途 |
|------|------|
| `references/reveal-template.md` | Reveal.js HTML 完整模板、CSS 元件庫 |
| `references/firebase-config.md` | 文字雲、投票完整程式碼片段 |
| `scripts/remove_bg.py` | PIL 圖標去背腳本（對 images/icon_*.png 執行） |
