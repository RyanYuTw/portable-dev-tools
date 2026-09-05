---
name: investment-contact-jira
description: "盤點 Laravel 投資接洽或同類後台功能的實作缺口，生成可驗收任務與進度摘要，並在使用者確認後同步 Jira。"
---

# 投資接洽 Jira 實作同步

## 目的

把程式碼盤點結果轉成可執行、可驗收、可追蹤的 Jira 工作項目。此 skill 只負責需求／實作追蹤，不代替功能開發；若使用者另行要求實作，才修改程式碼。

## 盤點範圍

以目前工作目錄所屬的 repository root 為專案根目錄。先讀取目標頁面、對應 Blade/JS、Controller、Service、Repository、Request、Model、migration 與 Feature tests，再以實際證據判斷狀態。以下 IMS 路徑是已知範例；其他專案須先搜尋實際 feature 名稱與路徑，不可假設結構完全相同：

- `resources/views/admin/investment_contact_p2.blade.php`：列表是否仍為靜態資料、篩選／分頁／操作連結是否帶有實際 ID。
- `resources/views/admin/investment_contact_p2_edit.blade.php` 與 `public/js/admin/pages/investment_contact_p2_edit.js`：表單欄位映射、載入單筆資料、POST／PUT、驗證錯誤、附件上傳與成功後重新導向。
- `resources/views/admin/investment_contact_p2_detail.blade.php` 與 `investment_contact_p2_detail.js`：單筆詳情、期別／關聯資料與唯讀呈現。
- `resources/views/admin/investment_contact_p2_history.blade.php` 與 `investment_contact_p2_history.js`：異動紀錄是否依資源 ID 載入。
- `app/Http/Controllers/Admin/InvestmentContactController.php`、`InvestmentContactService.php`、`InvestmentContactRepository.php`、兩個 Admin Request、`InvestmentContact` model 與 migration：確認後端契約，不重複建立已存在的 CRUD API。
- `tests/Feature/Admin/InvestmentContactCrudTest.php`：把已有 API 測試與缺少的瀏覽器／整合驗收分開列出。

目前已知 API 契約：

- CRUD：`/api/admin/investment-contacts`，需遵守 `admin.investment_contacts.view/edit` 權限。
- 附件：`POST /{id}/attachments`、`GET /{id}/attachments/{attachmentId}/download`、`DELETE /{id}/attachments/{attachmentId}`。
- 共用下拉：`GET /api/admin/lookups?sets[]=program_periods&sets[]=admin_users`；實際欄位以 Controller 回應為準。

## 任務生成規則

只為「目前未完成或無法由現有測試證明完成」的項目建立任務；已完成項目列入進度摘要，不重複建 Jira。每個任務必須包含：

1. `summary`：`[投資接洽] <動詞> <範圍>`。
2. `description`：背景、證據檔案、API／權限、驗收條件、測試方式與完成定義。
3. `labels`：使用繁體中文 `投資接洽`、`自動建立`；同類功能可再加入繁體中文功能標籤，例如 `投資評估統計`。不要新增英文同義 label。
4. `status` 建議：未開始 `待執行`、開發中 `執行中`、測試／待確認 `驗收中`、驗收通過 `已完成`；不能把「已建立 Jira」誤報成「已完成」。
5. `progress`：以已驗收任務數 ÷ 任務總數計算，並列出阻塞原因；只有程式碼、測試與可見驗收證據都具備時才算完成。

投資接洽頁通常拆成以下可獨立驗收的任務，實際數量依盤點結果調整：

- 列表 API 串接：移除硬編碼列，接上篩選、關鍵字、排序、分頁、空狀態與錯誤處理。
- 新增／編輯保存：以欄位白名單組 payload，串接 POST／PUT，處理 422／403，成功後重新載入資料。
- 詳情與異動紀錄：把資源 ID 傳入並載入正確單筆資料與 history，避免固定導向無 ID 頁面。
- 附件與權限：接上上傳／下載／刪除 API，依 view/edit 權限隱藏入口並保留 API 403 防線。
- 自動化驗收：補前端／Feature 測試，覆蓋列表、保存、驗證錯誤、權限、附件與重新整理後資料持久化。

## Jira 同步規則

預設使用 `scripts/sync_jira.py` 走 Jira Cloud REST API v3；只有在環境明確提供 Atlassian MCP connector 時才替換成 MCP adapter。API adapter 的設定、payload 與去重規則見 [references/rest-api.md](references/rest-api.md)。

同步前先確認使用者指定的 Jira project key；未指定時使用 `JIRA_PROJECT_KEY`，只有既有環境明確以 `KAN` 為預設時才沿用。以 JQL 讀取目標專案中帶有 `投資接洽` label 的 issue，再以完整 summary 去重；相容舊資料時可同時查詢既有 `investment-contact` label，但新建或更新 issue 一律寫入繁體中文 label。不可只用序號或建立時間判斷。預設為 dry-run，只有使用者明確要求同步且執行 `--apply` 時才寫入。若無法確認 project key、issue type、狀態名稱或欄位，不猜測，先回報阻塞。

Jira 寫入是對第三方的代表性操作。完成任務草稿、去重檢查與欄位預覽後，必須在即將按下建立／提交前向使用者確認；確認內容要明確列出將建立或修改的 issue 數量、標題、專案與狀態。未確認前只做讀取與本地產物。

同步完成後重新以 API 讀取 Jira，逐筆取得 issue key、URL、狀態與進度，並回報「本地盤點進度」和「Jira 追蹤進度」兩者，不把建立成功視為實作完成。建立 issue 的 REST API 回應只代表追蹤項目建立成功；狀態轉換必須另外讀取 transitions 並以名稱精確匹配。

## 輸出格式

先輸出一份任務清單，再輸出進度摘要：

```text
盤點範圍：investment_contact_p2
任務：N 項；已完成 A；進行中 B；待執行 C；阻塞 D
進度：A/N（僅驗收完成項計入）

每項：
- summary
- evidence
- acceptance criteria
- test command / verification
- local status
- Jira key（同步後填入）
```

不要把 `.kiro/specs` 中其他 feature 的需求直接套用到投資接洽；先確認 feature name 與資料表是否一致。
