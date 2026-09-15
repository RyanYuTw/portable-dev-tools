---
name: jira-ticket-plan
description: 依 Jira ticket 編號讀取需求內容，對照儲存庫現況後規劃執行步驟與做法，經使用者確認才開始實作。用於「PROJ-xxx 要怎麼做」「幫我規劃這張票」「開始做 PROJ-xxx」。
---

# 依 Jira ticket 規劃執行

輸入一個或多個 ticket 編號（如 `PROJ-228`），產出可執行的實作計畫，**確認後才動手**。

## 1. 讀取票的完整脈絡

用 Atlassian MCP 從 ticket URL 或已驗證的 Jira site 取得 cloudId，並讀取：

- 該票的 summary、description、狀態、受託人、標籤、類別、起訖日期
- 若是子任務，一併讀父任務與**所有兄弟子任務**——相鄰的票常決定介面契約與先後順序
- `listJiraIssueRemoteIssueLinks`：已掛上的 commit 連結代表這張票已經動過，不要重做

description 裡通常已有「背景／既有後端佐證／驗收標準／驗證方式／Definition of Done」五段，那是規劃的主要依據。

## 2. 對照儲存庫現況

不要相信票上的描述就是現況。實際查證：

- 票裡點名的檔案、路由、Service、測試是否已存在、內容是否已符合驗收標準
- 用票的關鍵字搜尋真正的執行路徑，不要臆測框架慣例
- 若票描述與程式碼不符，**以程式碼為準**並在計畫中指出落差

目標是回答：驗收標準中哪幾條已經滿足、哪幾條還沒。

### 這個儲存庫已知會騙人的地方

實際踩過、每次都要查證的三件事：

1. **路由前綴**。票的描述常寫成 `POST /admin/xxx`，但 `routes/web.php` 把 CRUD 包在
   `Route::prefix('api/admin')` 群組裡，真正的路徑是 **`/api/admin/xxx`**。以 `$apiCrud`
   的定義與測試檔實際打的路徑為準，不要照抄票面。
2. **必填欄位在畫面上未必存在**。先讀 FormRequest 找出 `required` 欄位，再回頭確認表單
   真的有對應的輸入元素。少一個必填欄位，整個送出流程永遠 422，這是阻塞而非細節。
3. **表單欄位是否可定址**。靜態原型常大量缺少 `name` 與 `id`：
   `grep -cE '<(input|select|textarea)' 檔案` 對比 `grep -cE '<(input|select|textarea)[^>]*name='`，
   差距就是要補的工作量。這通常才是票的主體，而票面往往沒提。

## 3. 產出計畫

進入 plan mode 後提出，內容包含：

- **現況**：逐條驗收標準標記 已滿足／未滿足／需確認，附檔案與行號證據
- **步驟**：每步說明改哪個檔案、做什麼、為何需要。依相依性排序
- **驗證方式**：票上指定的測試指令；沒有就提出可觀察的檢查方法
- **風險與落差**：與票描述不符之處、需要使用者決定的事項
- **範圍外**：明確列出這張票不該碰的東西

若該功能在 `.kiro/specs/` 已有對應 spec，改走 `/kiro-impl`，本 skill 只負責把票對應到 spec 並說明。

## 4. 等待確認

**得到使用者同意前不要修改任何檔案。** 若計畫中有需要使用者決定的分歧，在此一併問清楚。

## 5. 執行

確認後依步驟實作。過程中：

- 狀態轉移交給 commit hook 提示或 Jira skill 處理，**不要猜測 transition ID**。提交後若票仍在未開始狀態，讀取該 Jira project 的 transitions，依實際名稱與 ID 轉為進行中，並**一併檢查父任務**——只要任一子任務是進行中或完成，父任務就不該停在未開始狀態。hook 由 `scripts/install-git-hooks.sh` 安裝到 `.git/hooks/post-commit`，對 Codex、Claude Code 與純終端機 git 一律生效
- 子任務標記完成一律需要使用者同意，不可自行判定
- commit 訊息必須含完整票號（例如 `PROJ-228`，大寫、有連字號），否則 GitLab 不會回寫 Jira
- **commit 之前先問一句「要先看 git diff 嗎？」**。預設不顯示：使用者說不用、沒回應或非互動情境就直接 commit；說要看才輸出 `git diff --staged`（改動大時先給 `--stat` 摘要再給全文），等使用者反應後再 commit。每次 commit 只問一次，改動再小也要問。這是複查點不是許可閘門，使用者看完沒有要求修改就照原計畫 commit
- 推送前會被 review 閘門攔下，那是預期行為。跑完 review 或使用者選擇略過後，把 HEAD 的完整 SHA 寫入 `.claude/state/reviewed` 即放行
- **push 成功之後再問一句「要發 merge request 嗎？」**。預設不發：使用者說不用、沒回應或非互動情境就只回報推送結果。要發才用 GitLab MCP `create_merge_request`（專案由 `git remote get-url origin` 推得、不要臆測，source 為目前分支、target 為專案預設分支，標題帶票號如 `KNDU-228`，描述寫改動摘要與驗證方式），建立後回報 MR 連結。推送沒成功就不要問；該分支已有開啟中的 MR 就直接回報既有連結，不要重複開。不要自行 merge、approve 或指派審核者
