# Reveal.js HTML 基礎模板

## 完整 HTML 骨架

```html
<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title><!-- 簡報標題 --></title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reset.css" />
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.css" />
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/theme/night.css" />
  <!-- 若有文字雲，加這行 -->
  <!-- <script src="https://cdn.jsdelivr.net/npm/wordcloud@1.2.2/src/wordcloud2.min.js"></script> -->
  <style>
    /* === 全域變數 === */
    :root {
      --accent:  #e8643a;
      --accent2: #4fc3f7;
      --success: #81c784;
      --warn:    #ffb74d;
    }

    .reveal {
      font-family: 'Segoe UI', 'Noto Sans TC', sans-serif;
    }
    .reveal h1, .reveal h2, .reveal h3 {
      font-family: 'Segoe UI', 'Noto Sans TC', sans-serif;
      font-weight: 700;
      letter-spacing: -0.02em;
    }
    .reveal h1 { font-size: 2.2em; }
    .reveal h2 { font-size: 1.5em; color: var(--accent2); }
    .reveal .progress { color: var(--accent); }
    .reveal .fragment { opacity: 0.2; }
    .reveal .fragment.visible { opacity: 1; }

    /* === 封面 === */
    .title-slide { text-align: center; }
    .title-slide .tag {
      display: inline-block;
      background: var(--accent);
      color: #fff;
      padding: 4px 14px;
      border-radius: 20px;
      font-size: 0.55em;
      letter-spacing: 0.08em;
      margin-bottom: 0.8em;
      font-weight: 600;
    }
    .title-slide .subtitle { font-size: 0.75em; color: #aaa; margin-top: 0.5em; }
    .title-slide .author   { margin-top: 2em; font-size: 0.5em; color: #888; }

    /* === 統計數字卡 === */
    .stat-row { display: flex; gap: 20px; justify-content: center; margin-top: 1em; }
    .stat-card {
      background: rgba(255,255,255,0.07);
      border: 1px solid rgba(255,255,255,0.15);
      border-radius: 12px;
      padding: 20px 26px;
      text-align: center;
      flex: 1;
    }
    .stat-card .num   { font-size: 1.8em; font-weight: 800; color: var(--accent); line-height: 1; }
    .stat-card .label { font-size: 0.42em; color: #ccc; margin-top: 6px; }

    /* === 優勢卡（並列特點）=== */
    .adv-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-top: 0.6em; }
    .adv-card {
      background: rgba(255,255,255,0.05);
      border-top: 4px solid var(--accent2);
      border-radius: 8px;
      padding: 16px;
      text-align: center;
    }
    .adv-card .adv-icon { margin-bottom: 8px; }
    .adv-card .adv-icon img {
      width: 56px; height: 56px; object-fit: contain;
      display: block; margin: 0 auto;
      filter: drop-shadow(0 0 10px rgba(79,195,247,0.6));
    }
    .adv-card .adv-title { font-size: 0.5em; font-weight: 700; color: var(--accent2); margin-bottom: 6px; }
    .adv-card .adv-desc  { font-size: 0.4em; color: #bbb; line-height: 1.6; }

    /* === VS 對比 === */
    .vs-grid { display: grid; grid-template-columns: 1fr 60px 1fr; gap: 0; align-items: start; margin-top: 0.6em; }
    .vs-col { background: rgba(255,255,255,0.05); border-radius: 12px; padding: 18px; }
    .vs-col.left-col  { border-top: 3px solid var(--accent2); }
    .vs-col.right-col { border-top: 3px solid var(--warn); }
    .vs-label { font-size: 0.7em; font-weight: 700; margin-bottom: 10px; letter-spacing: 0.05em; }
    .vs-label.left  { color: var(--accent2); }
    .vs-label.right { color: var(--warn); }
    .vs-center { display: flex; align-items: center; justify-content: center; font-size: 1.4em; font-weight: 900; color: #555; }
    .vs-col ul { font-size: 0.42em; list-style: none; padding: 0; margin: 0; }
    .vs-col ul li { padding: 5px 0; border-bottom: 1px solid rgba(255,255,255,0.06); }
    .vs-col ul li:last-child { border-bottom: none; }
    .vs-col ul li::before { content: "✦ "; opacity: 0.5; }

    /* === 時間軸 === */
    .timeline { position: relative; padding-left: 36px; margin-top: 0.8em; }
    .timeline::before {
      content: ''; position: absolute; left: 14px; top: 4px; bottom: 4px;
      width: 2px; background: rgba(255,255,255,0.2);
    }
    .timeline-item { position: relative; margin-bottom: 18px; font-size: 0.46em; }
    .timeline-item::before {
      content: ''; position: absolute; left: -28px; top: 4px;
      width: 10px; height: 10px; border-radius: 50%;
      background: var(--accent); border: 2px solid #1a1a2e;
    }
    .timeline-item .ti-date { color: var(--accent); font-weight: 700; font-size: 1.1em; margin-bottom: 2px; }
    .timeline-item .ti-text { color: #ccc; }

    /* === 引用 === */
    .quote-box {
      background: rgba(255,255,255,0.05);
      border-left: 4px solid var(--accent);
      border-radius: 8px;
      padding: 20px 24px;
      margin: 0.8em 0;
      font-size: 0.55em;
      color: #ddd;
      font-style: italic;
      line-height: 1.7;
    }
    .quote-author { font-size: 0.4em; color: #888; text-align: right; margin-top: 8px; font-style: normal; }

    /* === 結論卡 === */
    .conclusion-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 0.8em; }
    .conclusion-card { border-radius: 10px; padding: 18px; font-size: 0.44em; }
    .conclusion-card.positive {
      background: rgba(79,195,247,0.12);
      border: 1px solid rgba(79,195,247,0.35);
    }
    .conclusion-card.caution {
      background: rgba(255,183,77,0.1);
      border: 1px solid rgba(255,183,77,0.3);
    }
    .conclusion-card .cc-title { font-size: 1.3em; font-weight: 700; margin-bottom: 8px; }
    .conclusion-card.positive .cc-title { color: var(--accent2); }
    .conclusion-card.caution  .cc-title { color: var(--warn); }
    .conclusion-card ul { list-style: none; padding: 0; margin: 0; color: #ccc; line-height: 1.8; }
    .conclusion-card ul li::before { content: "→ "; opacity: 0.6; }

    /* === 封底 === */
    .end-slide { text-align: center; }
    .end-slide .big { font-size: 3em; margin-bottom: 0.2em; }
    .end-slide .tagline { font-size: 0.65em; color: #aaa; }

    /* === LIVE 動畫 === */
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }
  </style>
</head>
<body>
<div class="reveal">
  <div class="slides">

    <!-- 投影片從這裡開始 -->

    <!-- 封面範例 -->
    <section data-background-image="images/cover.png"
             data-background-opacity="0.35"
             data-background-size="cover">
      <div class="title-slide">
        <div class="tag"><!-- 場次標籤，如：2026 年 5 月 · 課程名稱 --></div>
        <h1><!-- 主標題 --></h1>
        <h2 style="color:var(--accent); margin-top:0.2em;"><!-- 副標題 --></h2>
        <p class="subtitle"><!-- 說明文字 --></p>
        <p class="author"><!-- 講師 / 日期 --></p>
      </div>
    </section>

    <!-- 更多投影片... -->

  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.js"></script>
<script>
  Reveal.initialize({
    hash: true,
    transition: 'slide',
    transitionSpeed: 'default',
    backgroundTransition: 'fade',
    center: true,
    progress: true,
    controls: true,
    slideNumber: 'c/t',
    plugins: []
  });
</script>

<!-- 若有互動元件，Firebase module script 加在這裡 -->

</body>
</html>
```

---

## 常用 Section 片段

### 數字統計頁
```html
<section>
  <h2>關鍵數字</h2>
  <div class="stat-row fragment">
    <div class="stat-card">
      <div class="num">440<span style="font-size:0.5em">萬+</span></div>
      <div class="label">說明文字</div>
    </div>
    <div class="stat-card">
      <div class="num">8,200</div>
      <div class="label">說明文字</div>
    </div>
  </div>
</section>
```

### 4 欄優勢卡（含圖標）
```html
<section>
  <h2>四大優勢</h2>
  <div class="adv-grid">
    <div class="adv-card fragment">
      <div class="adv-icon"><img src="images/icon_a.png" alt="A"></div>
      <div class="adv-title">標題 A</div>
      <div class="adv-desc">說明文字...</div>
    </div>
    <!-- 重複 4 次 -->
  </div>
</section>
```

### 封底
```html
<section data-background-image="images/ending.png"
         data-background-opacity="0.4"
         data-background-size="cover">
  <div class="end-slide">
    <div class="big">
      <img src="images/icon_globe.png" alt=""
           style="width:160px;height:160px;object-fit:contain;
                  filter:drop-shadow(0 0 24px rgba(79,195,247,0.7));">
    </div>
    <h1 style="color:var(--accent2);"><!-- 收尾標語 --></h1>
    <p class="tagline"><!-- 引用句 --></p>
  </div>
</section>
```
