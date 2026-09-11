---
name: weekly-report-mail
description: 依 Jira tickets 產生週報（待辦／執行中／已完成三階段與完成度），補上使用者自填的專案進度，經確認後寄給 hr@dboem.com 並副本相關人。用於「產生週報」「寄週報」「這週工作報告」。
---

# 週報產生與寄送

先產生內容、讓使用者補齊與確認，**確認後才寄信**。

## 1. 收集與計算

執行 `portable-dev-tools:weekly-jira-report` 取得資料收集、分類與完成度計算規則，並照它執行（唯讀，不得修改 Jira 或 GitLab）。預設專案 `KNDU`、GitLab `laravel/ims`、時區 Asia/Taipei、週期為上週一 00:00 至週日 23:59:59。

### 分組必須用 statusCategory，不是狀態名稱

KNDU 有**四種**狀態，但只有三個分類：

| 狀態 | statusCategory | 週報歸類 |
|---|---|---|
| 待辦事項 | `new` | 待辦事項 |
| 計畫階段 | `new` | 待辦事項 |
| 進行中 | `indeterminate` | 執行中 |
| 完成 | `done` | 已完成 |

按狀態名稱分三組會讓「計畫階段」的票**憑空消失**。一律按 statusCategory 分組。

### 完成度

- **有子任務的票**：完成度 = 已完成子任務數 ÷ 子任務總數。這與 Jira 票面上顯示的百分比同源，兩者必須一致；不一致代表資料讀取有誤，先查清楚再往下走。
- **沒有子任務的票**：Jira 無法自動判定。**逐張詢問使用者**填寫百分比，不要自行推估，也不要用 commit 數量或工時代替。使用者未填的標記為「待確認」，不計入分子。

類別欄位空白是正常的（既有票不回填），歸為「未分類」，不要當成錯誤回報。

## 2. 請使用者補齊

兩件事必須由使用者提供，不可代寫：

1. 無子任務票的完成度百分比
2. **各案專案進度報告**——每個專案的文字說明

用 AskUserQuestion 或直接提問收集，一次問完減少往返。

## 3. 呈現完整草稿並取得確認

把完成的週報全文顯示給使用者，內容依 weekly-jira-report 的輸出格式，三階段分別列出工作內容與完成度百分比，加上使用者自填的專案進度報告。

**必須取得明確同意才進入下一步。** 使用者說「可以」「寄吧」才算；沒有回應、或只是討論內容修改，都不算同意。修改後要重新呈現並再次確認。

## 4. 寄送

用 Gmail MCP `send_message`：

| 欄位 | 值 |
|---|---|
| 寄件者 | `ryan.yu@dboem.com` — 見下方驗證步驟 |
| 收件者 | `hr@dboem.com` |
| 副本 | `ccy@dboem.com`、`barbie@dboem.com` |
| 主旨 | `研發部週報 YYYY-MM-DD ~ YYYY-MM-DD` |
| 內文 | 確認過的週報全文 |

### 寄件者必須是公司信箱

`send_message` **沒有 `from` 參數**，一律從連接器已驗證的帳號寄出，也不支援 Gmail 的 send-as 別名。所以寄件位址完全取決於 claude.ai 的 Gmail 連接器接的是哪個帳號。

`dboem.com` 是 Google Workspace 網域，`ryan.yu@dboem.com` 本身就是 Gmail 信箱，可直接連接。

**第一次寄送前必須先驗證**，不要直接 `send_message`：

1. 改用 `create_draft` 建立草稿（收件者、副本、主旨、內文都照正式內容填）
2. 請使用者到 Gmail 開啟該草稿，確認 **寄件者顯示為 `ryan.yu@dboem.com`**
3. 確認無誤才改用 `send_message` 正式寄出；往後同一連線不必重複驗證

若寄件者仍是個人帳號 `cecyu.tw@gmail.com`，**停止並回報**，不要寄出。請使用者重新授權 Gmail 連接器並改用 `ryan.yu@dboem.com`：Claude Code 走 claude.ai → 設定 → 連接器 → Gmail；Codex 走 `codex plugin` 的 gmail 外掛重新登入。這個 OAuth 動作無法由 agent 代勞。

寄出後回報 message id 與實際收件者，不要只說「已寄出」。
