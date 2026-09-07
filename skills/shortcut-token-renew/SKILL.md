---
name: shortcut-token-renew
description: "檢查 Shortcut API token（SHORTCUT_API_TOKEN）是否過期，過期時協助重新申請新 token、刪除舊 token，並同步更新所有本機設定檔。當 Shortcut 相關工具（mcp__shortcut__*、shortcut-api、shortcut-ticket 等）回傳 401，或使用者要求檢查/更新 Shortcut token 時使用。也可在 commit & push 流程中作為前置檢查步驟。"
license: MIT
metadata:
  author: Ryan Yu
  version: 1.0.0
---

# Shortcut Token 續期

Shortcut 的 API token 效期很短，過期後所有 Shortcut 相關操作（`mcp__shortcut__*`、`shortcut-api`、`shortcut-ticket` skill）都會回 401。這個 skill 把「發現過期 → 重新申請 → 刪除舊 token → 同步設定檔」的流程固定下來。

## 核心限制：token 申請/刪除只能在網頁上做

Shortcut 沒有提供「用 API 自我核發/撤銷 token」的端點，只能在 https://app.shortcut.com/{workspace}/settings/account/api-tokens 這個頁面手動操作，且登入通常需要人在場完成（密碼 + 2FA/SSO）。所以這個流程天生分兩段：

- **可以純腳本、免人工的部分**：檢查 token 是否有效、把新 token 值寫進所有設定檔。這兩段封裝成 `scripts/` 底下的純 bash + curl/perl script，不依賴 Claude Code 專屬工具，Codex 或任何能執行 shell 的 agent 都能直接呼叫。
- **一定要有 agent + 人共同完成的部分**：登入 Shortcut 網站、按「Create Token」、按「Delete Token」。這段需要有瀏覽器操作能力的 agent（例如 Claude Code 的 chrome-devtools MCP）配合使用者手動登入；若當下的 agent 沒有瀏覽器工具，就把步驟印出來請使用者自己按。

## 完整流程

### 1. 檢查目前 token 是否還有效

```bash
bash ~/.claude/skills/shortcut-token-renew/scripts/check_shortcut_token.sh
```

- exit 0：有效，流程到此結束，不用往下做。
- exit 2：`SHORTCUT_API_TOKEN` 根本沒設定，告知使用者並停止（這不是「過期」，是從沒設過）。
- exit 1：已過期，進入下面的重新申請流程。

### 2. 重新申請新 token（需要瀏覽器）

若目前 agent 有瀏覽器工具（如 chrome-devtools MCP）：

1. 導覽到 `https://app.shortcut.com/{workspace}/settings/account/api-tokens`（workspace slug 通常可以從舊的 `SHORTCUT_API_TOKEN` 值或使用者之前提供的網址得知；不確定就問使用者）。
2. 若被導去登入頁，停下來告知使用者「請在這個視窗手動登入（含 2FA/SSO）」，等使用者回覆完成後再繼續。**不要**去操作帳密欄位或代替使用者按登入 — 帳密輸入一律留給使用者自己動手。
3. 登入後，先看頁面上現有的 token 列表，記下要汰換的那一筆的 **Name** 和 **Access**（例如「Read + Write + Admin」對應「Full access」），之後新 token 要用一樣的名字、一樣的權限，避免改變既有整合的權限範圍。
4. 點 **Create Token**：填入同樣的 Token Name、選同樣的權限（一般對應到 `Full access` radio），送出。
5. 頁面只會顯示新 token 值「這一次」，用瀏覽器工具讀出這個值（例如按鈕文字/DOM 內容），**絕對不要把這個值輸出在對話文字裡**，直接在下一步用管線傳給 script。

若目前 agent 沒有瀏覽器工具（例如純 CLI 環境的 Codex）：印出上述 1-5 步驟的文字說明，請使用者自己在瀏覽器完成，並把新 token 貼給你（一樣不要把貼過來的值再原樣印出當作確認訊息，直接進下一步）。

### 3. 把新 token 寫進所有設定檔

新 token 值一律用 stdin 傳入，不要當成命令列參數（會留在 shell history / `ps` 輸出裡）：

```bash
printf '%s' "$NEW_TOKEN" | bash ~/.claude/skills/shortcut-token-renew/scripts/update_shortcut_token.sh
```

這支 script 會更新以下位置（存在且有寫到 `SHORTCUT_API_TOKEN` 才會動）：
- `~/.zshrc`、`~/.zprofile`、`~/.bash_profile`、`~/.bashrc`
- `~/.claude/settings.local.json`
- `~/.codex/config.toml`（若使用 Codex CLI 且用這個檔案管理環境變數）

若使用者的環境變數是設在其他地方（例如專案的 `.env`、CI 的 secret 設定），這支 script 不會碰到，要另外提醒使用者手動更新。

### 4. 刪除舊 token

回到瀏覽器，找到步驟 2.3 記下的舊 token 那一列，點 **Delete token**，跳出確認對話框後點 **Delete Token** 確認。確認頁面上顯示「deleted」字樣、且列表只剩新 token。

### 5. 驗證

```bash
bash ~/.claude/skills/shortcut-token-renew/scripts/check_shortcut_token.sh
```

**注意**：如果目前是在一個已經啟動的 MCP 連線 / agent session 裡做這件事，該行程的環境變數是啟動當下就固定的，改設定檔不會讓「這個已經在跑的行程」立刻生效，需要重啟 MCP 連線或開新 session 才會讀到新值——用上面這行驗證的是「設定檔裡的值本身有沒有效」，不代表當前 session 的 Shortcut 工具馬上就能用。

## 整合進 commit & push 流程

若這次的分支或改動會需要透過 Shortcut MCP 同步 ticket 狀態（例如分支名稱帶 `sc-XXXXX`），可以在 [auto-commit-push](../auto-commit-push/SKILL.md) 流程的最前面先跑一次步驟 1 的健康檢查；只有真的過期才進入步驟 2-5，一般情況下這一步應該是瞬間通過，不會拖慢正常的 commit/push。不需要 Shortcut 的 repo/commit 則不用跑這個檢查。

## 安全注意事項

- 新 token 的值絕對不能出現在對話的可見文字輸出裡，只能經由工具參數（瀏覽器工具讀值、script 的 stdin）傳遞。
- 不要用 `-p'token值'` 這種會把秘密留在 shell history 或 `ps` 輸出裡的寫法；一律走 stdin 或環境變數。
- 帳密輸入永遠是使用者自己動手，agent 不代為輸入或送出登入表單。
- 更新設定檔前後可以用「值的長度」而不是印出實際內容來確認有沒有換成功（新舊 token 格式通常長度一致）。
