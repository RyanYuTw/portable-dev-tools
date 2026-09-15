---
name: jira-breakdown
description: 依需求自動拆解為 Jira 任務與子任務，估算日期與優先順序、判定類別與標籤、詢問指派對象後開票。用於「把這個需求拆成 Jira ticket」「幫我開票」「拆解任務」。
---

# 需求拆解與 Jira 開票

把一個需求轉成可獨立驗收的 Jira 工作項目。本 skill 只管理工作項目，不實作產品程式碼。

## 分析功能範圍

以使用者提供的頁面、需求、issue、設計或檔案為功能邊界，只查閱相關的路由、UI、controller/handler、service、資料持久層、權限、整合與測試證據。若可連線到 live page，對照可見行為、程式碼與 API 行為。

每項能力分類為：

- `已完成`：實作、自動化測試與可觀察驗證均存在。
- `執行中`：已有實作，但驗收證據尚不完整。
- `待執行`：缺少實作或仍是 placeholder/static 行為。
- `阻塞`：依賴未解決的外部決策或不可用的依賴。

只為未完成或尚未證明的工作建立 Jira，不要把已完成能力重複開票。

## Repository and feature naming

每張票都以實際落地的 repository 與功能命名：

- `{repo-name}`：優先取 `basename -s .git "$(git remote get-url origin)"`，沒有 remote 時取 repository 根目錄名稱；保留原始大小寫，例如 `ims`、`aims-front`。
- `{function-name}`：本批的功能邊界，以繁體中文命名且不含空白，因 Jira label 不接受空白。

summary 一律是 `[{repo-name}] 動詞＋可交付結果`，功能名稱寫進標題本身而不是另開一個中括號（例：`[ims] 案件合併加上授權檢查並回傳 403`）。

每張 draft 必須包含：summary、description（背景、repository evidence、契約／權限、驗收標準、驗證方式與完成定義）、labels、local status、verification，以及 assignee。避免「完成前端」或「處理 API」等無法驗收的描述。

## 目標環境

- 組織共用 Jira 目標預設為 `https://dboem.atlassian.net/jira/core/projects/KNDU/board`，不同 repository／產品專案都寫入 Jira project `KNDU`；repository 名稱只用於 summary 與 labels，不要拿來當 Jira project key。
- 仍須以 Jira metadata 回讀確認 site、cloudId、issue type、required fields、labels、assignee 與 workflow；若使用者提供其他 Jira project 或 board，依明確指定覆寫預設。
- 建立前確認目標 board 與 Sprint／Backlog。Jira issue 建立不代表已進入看板或 Sprint；若使用者要求放入特定 Sprint，建立後要執行加入 Sprint 並回讀驗證。
- 狀態轉移必須先讀取該 project 可用的 transition，依回傳的名稱與 ID 操作；不可猜測跨 project 的 transition ID。

## 階層只有兩層

**Jira 在此專案無法再往下拆第三層**，沒有 Epic，子任務底下不能再有子任務。

若拆解結果出現第三層，不要嘗試建立，改為：

- 把第三層併入所屬子任務的**驗收標準**，每條對應一個可觀察行為；或
- 若第三層各自可獨立驗收，把該子任務升格為 `任務`，第三層成為它的子任務。

拆完後檢查：每個 `子任務` 都必須有 `parent`（必填欄位）。

## 欄位自動填寫

| 欄位 | fieldId | 規則 |
|---|---|---|
| 優先順序 | `priority` | 阻擋他人或線上問題→`2` High；一般功能→`3` Medium（預設）；可延後→`4` Low。只有正式事故才用 `1` Highest |
| 開始日期 | 由 project metadata 取得 | 依相依順序排程，第一項為今天 |
| 截止日期 | `duedate` | 開始日期 + 難度天數 |
| 類別 | 由 project metadata 取得 | 依 Jira project 實際欄位與選項設定分類，不可沿用其他 project 的 field／option ID |
| 標籤 | `labels` | `{repo-name}` + `{function-name}` + 1～3 個實際觸及面向（`前端`／`後端`／`API`／`資料庫`／`權限`／`測試`／`文件`／`設定`）。標籤不得含空白，**不要**加 `自動建立` |
| 受託人 | `assignee` | 見下方詢問流程 |

難度對應天數：單一檔案的小改動 1 天；跨 UI／API／持久層的一般功能 3 天；牽涉權限、資料遷移或外部整合 5 天。排程時**跳過週六日**。

類別與其他 custom field 必須先讀取 project／issue type metadata，再依回傳的 field ID 與 option ID 寫入。**不要嘗試用 API 新增選項**，寫入不存在的值會被拒絕。既有票不回填類別。

## 指派對象

開票前用 AskUserQuestion 問一次，涵蓋本批所有票：

- 組織預設受託人為 `ryan.yu@dboem.com`；仍須在建立 payload 明確寫入每張票，使用者指定其他人時以指定為準。
- 其他候選用 `lookupJiraAccountId` 查，並以 Jira account ID 寫入。
- 使用者可指定「整批同一人」或「逐張指定」

沒得到答覆前不要開票。

## 驗收標準必須可執行

寫驗收標準時，把「要做到什麼」與「做到它需要先有什麼」一起寫進去。實際發生過的兩種漏寫：

- **漏掉前置步驟**：寫了「編輯送出呼叫 PUT」，卻沒寫「先載入既有資料回填表單」。少了載入，
  送出會把未填欄位清空——驗收標準本身變成不安全的作法。
- **漏掉可及性**：寫了「表單送出」，卻沒確認表單是否具備必填欄位、欄位是否有 `name` 可讀取。
  補這些往往才是主要工作量，漏寫會讓估時嚴重失準。

開票前對每條驗收標準自問：照這條做下去，中途會不會卡在某個票上沒寫的前置條件？
會的話，把那個前置條件也寫成一條驗收標準。

## 開票前預覽

列出完整任務清單與進度摘要，並額外列出本 skill 自動決定的欄位，讓使用者在寫入前能一眼看出日期、優先序與受託人是否合理：

```text
盤點範圍：<feature>
任務：N 項（任務 X／子任務 Y）；已完成 A；進行中 B；待執行 C；阻塞 D

每項：summary｜類別｜優先序｜開始→截止｜受託人｜parent
```

## 寫入後

回讀每張受影響的票，確認 key、URL、status、labels、assignee、類別、日期與 parent。**不要**把「已開票」當成實作進度——完成度一律由子任務完成件數決定（Jira 原生計算）。

Commit／MR 追蹤必須使用 Jira Remote Link 寫入對應票的 Web links；不要用留言代替。若 GitLab 整合會自動掛連結，仍要在寫入後回讀確認；未掛上時，取得可用的 commit／MR URL 後補寫 Remote Link。
