# AI × Jira × GitLab 工作流設定與操作手冊

> 適用案例：GitLab https://gitlab.dbodm.com/laravel/ims 搭配 Jira KNDU 專案。
>
> 版本：2026-09-07
>
> 目的：讓 AI 讀取 GitLab repo 與開發需求，自動拆成可驗收的 Jira 子任務，提出負責人、優先順序與預估工時；開發期間再用 Jira key 對應 branch、commit、Merge Request（MR）與工作紀錄。

## 1. 先看懂整體流程

~~~mermaid
flowchart LR
    A["需求或維護描述"] --> B["AI 讀取 GitLab repo"]
    B --> C["盤點 routes、controller、service、model、test"]
    C --> D["拆成可驗收的 Jira 任務"]
    D --> E["推薦負責人、優先順序、工時"]
    E --> F{"使用者確認預覽"}
    F -- "否" --> D
    F -- "是" --> G["建立或更新 Jira"]
    G --> H["建立含 Jira key 的 branch"]
    H --> I["建立含子任務 key 的 commit"]
    I --> J["MR 描述包含 Jira key"]
    J --> K["回寫 comment、worklog、status"]
    K --> L["讀回 Jira 驗證"]
~~~

核心原則：

1. AI 可以自動分析與提出計畫，但建立 Jira、指派人員、修改優先順序、記工時與轉換狀態都屬於外部寫入。
2. 寫入前先顯示完整預覽；確認後才執行。
3. 「程式實作完成」與「Jira ticket 已建立」是兩種不同的進度，不可混為一談。
4. 所有 branch、commit、MR 都要包含 Jira key，例如 KNDU-123。
5. Token、密碼、Cookie、Jira account ID 清單不要提交到 repo，也不要貼進 Jira 描述。

## 2. 本案例的固定資訊

| 項目 | 值 | 備註 |
|---|---|---|
| Jira URL | https://dboem.atlassian.net/jira/core/projects/KNDU/board | 目標 project key 暫定為 KNDU，仍需用權限驗證 |
| GitLab URL | https://gitlab.dbodm.com/laravel/ims | self-hosted GitLab |
| GitLab API URL | https://gitlab.dbodm.com/api/v4 | MCP 使用 API，不是網頁 URL |
| GitLab encoded project path | laravel%2Fims | REST/MCP 傳入 project path 時使用 |
| Repo 本地副本 | /Users/ryanai/Documents/dboem/ims | 依目前工作區盤點結果 |
| Jira Issue Type | 待驗證 | 不要直接猜 Task；先查 project metadata |
| Jira 狀態名稱 | 待驗證 | 不要直接猜 To Do、In Progress 等名稱 |
| Jira 成員 account ID | 待建立對照表 | Jira 指派通常需要 account ID，不是顯示名稱 |

### 本次盤點結果

- 目前 Atlassian MCP 授權回傳的 site 是 dboem-team-hi2tga74.atlassian.net，與需求提供的 dboem.atlassian.net 不同；在該授權下查不到 KNDU。請先重新登入正確的 Atlassian site，或確認 KNDU 是否位於另一個 Jira site。
- 目前 GitLab MCP 回傳 401 Unauthorized；請補上可讀取 gitlab.dbodm.com 的 Personal Access Token。
- 沒有建立 Jira ticket、沒有修改 Jira、沒有修改 GitLab。
- 本地 repo 已存在使用者自己的修改，手冊產出未碰觸這些修改。

## 3. 安裝前需要準備什麼

### 3.1 Jira 權限

至少需要：

- Browse/View project：讀取 KNDU 專案、Issue、狀態、成員。
- Create Issues：建立 Story/Task/Bug 或 Sub-task。
- Edit Issues：更新描述、labels、priority、assignee、original estimate。
- Transition Issues：把 ticket 轉為 In Progress、In Review、Done 等實際存在的狀態。
- Add Worklog：回寫實際工作時間時才需要。

Jira 的 KNDU、Issue Type、required fields、priority 名稱與 transition ID 依 workspace 設定而不同；一定要由 MCP metadata 查詢，不要從別的專案複製猜測。

### 3.2 GitLab Personal Access Token

#### 3.2.1 取得 Token 的位置

請使用瀏覽器登入公司的 GitLab：

`https://gitlab.dbodm.com`

登入後依序開啟右上角頭像 → **Edit profile** → 左側 **Access** → **Personal access tokens**。在 **Generate token** 下拉選單選擇 **Legacy token**（若該版本有顯示），填入 Token 名稱、說明、到期日及 scopes，最後按 **Generate token**。GitLab 官方說明請參考 [Personal access tokens](https://docs.gitlab.com/user/profile/personal_access_tokens/)。

建議使用容易辨識的名稱，例如：

`portable-dev-tools-mcp-<電腦名稱>`

Token 產生後只會完整顯示一次，請立即複製並保存；離開頁面或重新整理後，通常無法再次查看原值，只能撤銷後重新建立。到期日依公司政策設定；GitLab Self-Managed 管理員也可能限制最長有效期限。

#### 3.2.2 權限怎麼選

先從最小權限開始：

- 只讀分析：read_api、read_repository。
- 若只需要查詢目前登入者，可另外加入 read_user。
- 需要由 MCP 透過 GitLab API 寫入資料（例如建立或更新 note、MR 等）：依 GitLab 版本與 MCP 工具需求，可能需要 api；此權限範圍較大，應先由 GitLab 管理員核准。
- write_repository 主要是 Git-over-HTTP 的 repository push 權限，不能當成一般 GitLab API 寫入權限；請依實際操作需求選擇。各 scope 的差異請參考 [GitLab access token scopes](https://docs.gitlab.com/security/tokens/access_token_scopes/)。

本工作流的 GitLab MCP 設定預設只讀取環境變數 `GITLAB_PERSONAL_ACCESS_TOKEN`，並連線到：

`https://gitlab.dbodm.com/api/v4`

#### 3.2.3 Token 應該放在哪裡

推薦順序如下：

1. 作業系統的 Secret Manager（macOS 見 3.2.3.1、Windows 見 3.2.3.2）或公司核准的密碼管理工具。
2. 啟動 Codex、Claude Code 前，由 Keychain 注入環境變數 `GITLAB_PERSONAL_ACCESS_TOKEN`。
3. 僅限本機測試的 `.env` 或 shell 設定檔；該檔案不可提交到 Git。

#### 3.2.3.1 寫入 macOS Keychain（推薦）

macOS 內建的 **Keychain Access（鑰匙圈存取）** 可以保存 GitLab Personal Access Token 或其他 API Key。圖形介面位置是：開啟「Keychain Access」→ 左側選擇 **login** → 類別選 **Passwords** → 選單 **File → New Password Item**；將 **Keychain Item Name** 設為服務名稱、**Account Name** 設為目前 macOS 使用者，並把 Token/API Key 填入 Password。

也可以使用 Terminal，以下範例會讓 `security` 互動式要求輸入密碼，不會把實際 Token 放在指令參數或 shell history：

~~~bash
KEYCHAIN_SERVICE="portable-dev-tools.gitlab.personal-access-token"
security add-generic-password \
  -a "$USER" \
  -s "$KEYCHAIN_SERVICE" \
  -U \
  -w
~~~

執行後貼上 GitLab Token 並按 Enter。`-U` 代表同一個服務已存在時更新它。其他 API Key 也使用相同方式，只要換成不同的服務名稱，例如 `portable-dev-tools.jira.api-token`；不要在同一個服務名稱下混放不同用途的密鑰。

從 Keychain 讀取並提供給 GitLab MCP：

~~~bash
KEYCHAIN_SERVICE="portable-dev-tools.gitlab.personal-access-token"
export GITLAB_PERSONAL_ACCESS_TOKEN="$(security find-generic-password \
  -a "$USER" \
  -s "$KEYCHAIN_SERVICE" \
  -w)"
claude --plugin-dir /Users/ryanai/plugins/portable-dev-tools
~~~

如果啟動 Codex，請在啟動 Codex 的同一個 Terminal 執行相同的 `export`；MCP 會透過 `.mcp.json` 的 `${GITLAB_PERSONAL_ACCESS_TOKEN}` 取得值。工作完成後可執行 `unset GITLAB_PERSONAL_ACCESS_TOKEN` 清除目前 Terminal 的環境變數。不要使用 `-A` 讓所有程式無提示存取 Keychain，除非公司安全規範明確要求。

portable-dev-tools 的 `.mcp.json` 只保留環境變數引用，不放真實 Token：

~~~json
{
  "env": {
    "GITLAB_PERSONAL_ACCESS_TOKEN": "${GITLAB_PERSONAL_ACCESS_TOKEN}",
    "GITLAB_API_URL": "https://gitlab.dbodm.com/api/v4"
  }
}
~~~

`.env.example` 只能放變數名稱，例如 `GITLAB_PERSONAL_ACCESS_TOKEN=`，不能填入實際值。Claude Code 或 Codex 啟動前，在同一個 Terminal 設定環境變數，之後重啟工具讓 MCP 進程取得新值：

~~~bash
read -s 'GITLAB_PERSONAL_ACCESS_TOKEN?GitLab Token: '
export GITLAB_PERSONAL_ACCESS_TOKEN
claude --plugin-dir /Users/ryanai/plugins/portable-dev-tools
~~~

若使用 Codex，則在啟動 Codex 的 Terminal 設定同一個變數；不要把真實 Token 寫進 `.mcp.json`、README.md、SKILL.md、Jira description、commit message、Git history 或截圖。也避免直接把真實 Token 打在會被 shell history 保存的指令中，正式環境應改用 Secret Manager 或互動式安全注入。

#### 3.2.3.2 寫入 Windows Secret Store（推薦）

Windows 沒有 Keychain，對應做法有兩種，擇一即可。兩者都只有**你這個 Windows 帳號**解得開，設定檔裡留下的也只是「去哪裡拿」，不是 Token 本身。

**方式 A：PowerShell SecretManagement（等價於 Keychain）**

只需要安裝一次：

~~~powershell
Install-Module Microsoft.PowerShell.SecretManagement,
  Microsoft.PowerShell.SecretStore -Scope CurrentUser

Register-SecretVault -Name LocalStore `
  -ModuleName Microsoft.PowerShell.SecretStore -DefaultVault
~~~

存入 Token。使用 `Read-Host -AsSecureString` 互動式輸入，Token 不會留在 PowerShell history：

~~~powershell
Set-Secret -Name GITLAB_PERSONAL_ACCESS_TOKEN `
  -Secret (Read-Host -AsSecureString)
~~~

取用。把這兩行放進 PowerShell profile，路徑用 `$PROFILE` 查：

~~~powershell
$env:GITLAB_PERSONAL_ACCESS_TOKEN =
  Get-Secret -Name GITLAB_PERSONAL_ACCESS_TOKEN -AsPlainText
~~~

其他金鑰換一個 `-Name` 即可，例如 `JIRA_API_TOKEN`；不要在同一個名稱下混放不同用途的密鑰。

**方式 B：DPAPI 加密檔（不需安裝模組）**

`ConvertFrom-SecureString` 使用 Windows 內建的 DPAPI 加密，結果只有同一個帳號在同一台機器解得開，複製到別台機器無效：

~~~powershell
Read-Host -AsSecureString |
  ConvertFrom-SecureString |
  Set-Content "$env:USERPROFILE\.gitlab-pat"
~~~

取用（同樣放進 `$PROFILE`）：

~~~powershell
$sec = Get-Content "$env:USERPROFILE\.gitlab-pat" |
  ConvertTo-SecureString
$env:GITLAB_PERSONAL_ACCESS_TOKEN =
  [Net.NetworkCredential]::new("", $sec).Password
~~~

**最後手段：明文使用者環境變數（僅限本機測試）**

對應 3.2.3 優先順序的第 3 項。它把 Token 明文寫進登錄檔 `HKCU\Environment`，任何以你身分執行的程式都讀得到，所以到期日不要設長，scope 只勾 `read_api`：

~~~powershell
[Environment]::SetEnvironmentVariable(
  "GITLAB_PERSONAL_ACCESS_TOKEN",
  "glpat-...",
  "User")
~~~

第三個參數 `"User"` 只影響你這個帳號。不要用 `"Machine"`，那會套用到整台機器並需要系統管理員權限。圖形介面等價做法：按 `Win` + `R` 輸入 `sysdm.cpl` → 「進階」→「環境變數」→ **上半部**的「使用者變數」→「新增」，三層視窗都要按「確定」。cmd 的 `setx` 也可以，但目前這個視窗讀不到，要另開新視窗。

**三個 Windows 專屬注意事項**

1. **已開著的程式讀不到新值。** 環境變數是行程啟動時繼承的。Cursor、VS Code、終端機都要完全關閉再開；從開始功能表啟動的 GUI 程式有時要登出再登入。這是「明明設好了卻一直 401」最常見的原因。
2. **Git Bash 自成一國。** 它讀 `~/.bashrc`，不讀 PowerShell profile；從 GUI 啟動的 Codex、Cursor 讀的是使用者環境變數，也不讀 Git Bash 的設定。三者要分開設。
3. **WSL 不繼承 Windows 端的設定。** 在 WSL 內執行時，照 3.2.3 的優先順序設在 WSL 自己的環境（`secret-tool` 或 `~/.bashrc`）。

#### 3.2.4 測試 Token 是否可用

設定環境變數並重啟工具後，先用 GitLab MCP 執行 `whoami`，再讀取 `laravel/ims` 專案。若用命令列測試，可使用下列只讀 API 請求：

~~~bash
curl --fail --silent --show-error \
  --header "PRIVATE-TOKEN: ${GITLAB_PERSONAL_ACCESS_TOKEN}" \
  "https://gitlab.dbodm.com/api/v4/projects/laravel%2Fims"
~~~

Windows（PowerShell）：

~~~powershell
curl.exe --fail --silent --show-error `
  --header "PRIVATE-TOKEN: $env:GITLAB_PERSONAL_ACCESS_TOKEN" `
  "https://gitlab.dbodm.com/api/v4/projects/laravel%2Fims"
~~~

PowerShell 裡的 `curl` 是 `Invoke-WebRequest` 的別名、參數完全不同，一定要打 `curl.exe`（Windows 10 1803 以後內建）；行尾的反引號是 PowerShell 的換行符號，不是 bash 的反斜線。若只想確認變數是否載入而不顯示 Token，可用 `$env:GITLAB_PERSONAL_ACCESS_TOKEN.Length`。

`401 Unauthorized` 通常表示 Token 未載入、已過期或無效；`404 Not Found` 可能表示專案路徑錯誤，或 Token 所屬帳號沒有該專案的存取權。測試輸出不要貼到公開頻道。

#### 3.2.5 到期與撤銷

Token 到期或疑似外洩時，回到同一個 **Personal access tokens** 頁面撤銷舊 Token，建立新 Token，更新 Secret Manager 或環境變數，再重啟 Codex/Claude Code。確認新 Token 已能讀取專案後，再撤銷舊 Token。

Token 只放在環境變數或 Codex 的安全設定，不要放在：

- README.md、SKILL.md、Jira description、commit message。
- .env.example 的真實值。
- Git history、shell command、螢幕截圖。

### 3.3 建議的 Jira 成員對照表

建立一份只放在本機或受控的秘密管理工具中的設定。不要把真實 account ID 直接提交到公開 repo。

~~~yaml
# ~/.config/ai-workflow/owners.yml
owners:
  backend:
    display_name: "後端主要維護者"
    jira_account_id: "替換成由 Jira lookup 查到的 account ID"
    paths:
      - "app/Http/Controllers/**"
      - "app/Services/**"
      - "app/Models/**"
  frontend:
    display_name: "前端主要維護者"
    jira_account_id: "替換成由 Jira lookup 查到的 account ID"
    paths:
      - "resources/js/**"
      - "resources/views/**"
  qa:
    display_name: "測試/驗收負責人"
    jira_account_id: "替換成由 Jira lookup 查到的 account ID"
    paths:
      - "tests/**"

default_assignee:
  display_name: "專案維護者"
  jira_account_id: "替換成已核准的 fallback account ID"
~~~

如果 AI 無法從 CODEOWNERS、最近 commit、目錄負責人或上述對照表得到可信的結果，應標示「待人工指定」，不可自行捏造人員。

## 4. MCP 設定

MCP 是讓 AI 呼叫 Jira/GitLab 工具的連接層。此案例需要兩個 server：

- atlassian：查詢與寫入 Jira。
- gitlab：讀取 repo/commit/MR，必要時寫入 MR note 或其他 GitLab 資料。

### 4.1 方式 A：使用已安裝的 Atlassian connector

如果 Codex 已安裝 Atlassian Rovo/Atlassian connector，先登入正確的 Jira site：

~~~bash
codex mcp login atlassian
~~~

登入後重新啟動 Codex，確認能取得：

~~~text
mcp__atlassian__getAccessibleAtlassianResources
mcp__atlassian__getVisibleJiraProjects
mcp__atlassian__getJiraProjectIssueTypesMetadata
~~~

如果結果仍只有 dboem-team-hi2tga74.atlassian.net 而沒有 dboem.atlassian.net，請不要建立 ticket；先重新授權正確 site。

### 4.2 方式 B：GitLab 的 MCP 設定

本案例的 GitLab MCP server 範例：

~~~json
{
  "mcpServers": {
    "gitlab": {
      "command": "npx",
      "args": ["-y", "@zereight/mcp-gitlab"],
      "env": {
        "GITLAB_PERSONAL_ACCESS_TOKEN": "${GITLAB_PERSONAL_ACCESS_TOKEN}",
        "GITLAB_API_URL": "https://gitlab.dbodm.com/api/v4"
      }
    },
    "atlassian": {
      "type": "http",
      "url": "https://mcp.atlassian.com/v2/mcp"
    }
  }
}
~~~

在使用 .mcp.json 的 MCP client 中，可放在 plugin 或使用者設定目錄；不要把含有真實 Token 的檔案加入 Git。

### 4.3 Codex config.toml 範例

某些 Codex 安裝會使用 ~/.codex/config.toml。請先備份，再依目前版本支援的格式加入 GitLab server；保留原本其他設定：

~~~toml
[mcp_servers.gitlab]
command = "npx"
args = ["-y", "@zereight/mcp-gitlab"]
startup_timeout_sec = 120

[mcp_servers.gitlab.env]
GITLAB_PERSONAL_ACCESS_TOKEN = "${GITLAB_PERSONAL_ACCESS_TOKEN}"
GITLAB_API_URL = "https://gitlab.dbodm.com/api/v4"
~~~

如果目前版本不支援 ${GITLAB_PERSONAL_ACCESS_TOKEN} 這種插值，請改用 MCP client 的 secret/environment injection，不要把 token 明文寫進 TOML。

### 4.4 設定環境變數

macOS/zsh 測試用法：

~~~bash
export GITLAB_PERSONAL_ACCESS_TOKEN='只在目前 shell 暫時存在的 token'
~~~

若要永久設定，請使用公司核准的 secrets manager 或使用者 shell 私有設定；不要把下列指令貼進 repo 文件：

~~~bash
# 只展示變數名稱，不要把真實值提交到 repo
printenv GITLAB_PERSONAL_ACCESS_TOKEN
~~~

設定完成後，重新啟動 Codex，再做唯讀測試：

~~~text
請用 GitLab MCP 查詢目前登入者，以及專案 laravel/ims 的名稱、default branch 和可見性；不要修改任何資料。
~~~

成功的最低條件：whoami 不再回 401，get_project(project_id="laravel%2Fims") 能回傳 project。

## 5. 第一次驗證連線：只讀，不寫入

依序執行下列檢查。任何一步失敗，都先處理權限，不要跳到建立 ticket。

### 5.1 Jira

~~~text
請使用 Atlassian MCP：
1. 取得可用的 cloudId 與 site URL。
2. 查詢 project key KNDU。
3. 讀取 KNDU 可建立的 issue types、required fields、priority 選項與 workflow 狀態。
4. 查詢以下 Jira 使用者的 account ID：<姓名清單>。
只讀，不建立、不更新、不轉換狀態。
~~~

對應工具概念：

~~~text
getAccessibleAtlassianResources
getVisibleJiraProjects(cloudId, searchString="KNDU")
getJiraProjectIssueTypesMetadata(cloudId, projectIdOrKey="KNDU")
getJiraIssueTypeMetaWithFields(cloudId, projectIdOrKey="KNDU", issueTypeId="由上一個結果取得")
lookupJiraAccountId(cloudId, name/email="由使用者提供")
~~~

### 5.2 GitLab

~~~text
請使用 GitLab MCP：
1. 取得目前登入者。
2. 讀取 laravel/ims 專案 metadata。
3. 讀取 default branch 的第一層檔案。
4. 讀取最近 10 筆 commit，僅列出 hash、subject、author、日期。
只讀，不建立 branch、不修改檔案、不建立 MR。
~~~

對應工具概念：

~~~text
whoami()
get_project(project_id="laravel%2Fims")
get_repository_tree(project_id="laravel%2Fims", ref="default branch", per_page=100)
list_commits(project_id="laravel%2Fims", ref_name="default branch", per_page=10, trailers=true)
~~~

## 6. AI 如何分析需求並拆成 Jira 子任務

### 6.1 解析範圍

AI 不應只依需求標題猜測。應沿著實際 runtime path 盤點：

- routes：入口 URL、HTTP method、middleware。
- controller/handler：輸入驗證、授權、回應格式。
- service/domain：商業規則、狀態轉換、交易。
- model/repository/migration：資料欄位、索引、關聯。
- views/frontend：畫面行為、欄位與錯誤訊息。
- tests：既有的驗收證據與缺口。
- permissions/integrations：角色權限、郵件、檔案、外部 API。

### 6.2 任務分類

每一項能力分成：

- 已完成：實作、automated tests、可觀察驗證都存在。
- 執行中：已有部分實作，但驗收證據不完整。
- 待執行：功能或測試尚未完成。
- 阻塞：需要外部決策、權限或不可用依賴。

只替執行中、待執行、阻塞建立 Jira draft；已完成只放在進度摘要，避免重複建票。

### 6.3 子任務切分原則

以「可獨立交付及驗收的行為」切分，而不是把每個檔案各建一票。例如「新增案件合併功能」可以有：

1. 後端建立合併 API 與授權規則。
2. 資料庫保存合併關係與唯一性限制。
3. 前端顯示可合併案件與確認流程。
4. 補齊成功、重複、無權限與不存在案件的測試。

不要建立「完成前端」「完成後端」這種無法驗收的模糊任務。

### 6.4 每個 Jira draft 必須包含

~~~yaml
summary: "[ims] 新增案件合併 API 與授權驗證"
description:
  background: "為避免重複案件，需要讓授權使用者將兩筆案件合併。"
  repository_evidence:
    - "routes/api.php: 找到案件 API 入口"
    - "app/Services/CaseFollowupService.php: 既有案件服務"
    - "tests/Feature/...: 目前缺少合併成功與無權限測試"
  acceptance_criteria:
    - "授權角色可以合併兩筆有效案件"
    - "非授權角色收到 403，且資料不變"
    - "同一案件不可與自己合併"
    - "重複操作不產生第二筆關係"
  verification:
    - "php artisan test --filter=CaseMerge"
  definition_of_done:
    - "程式碼完成並通過測試"
    - "MR 描述包含 KNDU-123"
labels: ["ims", "案件合併", "後端"]
local_status: "待執行"
assignee_recommendation: "依 owners.yml 或 CODEOWNERS 推薦"
priority_recommendation: "High"
estimate_recommendation: "6h"
~~~

## 7. 自動指派、優先順序與預估工時

### 7.1 指派規則

建議順序：

1. 明確指定的需求負責人。
2. CODEOWNERS 或目錄 owner。
3. 最近負責相關路徑且有成功合併紀錄的人。
4. owners.yml 的路徑規則。
5. 專案 fallback 維護者。

AI 應在預覽列出「證據」與「信心」。例如：

~~~text
推薦 assignee：後端主要維護者
依據：本任務修改 app/Services/ 與 tests/Feature/；最近 10 次相關 commit 有 7 次由該維護者完成
信心：中
~~~

帳號對應必須用 Jira lookup 查回 account ID。顯示名稱相同、離職帳號、沒有 project permission 都要停止並要求人工確認。

### 7.2 優先順序規則

這是一個可審查的初始規則，不是取代產品負責人的決策：

| 條件 | 建議 priority |
|---|---|
| 資安漏洞、資料毀損、正式環境全面中斷 | Highest |
| 核心流程阻斷、主要客戶無法操作、資料正確性風險 | High |
| 一般功能、正常維護、可繞行問題 | Medium |
| 文件、低風險整理、非阻斷性改善 | Low |

如果 Jira 使用的是 Blocker/Major/Minor 或其他名稱，以 metadata 回傳的名稱為準，不要硬寫 Highest。

### 7.3 預估工時

先估可驗收工作，不要只估寫 code 的時間：

~~~text
總工時 = 分析 + 實作 + 測試 + code review/MR 修正 + 部署/驗收緩衝
~~~

初始估算表：

| 類型 | 參考範圍 |
|---|---:|
| 小型設定/文件/單一測試修正 | 0.5–2h |
| 單一路徑的 bug fix | 2–4h |
| 單一 API 或頁面，含測試 | 4–8h |
| 跨 API、資料庫、前端與權限 | 1–3d |
| 不熟悉的跨模組重構或外部整合 | 3d 以上，先拆更小任務 |

Jira 的 original estimate 欄位可能是 timetracking.originalEstimate，也可能被管理員改成 custom field。先查 issue type field metadata；確認欄位名稱後才寫入。若查不到，保留在 Jira description 的「AI 建議工時」，不要假裝已設定 Jira 原生估算欄位。

## 8. Jira 寫入前預覽格式

AI 在任何外部寫入前，應顯示：

~~~text
盤點範圍：laravel/ims 的「案件合併功能」
Jira project：KNDU
Issue type：Task（已由 metadata 驗證）
預計建立：4 項；更新既有：0 項
進度：已完成 1；執行中 1；待執行 4；阻塞 0

1. [ims] 建立案件合併 API 與授權
   assignee：後端主要維護者（信心：中）
   priority：High
   original estimate：6h
   labels：ims、案件合併、後端
   status：待執行
   驗收：授權、403、自己合併、重複操作
   verification：php artisan test --filter=CaseMerge

2. ...

請確認：建立 4 張 KNDU Task，並套用上述 assignee、priority、labels、工時與描述。
~~~

使用者確認時應明確回答，例如：

~~~text
確認建立以上 4 張 Jira ticket。
~~~

沒有確認前，只能產生 draft、JSON 或 Markdown 預覽，不可呼叫 createJiraIssue、editJiraIssue、transitionJiraIssue 或 addWorklogToJiraIssue。

## 9. Jira MCP 寫入範例

以下是概念範例；cloudId、issueTypeName、assignee_account_id、priority 名稱、估算欄位必須使用前面查到的實際值。

### 9.1 建立 Task

~~~json
{
  "tool": "mcp__atlassian__createJiraIssue",
  "arguments": {
    "cloudId": "已驗證的 cloudId",
    "projectKey": "KNDU",
    "issueTypeName": "Task",
    "summary": "[ims] 建立案件合併 API 與授權",
    "description": "背景、repository evidence、acceptance criteria、verification、definition of done",
    "assignee_account_id": "由 Jira lookup 查回的 account ID",
    "contentFormat": "markdown",
    "additional_fields": {
      "priority": {"name": "High"},
      "labels": ["ims", "案件合併", "後端"]
    }
  }
}
~~~

### 9.2 建立 Sub-task 或建立父子關係

若 Jira project 支援 Sub-task，使用已建立的 parent key：

~~~json
{
  "tool": "mcp__atlassian__createJiraIssue",
  "arguments": {
    "cloudId": "已驗證的 cloudId",
    "projectKey": "KNDU",
    "issueTypeName": "Sub-task",
    "parent": "KNDU-123",
    "summary": "[ims] 補齊案件合併的權限與重複操作測試",
    "description": "驗收條件與測試命令",
    "contentFormat": "markdown"
  }
}
~~~

如果不能建立 Sub-task，改用一般 Task 加 Relates 或 Blocks link；link type 必須先用 Jira metadata 查詢。

### 9.3 回寫 commit 到 Jira

最可靠的做法是同時使用：

1. commit message 包含 Jira key，讓 Jira/GitLab 原生 DVCS 整合可以辨識。
2. MCP 直接在 Jira issue 加一則帶 commit URL 的 comment，作為可追溯證據。

~~~json
{
  "tool": "mcp__atlassian__addCommentToJiraIssue",
  "arguments": {
    "cloudId": "已驗證的 cloudId",
    "issueIdOrKey": "KNDU-123",
    "contentFormat": "markdown",
    "commentBody": "已完成 commit：abc1234\n\nGitLab：https://gitlab.dbodm.com/laravel/ims/-/commit/abc1234\n\n摘要：新增案件合併 API 與授權測試。\n驗證：php artisan test --filter=CaseMerge"
  }
}
~~~

### 9.4 回寫實際工作時間

只有在 Jira permission、工作起訖時間與工時規則都確認後才使用：

~~~json
{
  "tool": "mcp__atlassian__addWorklogToJiraIssue",
  "arguments": {
    "cloudId": "已驗證的 cloudId",
    "issueIdOrKey": "KNDU-123",
    "timeSpent": "4h",
    "started": "2026-09-07T09:00:00.000+0800",
    "commentBody": "實作 API、補測試並完成 MR review"
  }
}
~~~

### 9.5 Commit 自動對應 Jira 子任務與完成規則

可以自動對應，但建議分成兩個階段：

1. commit message 或 MR description 解析出 Jira key，例如 KNDU-124。
2. 查詢該 key 是否為 KNDU 專案的 Sub-task，確認它屬於目前 parent/功能範圍，再寫入 commit/MR 證據。

安全的預設行為如下：

| 事件 | AI 動作 |
|---|---|
| commit 含有一個有效子任務 key | 在 Jira 子任務加上 commit URL/comment；若尚未開始，可轉為實際的 In Progress 狀態 |
| commit 含有 parent key 但沒有子任務 key | 只回報「無法精確對應」，不自動完成 parent |
| commit 含有多個 Jira key | 可分別建立關聯，但不自動完成任何一張，要求人工確認每張驗收範圍 |
| MR 已合併、CI 測試成功、Jira key 是有效子任務 | 才可依核准政策轉為實際的完成狀態 |
| 只有本地 commit，尚未 push 或沒有測試證據 | 不標示完成，只記錄為已執行證據 |

「自動標示已完成」不應只由 commit 觸發。建議完成條件至少包含：

- commit 已 push 到 GitLab，且可讀取 commit URL；
- Jira key 精確對應一張 Sub-task，不是模糊的 parent key；
- MR 已合併到指定分支；
- CI pipeline 成功，或有明確的驗證命令與成功結果；
- Jira 子任務沒有阻塞或待確認欄位；
- 已用 getTransitionsForJiraIssue 取得實際完成狀態與 transition，不能猜 transition ID；
- 完成前後都讀回 Jira，確認 status/resolution 確實更新。

若公司政策允許「commit 後立即完成」，可以把最後一段改成明確的 opt-in 模式；但至少仍應驗證 Jira key、Issue Type、權限與 transition，並在 Jira comment 保留 commit、MR、pipeline 證據。

自動完成的概念流程：

~~~text
讀取 commit message
  → 擷取 KNDU-124
  → getJiraIssue(KNDU-124)
  → 驗證 project=KNDU、issuetype=Sub-task、key 唯一
  → 讀取 GitLab commit/MR/CI
  → 若證據完整：transitionJiraIssue(KNDU-124, 實際完成 transition)
  → addCommentToJiraIssue（附 commit、MR、CI、測試）
  → getJiraIssue 讀回驗證
~~~

## 10. Branch、commit、MR 規範

### 10.1 Branch

~~~bash
git switch -c feature/KNDU-123-case-merge
# 或 bug fix
git switch -c fix/KNDU-124-invalid-merge
~~~

不要在 Jira key 尚未確認前使用假 key；若尚未建立 ticket，先使用暫存 branch，建立後再重新命名。

### 10.2 Commit

~~~bash
git add app/Services/CaseMergeService.php tests/Feature/CaseMergeTest.php
git commit -m "feat(KNDU-123): add case merge authorization"
~~~

建議格式：

~~~text
<type>(<JIRA-KEY>): <英文或繁中簡短摘要>

可選的背景、驗證命令與 breaking change 說明
~~~

常見 type：feat、fix、refactor、test、docs、chore。

若要自動對應「子任務」，commit 必須使用子任務 key：

~~~bash
git commit -m "feat(KNDU-124): add case merge authorization"
~~~

只寫 feat(KNDU-123)（parent key）不足以判定是哪一個子任務；如果一次 commit 真的包含多個子任務，請在 body 明列每一張 key，並讓 AI 在完成前要求人工確認：

~~~text
feat(KNDU-124): add merge API

Also affects: KNDU-125
~~~

### 10.3 MR 描述

~~~~markdown
## Jira

KNDU-123

## 變更

- 新增案件合併 API
- 加入角色授權與重複操作保護

## 驗證

~~~bash
php artisan test --filter=CaseMerge
~~~

## 風險與回滾

- 只新增關係資料，不刪除原案件
- 發生問題時可關閉 endpoint feature flag
~~~~

## 11. 一次完整操作範例

### 11.1 使用者輸入

~~~text
請分析 laravel/ims：新增「案件合併」功能。
先讀 repo 與既有測試，拆成可獨立驗收的 Jira 子任務，推薦負責人、優先順序與工時。
先只產生預覽，不要寫入 Jira。
~~~

### 11.2 AI 應產出的預覽摘要

~~~text
盤點範圍：routes/api.php → Case controller → CaseFollowupService → models/migrations → Feature tests
任務：4 項；已完成 0；進行中 1；待執行 3；阻塞 0
進度：0/4（尚無驗收完成項）

- [ims] 建立案件合併 API 與授權（High，6h，後端，待執行）
- [ims] 儲存案件合併關係並限制重複（High，4h，後端，待執行）
- [ims] 加入前端合併確認流程（Medium，6h，前端，待執行）
- [ims] 補齊成功與失敗路徑測試（High，4h，QA/後端，執行中）
~~~

### 11.3 使用者確認後

~~~text
確認建立以上 4 張 KNDU Task；請依預覽設定 assignee、priority、labels 與估算，並讀回驗證。
~~~

AI 執行順序：

1. 以完整 summary 搜尋 KNDU，確認沒有相同 ticket。
2. 逐張建立 ticket，記錄回傳 key。
3. 建立 parent/child 或 issue links。
4. 讀回每張 ticket，確認 summary、status、labels、assignee、priority。
5. 報告 Jira key、URL、狀態，以及哪些欄位未能寫入。
6. 程式開發仍由開發者或 AI 依使用者明確指示進行，不因 Jira 建票就宣稱完成。

## 12. 建議建立的 Skill

Skill 是可重複使用的工作規則。建議名稱：gitlab-jira-workflow。

### 12.1 用 initializer 建立目錄

~~~bash
SKILL_CREATOR="/Users/ryanai/.codex/skills/.system/skill-creator"
python3 "$SKILL_CREATOR/scripts/init_skill.py" \
  gitlab-jira-workflow \
  --path "$HOME/.codex/skills" \
  --resources references
~~~

Skill 的基本結構：

~~~text
~/.codex/skills/gitlab-jira-workflow/
├── SKILL.md
├── agents/
│   └── openai.yaml
└── references/
    └── jira-field-mapping.md   # 需要時再建立
~~~

不要在 Skill 內存放 Token；不要把公司專案的私人資料硬編碼成所有專案都適用的規則。

### 12.2 可直接使用的 SKILL.md 內容

以下內容可以貼到 ~/.codex/skills/gitlab-jira-workflow/SKILL.md：

~~~~markdown
---
name: gitlab-jira-workflow
description: Analyze a GitLab repository change request, split unfinished work into verifiable Jira tasks, recommend assignees/priority/estimates, and link confirmed implementation commits to Jira.
---

# GitLab × Jira workflow

Use this skill when the user asks to plan, implement, maintain, or trace a change in a GitLab repository and the related work must be tracked in Jira.

## Safety boundary

- Read the repository and Jira/GitLab metadata before proposing tasks.
- Treat external writes as a separate phase.
- Before creating or updating Jira, show every summary, issue type, assignee, priority, estimate, labels, status, and verification command; require explicit confirmation.
- Never print or commit tokens.
- Never guess a Jira project, issue type, field ID, workflow status, transition ID, assignee account ID, or priority name.

## Analyze

Inspect only files relevant to the requested behavior: routes, controllers/handlers, services, models, migrations, permissions, integrations, UI, and tests. Follow the runtime path instead of assuming the architecture.

Classify each capability as:

- 已完成: implementation, automated tests, and observable verification exist.
- 執行中: meaningful implementation exists but acceptance evidence is incomplete.
- 待執行: implementation or proof is missing.
- 阻塞: an external decision or dependency is unresolved.

Create Jira drafts only for unfinished or unproven work.

## Split tasks

Split by independently deliverable behavior, not arbitrary files or technical layers. Every draft must include:

1. summary: [{repo-name}] 動詞＋可交付結果，功能名稱寫進標題本身，不另開中括號。
2. description: background, repository evidence, contracts/permissions, acceptance criteria, verification, and definition of done.
3. labels: {repo-name} plus {function-name} plus 1-3 labels for what the ticket touches; no spaces, no 自動建立.
4. local status: 待執行, 執行中, 驗收中, or 已完成.
5. exact test command or observable verification when known.

Avoid vague tasks such as 完成前端 or 處理 API.

## Recommend fields

- Assignee: use explicit ownership, CODEOWNERS, relevant path owners, then a verified project fallback. Report evidence and confidence.
- Priority: Highest for security/data loss/outage, High for blocked core flow, Medium for normal feature/maintenance, Low for documentation or low-risk cleanup. Map to names returned by Jira metadata.
- Estimate: include analysis, implementation, tests, review fixes, and acceptance. Write Jira's native estimate only after the field is verified; otherwise put the recommendation in the description.

## Synchronize

1. Verify the Atlassian site/cloudId, project key, issue type, required fields, statuses, transitions, and assignee account IDs.
2. Search the target project for the full summary before creating an issue.
3. Show the complete create/update preview and wait for explicit confirmation.
4. Create or update only confirmed issues.
5. Read every affected issue back and report key, URL, status, labels, assignee, priority, and estimate.
6. Keep implementation progress separate from Jira synchronization progress.

## Commit traceability

- Use feature/<JIRA-KEY>-<short-name> or fix/<JIRA-KEY>-<short-name> branches.
- Use the child issue key in the commit, for example <type>(KNDU-124): <summary>. A parent key alone is not enough.
- Put the Jira key in the MR description.
- After a confirmed commit, add a Jira comment containing the commit hash, GitLab URL, summary, and verification command when the integration does not automatically expose the commit.
- Parse and validate the Jira key against the project and issue type before linking it.
- A linked commit means 已執行 evidence. Do not mark the child completed from a local commit alone.
- Auto-transition a child to the verified completed status only when the commit is pushed, the MR is merged, CI is successful or acceptance evidence is explicit, and the exact Jira transition is verified.
- If multiple child keys appear in one commit, link all candidates but require confirmation before completing any child.
- Read the Jira issue back after linking or transitioning and report the resulting status.
~~~~

### 12.3 驗證 Skill

~~~bash
python3 "$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py" \
  "$HOME/.codex/skills/gitlab-jira-workflow"
~~~

驗證通過只代表 frontmatter、命名與 scaffold 格式正確；仍要用一個唯讀、無寫入的測試需求確認它會先預覽、會查 metadata、會拒絕猜 account ID。

### 12.4 自動生成週報 Skill

建議另外建立 Skill：weekly-jira-report。它只讀取 Jira、GitLab commit/MR 與可用的 worklog，產出指定週期的 Markdown 週報，不修改外部資料。

初始化：

~~~bash
SKILL_CREATOR="/Users/ryanai/.codex/skills/.system/skill-creator"
python3 "$SKILL_CREATOR/scripts/init_skill.py" \
  weekly-jira-report \
  --path "$HOME/.codex/skills"
~~~

可直接使用的 ~/.codex/skills/weekly-jira-report/SKILL.md：

~~~~markdown
---
name: weekly-jira-report
description: Generate a read-only weekly engineering report from Jira subtask status, estimates, worklogs, GitLab commits, and merge requests, including not started, executed work, subtask-based progress, and completed items.
---

# Weekly Jira report

Use this skill when the user asks for a weekly report, engineering progress report, Jira progress summary, or GitLab development summary for a tracked project.

## Safety and scope

- Read Jira and GitLab only; do not create, edit, transition, comment, or log work.
- Confirm the Jira site, project key, report period, timezone, and status mapping before calculating.
- Default timezone is Asia/Taipei. Default period is the previous Monday 00:00 through Sunday 23:59:59, unless the user supplies dates.
- Never count issue creation as implementation progress.
- Never claim an item is completed from a commit alone. Completed requires a verified Jira completion status/resolution or explicit acceptance evidence.
- If a field or event cannot be read, mark it as unknown and explain the limitation.

## Required inputs

1. Jira project key, normally KNDU.
2. Report period in YYYY-MM-DD format.
3. Verified Jira statuses that mean not started, in progress/review, and completed.
4. Parent issues and their child tasks, or a JQL query that identifies the scope.
5. GitLab project path, normally laravel/ims.

If the user does not give a parent issue, use all matching project tasks changed during the period and clearly label the report as project-level.

## Collect evidence

Collect the following read-only evidence:

- Jira child issue key, parent key, summary, status, resolution, assignee, priority, estimate, time spent, updated date, and relevant worklogs.
- Jira status changes or comments during the period when available.
- GitLab commits and merge requests during the period, including commit hash, subject, author, branch, MR, and linked Jira key.
- Test or verification evidence mentioned in Jira, MR descriptions, or commit messages.

Use a stable key such as Jira issue key plus commit hash to deduplicate evidence.

Suggested read-only MCP calls:

~~~text
Atlassian:
  searchJiraIssuesUsingJql
  getJiraIssue
  getTransitionsForJiraIssue      # 只查狀態，不執行 transition

GitLab:
  list_commits
  list_merge_requests
  get_merge_request
  get_merge_request_notes         # 若需要讀取 MR 討論中的驗收證據
~~~

查詢範圍應以明確日期為準，例如 project = KNDU 並限制 updated 或 worklog/activity 在報告週期內；不要把所有歷史資料都當成本週工作。Jira status 名稱必須使用實際 metadata 回傳值。

## Classify work

### 未執行

Include a child task when its verified status is not started and there is no reliable execution evidence in the report period. Show key, summary, assignee, priority, estimate, and blocker if present.

### 已執行

Include a child task when there is a worklog, status change, relevant commit, MR activity, or explicit progress comment during the period. This section may include tasks that are still in progress and tasks that were completed.

Show one row per Jira ticket. Aggregate that ticket's worklogs, status changes, commits, MRs, comments, and test evidence into the same row; do not merge several tickets into one generic activity row.

For each ticket show evidence type and date, current Jira status, this-period activity, linked commit/MR, and ticket progress. Do not imply that 已執行 means 已完成.

### 已完成事項

Include a child task only when its verified status/resolution means completed, or when an explicit acceptance/test result proves completion. Show the completion evidence, linked commit/MR, and verification result.

### 阻塞與待確認

Separate permission failures, missing assignee, missing estimates, unavailable worklogs, and unresolved external decisions from normal unfinished work.

## Calculate progress

Progress is based on child-task completion, never on the number of parent tickets or Jira records created.

When every child has a verified estimate:

    completion percentage =
      sum(estimate of completed child tasks)
      / sum(estimate of all in-scope child tasks) × 100

When estimates are missing or incomparable, use the count fallback:

    completion percentage =
      completed child-task count
      / total in-scope child-task count × 100

Round to one decimal place. Always show numerator, denominator, weighting mode, and the list of child tasks included. A parent with four children where two are complete is 50%, even if the parent Jira issue was created today. Do not count blocked or unknown tasks as complete.

For the per-ticket view:

- completed status/resolution: ticket progress 100%;
- verified not-started status with no period evidence: ticket progress 0%;
- in-progress/review status: show 執行中 and evidence; use a numeric partial percentage only when the ticket has verified checklist/subtask evidence;
- unknown or blocked: show 待確認 or 阻塞, and exclude it from the completed numerator.

Also report:

- completed children / total children;
- executed children / total children;
- not-started children / total children;
- total estimate and completed estimate when estimates are available;
- this-period activity separately from all-time completion.

## Output format

Produce Traditional Chinese Markdown with this structure:

1. 週報標題、週期、時區、資料來源、產生時間。
2. 摘要：子任務完成數、完成度公式、執行數、未執行數、阻塞數。
3. 工作進度：formula, numerator/denominator, weighted or count mode.
4. 未執行：table.
5. 已執行：table with evidence and current status.
6. 已完成事項：table with acceptance evidence.
7. 阻塞與風險。
8. 下週建議。
9. 資料限制與待人工確認。

Use this table shape:

| Jira ticket | 父任務 | 子任務 | 負責人 | 目前狀態 | Ticket 進度 | 預估 | 本週執行證據 | 完成證據 |
|---|---|---|---|---|---:|---:|---|---|

Do not invent missing values. Use 未設定、無資料、待確認 as appropriate.

## Example request

請產生 KNDU 專案 2026-09-01 至 2026-09-07 的週報，時區 Asia/Taipei。以 Jira 子任務完成度計算工作進度，列出未執行、已執行、已完成事項與阻塞；只讀取，不修改 Jira 或 GitLab。
~~~~

驗證：

~~~bash
python3 "$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py" \
  "$HOME/.codex/skills/weekly-jira-report"
~~~

### 12.5 週報觸發方式

手動執行時，直接輸入：

~~~text
$weekly-jira-report
請產生上週 KNDU / laravel/ims 週報，時區 Asia/Taipei。
列出未執行、已執行、依子任務完成度計算的工作進度、已完成事項、阻塞與資料限制。
只讀取 Jira 與 GitLab，不要修改任何資料。
~~~

若要每週自動產出，可由排程工具、CI pipeline 或公司核准的自動化平台，在每週一上午觸發同一段 prompt，並將報告保存為：

~~~text
reports/weekly/KNDU-YYYY-MM-DD.md
~~~

排程帳號只需要 Jira/GitLab 讀取權限。若排程失敗，週報必須標示資料取得失敗，不可產出看似完整但沒有來源證據的報告。

### 12.6 週報進度計算實例

假設 KNDU-123 底下有四個子任務：

| 子任務 | 預估 | 狀態 |
|---|---:|---|
| KNDU-124 | 4h | Done |
| KNDU-125 | 6h | Done |
| KNDU-126 | 8h | In Progress |
| KNDU-127 | 2h | To Do |

因為所有子任務都有可比較的預估工時，使用加權完成度：

~~~text
完成度 = (4h + 6h) / (4h + 6h + 8h + 2h) × 100
       = 10 / 20 × 100
       = 50.0%
~~~

週報應呈現：

~~~text
工作進度：50.0%
計算方式：預估工時加權
已完成：2/4 個子任務，10h/20h
已執行：3/4 個子任務
未執行：1/4 個子任務
已完成事項：KNDU-124、KNDU-125
~~~

若 KNDU-127 沒有估算，則改用數量完成度 2/4 = 50.0%，並在「資料限制」註明未使用工時加權。

### 12.7 週報依各 ticket 顯示已執行進度

已執行區塊不只顯示「本週完成 3 項」，而是每一張 ticket 一列，將同一 ticket 的 commit、MR、worklog、狀態變更與測試證據合併呈現：

| Jira ticket | 父任務 | 目前狀態 | Ticket 進度 | 本週執行證據 | 完成證據 |
|---|---|---|---:|---|---|
| KNDU-124 | KNDU-123 | Done | 100% | 2026-09-03 commit abc1234、MR !51、CI passed | 已合併；CaseMergeTest 通過 |
| KNDU-125 | KNDU-123 | In Progress | 執行中 | 2026-09-05 worklog 3h、commit def5678 | 尚未完成 |
| KNDU-126 | KNDU-123 | To Do | 0% | 無本週證據 | 未開始 |

因此：

- 已執行 ticket 數：KNDU-124、KNDU-125，共 2/3。
- 已完成 ticket 數：KNDU-124，共 1/3。
- 工作進度仍依所有子任務的完成度公式計算，不以「已執行數」取代完成度。
- 同一 ticket 有多個 commit 時，合併在同一列並列出 hash；不要重複計算成多張 ticket。

## 13. 可選的 Jira plan JSON

若使用 REST fallback 或希望先保存 draft，可以產生 jira-plan.json：

~~~json
[
  {
    "summary": "[ims] 建立案件合併 API 與授權",
    "description": "背景：避免重複案件。\n\nRepository evidence：routes/api.php、app/Services/CaseFollowupService.php。\n\nAcceptance criteria：授權角色可合併；非授權角色得到 403；同一案件不可自我合併；重複操作不產生第二筆關係。\n\nVerification：php artisan test --filter=CaseMerge。\n\nAI 建議：assignee=待以 Jira account lookup 驗證；priority=High；estimate=6h。",
    "labels": ["案件管理", "後端"]
  }
]
~~~

沒有 Atlassian MCP 時，才使用 jira-breakdown skill 所提供的 REST fallback；該 helper 預設 dry-run，必須在預覽與明確確認後才加 --apply。Token 應使用環境變數：

~~~bash
export JIRA_BASE_URL='https://dboem.atlassian.net'
export JIRA_EMAIL='你的 Atlassian 登入信箱'
export JIRA_API_TOKEN='只存在安全環境的 token'
export JIRA_PROJECT_KEY='KNDU'
export JIRA_ISSUE_TYPE='Task'
~~~

## 14. 常見錯誤與排除

### 401 Unauthorized（GitLab）

1. 確認 Token 尚未過期、沒有貼錯空白或換行。
2. 確認 GitLab host 是 gitlab.dbodm.com，API URL 是 https://gitlab.dbodm.com/api/v4。
3. 確認使用者對 laravel/ims 有權限。
4. 重新啟動 MCP server/Codex，再執行 whoami。

### Jira 找不到 KNDU

1. 比對登入的 site URL 與瀏覽器實際開啟的 site。
2. 重新執行 Atlassian OAuth 登入。
3. 確認使用者能在瀏覽器開啟 KNDU board。
4. 重新查詢 cloudId；不要手動複製別人的 cloudId。

### Field cannot be set 或 Issue Type is invalid

- 重新查 getJiraProjectIssueTypesMetadata。
- 重新查 getJiraIssueTypeMetaWithFields。
- 把不確定的 priority/estimate/custom field 從 create payload 拿掉，先建立最小合法 ticket，或請 Jira 管理員確認欄位。

### 建立重複 ticket

- 先用完整 summary 搜尋，不要依建立時間或流水號去重複。
- 用 {repo-name}、{function-name} 標籤或 [{repo-name}] 標題前綴輔助搜尋，但不能只依 labels 判斷。
- 已存在相同摘要時，優先更新既有 ticket 或要求人工決定。

### Commit 沒有出現在 Jira

- 確認 commit message/MR description 包含完整 Jira key，例如 KNDU-123。
- 確認 GitLab/Jira DVCS integration 已把正確 GitLab host 連到正確 Jira site。
- 若原生整合未啟用，使用 Jira MCP comment 回寫 commit hash、URL 與驗證結果。

## 15. 上線前驗收清單

- [ ] Atlassian MCP 登入的是包含 KNDU 的正確 site。
- [ ] GitLab MCP whoami 不回 401。
- [ ] laravel/ims 可讀取 project metadata、tree、commit。
- [ ] 能查到 Jira issue type、required fields、priority、status、transition。
- [ ] 能用 Jira lookup 查到實際 assignee account ID。
- [ ] owner mapping 有 fallback，且低信心時會要求人工確認。
- [ ] priority 規則與 Jira 實際名稱完成 mapping。
- [ ] estimate 欄位已驗證，或明確只寫建議工時。
- [ ] AI 寫入前會列出完整 preview。
- [ ] 已驗證「未確認不寫入」。
- [ ] branch/commit/MR 規範含 Jira key。
- [ ] commit 回寫 Jira 的原生整合或 MCP fallback 至少一條可用。
- [ ] 建立後會讀回每張 Jira issue 驗證。
- [ ] Token 沒有出現在 repo、log、Jira description 或 commit。

## 16. 目前待人工補齊的問題

以下資訊會直接影響正式啟用，請 Jira/GitLab 管理員提供：

1. KNDU 實際所在的 Atlassian site 是否就是 dboem.atlassian.net？
2. AI 使用的 Jira account 應是哪一個帳號？是否允許建立、更新與記 worklog？
3. 可自動指派的開發/測試人員清單，以及每人的 Jira account ID 或可查詢的 email/name。
4. Jira 使用的 Issue Type、priority 名稱、狀態流程與 original estimate 欄位。
5. GitLab 是否已與 Jira 啟用 DVCS/integration？若沒有，是否允許 AI 以 Jira comment 回寫 commit？
6. GitLab MCP Token 是只讀，還是允許建立 branch、MR note、commit status？
7. 工時是使用實際時間、預估時間，還是只要 Jira story points？

在這些問題確認前，可以安全執行 repo 分析與 Jira draft 預覽，但不建議啟用全自動外部寫入。

## 參考

- Jira：https://dboem.atlassian.net/jira/core/projects/KNDU/board
- GitLab：https://gitlab.dbodm.com/laravel/ims
- OpenAI Developers：https://developers.openai.com/
- OpenAI Skills API reference：https://developers.openai.com/api/reference/python/resources/skills/methods/create
- OpenAI MCP tool reference：https://developers.openai.com/api/reference/cli/resources/responses/methods/create
