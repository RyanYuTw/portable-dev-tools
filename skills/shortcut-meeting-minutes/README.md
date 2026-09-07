# Shortcut Meeting Minutes Generator

從 Shortcut API 自動提取 IT Team 成員的 tickets 並生成會議紀錄。

## 功能特色

✅ 自動從 Shortcut 提取 Ryan、小智、Joyce、Angel 的 tickets  
✅ 過濾近 N 天(預設 30 天)更新的項目  
✅ 只包含 Review 相關狀態(已完成/進行中項目)  
✅ 自動移除待執行、待確認等未開始項目  
✅ 按專案分類，按狀態排序  
✅ 同時生成 Markdown 和 Word 檔案  

## 使用方式

### 基本用法

```bash
#shortcut-meeting-minutes
```

生成近 30 天的會議紀錄，輸出到 `~/Documents/TNL/`

### 自訂天數

```bash
#shortcut-meeting-minutes 15
```

生成近 15 天的會議紀錄

### 自訂輸出目錄

```bash
#shortcut-meeting-minutes 30 ~/Documents/meetings
```

生成近 30 天的會議紀錄，輸出到指定目錄

## 環境需求

### 1. Shortcut API Token

需要設定環境變數 `SHORTCUT_API_TOKEN`:

```bash
export SHORTCUT_API_TOKEN="your-token-here"
```

或在 `~/.claude/settings.json` 中設定:

```json
{
  "env": {
    "SHORTCUT_API_TOKEN": "your-token-here"
  }
}
```

### 2. Python 套件

需要安裝 `python-docx`:

```bash
pip3 install --break-system-packages python-docx
```

Skill 會自動檢查並安裝。

## 產出檔案

- `會議記錄_MM-DD_IT_Review.md` - Markdown 版本
- `會議記錄_MM-DD_IT_Review.docx` - Word 版本

## 會議紀錄結構

```
會議記錄: MM/DD - IT Team Review
├── 大綱
│   ├── 與會人: Joyce, 小智, Ryan, Angel
│   ├── 會議日期: YYYY年MM月DD日
│   ├── 統計期間: YYYY年MM月DD日 ~ YYYY年MM月DD日
│   └── 會議目標: 回顧近期工作成果與進度
├── 會議記錄
│   ├── [專案A]
│   │   ├── 已完成項目
│   │   ├── Production 項目
│   │   └── ...
│   ├── [專案B]
│   └── ...
├── 討論
└── 心情
```

## 包含的狀態

- ✅ 已完成
- 🟢 Production
- 🟡 Sandbox
- 🔵 Stage
- 🟣 Greenroom
- 🔄 執行中

## 排除的狀態

- ❌ 待確認
- ❌ 待執行
- ❌ 已確認待排程
- ❌ 觀察中

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

## 檔案說明

- `SKILL.md` - Skill 定義和說明文件
- `generate_meeting.py` - 從 Shortcut 提取資料並生成 Markdown
- `convert_to_docx.py` - 將 Markdown 轉換為 Word 檔案
- `README.md` - 本說明檔

## 技術細節

### 成員對應

```python
MEMBERS = {
    '65f917d5-1329-4b73-a462-2049fd53f3a7': 'Ryan',
    '65f919ee-cf06-437e-9b9e-868e80e71960': '小智',
    '65f941c1-57c6-45fc-875d-c00fff48f79f': 'Joyce',
    '67a1cfca-c087-4ad3-adee-29c420c98ba8': 'Angel',
}
```

### Shortcut API

使用 Shortcut Stories Search API:

```bash
POST https://api.app.shortcut.com/api/v3/stories/search
```

payload:
```json
{
  "owner_ids": ["...", "...", "...", "..."],
  "archived": false
}
```

## 疑難排解

### 錯誤: 未設定 SHORTCUT_API_TOKEN

解決方式:
```bash
export SHORTCUT_API_TOKEN="your-token-here"
```

### ModuleNotFoundError: No module named 'docx'

解決方式:
```bash
pip3 install --break-system-packages python-docx
```

### 沒有生成任何項目

可能原因:
1. 近期沒有符合條件的 tickets
2. 成員 ID 有變更
3. API Token 過期

## 更新記錄

- 2026-06-05: 初版建立
  - 支援從 Shortcut 提取 tickets
  - 生成 Markdown 和 Word 檔案
  - 支援自訂天數和輸出目錄
