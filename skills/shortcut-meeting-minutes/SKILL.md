---
description: 從 Shortcut API 提取 tickets 並生成 IT Team Review 會議紀錄(Markdown + Word)
args:
  days: 統計天數(預設 30 天)
  output_dir: 輸出目錄(預設 ~/Documents/TNL)
---

# Shortcut Meeting Minutes Generator

從 Shortcut API 提取指定成員近期的 tickets，生成 IT Team Review 會議紀錄。

## 功能

- 從 Shortcut 提取 Ryan、小智、Joyce、Angel 四位成員的 tickets
- 過濾近 N 天(預設 30 天)更新的項目
- 只包含 Review 相關狀態(已完成、Production、Sandbox、Stage、Greenroom、執行中)
- 移除待執行、待確認等未開始的項目
- 按專案分類，按狀態排序
- 同時生成 Markdown 和 Word 檔案

## 使用方式

```
#shortcut-meeting-minutes
#shortcut-meeting-minutes 15
#shortcut-meeting-minutes 30 ~/Documents/meetings
```

## 環境需求

- 需要設定環境變數 `SHORTCUT_API_TOKEN`
- 需要安裝 `python-docx` 套件

## 產出檔案

- `會議記錄_MM-DD_IT_Review.md` - Markdown 版本
- `會議記錄_MM-DD_IT_Review.docx` - Word 版本

## 會議紀錄結構

```
會議記錄: MM/DD - IT Team Review
├── 大綱
│   ├── 與會人
│   ├── 會議日期
│   ├── 統計期間
│   └── 會議目標
├── 會議記錄(按專案分類)
├── 討論
└── 心情
```

## 指令

當使用者觸發這個 skill 時:

1. 檢查環境變數 `SHORTCUT_API_TOKEN` 是否存在
2. 檢查並安裝 `python-docx` 套件
3. 解析參數:
   - 第一個參數: 統計天數(預設 30)
   - 第二個參數: 輸出目錄(預設 ~/Documents/TNL)
4. 執行生成腳本
5. 回報生成結果

## 成員 ID 對應

```python
MEMBERS = {
    '65f917d5-1329-4b73-a462-2049fd53f3a7': 'Ryan',
    '65f919ee-cf06-437e-9b9e-868e80e71960': '小智',
    '65f941c1-57c6-45fc-875d-c00fff48f79f': 'Joyce',
    '67a1cfca-c087-4ad3-adee-29c420c98ba8': 'Angel',
}
```

## 狀態對應

```python
STATE_MAP = {
    500009833: '待確認', 500009841: '觀察中', 500009826: '已確認待排程',
    500009827: '待執行', 500009828: '執行中', 500009840: 'Greenroom',
    500009829: 'Stage', 500009830: 'Sandbox', 500009832: 'Production',
    500009831: '已完成',
}

# Review 會議只包含這些狀態
REVIEW_STATES = ['已完成', 'Production', 'Sandbox', 'Stage', 'Greenroom', '執行中']
```

## 實作步驟

### 步驟 1: 檢查環境

```bash
# 檢查 API Token
if [ -z "$SHORTCUT_API_TOKEN" ]; then
  echo "❌ 錯誤: 未設定 SHORTCUT_API_TOKEN 環境變數"
  exit 1
fi

# 檢查/安裝 python-docx
python3 -c "import docx" 2>/dev/null || pip3 install --break-system-packages python-docx -q
```

### 步驟 2: 提取 Shortcut Stories

使用 Shortcut Search API 提取所有成員的 stories:

```bash
curl -s -X POST \
  -H "Shortcut-Token: $SHORTCUT_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"owner_ids": ["65f917d5-1329-4b73-a462-2049fd53f3a7", "65f919ee-cf06-437e-9b9e-868e80e71960", "65f941c1-57c6-45fc-875d-c00fff48f79f", "67a1cfca-c087-4ad3-adee-29c420c98ba8"], "archived": false}' \
  "https://api.app.shortcut.com/api/v3/stories/search" > /tmp/stories.json
```

### 步驟 3: 生成 Markdown

執行 Python 腳本過濾並生成 Markdown:
- 過濾近 N 天更新的 stories
- 只保留 Review 狀態的項目
- 按專案分類
- 按狀態排序

### 步驟 4: 轉換為 Word

使用 `python-docx` 將 Markdown 轉換為 Word 格式。

### 步驟 5: 回報結果

回報生成的檔案路徑和統計資訊。

## 範例輸出

```
✅ 會議紀錄生成完成

📁 生成的檔案:
- ~/Documents/TNL/會議記錄_06-05_IT_Review.md (6.4 KB)
- ~/Documents/TNL/會議記錄_06-05_IT_Review.docx (38.3 KB)

📊 統計:
- 統計期間: 2026-05-06 ~ 2026-06-05 (30天)
- 總 Stories: 2,696 個
- 近期更新: 106 個
- Review 項目: 91 個
- 涵蓋專案: 35+ 個
```
