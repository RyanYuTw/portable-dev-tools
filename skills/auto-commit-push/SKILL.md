---
name: auto-commit-push
description: 自動分析 git 變更、產生 Conventional Commits 格式的 commit message、安全挑選要 staging 的檔案（絕不誤加 .env / 憑證等敏感檔案，也不用 git add -A / git add .）、建立 commit 並 push 到目前分支。當使用者說「幫我 commit」「自動 commit and push」「commit 這些變更然後推上去」「commit and push」或任何要求自動化 git commit/push 流程的請求時使用，即使沒有明講 conventional commits 或 push 也應觸發。內建安全防護：偵測敏感檔案、偵測 main/master 分支、偵測分支落後 remote 或需要 force push 的情況，遇到這些狀況會停下詢問使用者，不會盲目自動執行危險操作。
---

# Auto Commit & Push

目標：把「產生高品質 commit + 安全 push」整套判斷流程固定下來，讓使用者不用每次都重複交代規則，同時保留人在關鍵風險點上的決定權（main 分支、分支分歧、敏感檔案）。

## 完整流程

### 0.（可選）Shortcut token 健康檢查

只有當這次的分支或後續動作會用到 Shortcut MCP（例如分支名稱帶 `sc-XXXXX`、或使用者有要求順便同步 ticket 狀態）才需要跑這一步；單純 commit/push 跟 Shortcut 無關的話跳過。

```bash
bash ~/.claude/skills/shortcut-token-renew/scripts/check_shortcut_token.sh
```

- exit 0：略過，直接進第 1 步。
- exit 1（token 過期）：依照 [shortcut-token-renew](../shortcut-token-renew/SKILL.md) 的流程重新申請、刪除舊 token、更新設定檔，完成後再回來繼續。
- exit 2（沒設定過）：跟這次任務無關的話直接忽略，繼續第 1 步。

### 1. 收集現況（可平行執行）

```bash
git status --short
git diff              # unstaged
git diff --staged     # 已 staged 但還沒 commit 的
git log --oneline -10 # 參考近期 commit 風格
```

這個 repo 近期 commit 都是英文 + Conventional Commits 前綴。**若目前分支名稱帶 Shortcut ticket 編號（如 `ryan.yu/sc-49/misc` 裡的 `sc-49`），commit subject 前面要加 `[sc-49]` 前綴**——這是 GitLab↔Shortcut 整合實際辨識、拿來自動把 commit 掛進 story「Commits」清單的格式（已用 story sc-49 裡唯一一筆有自動掛進去的 commit `[sc-49] feat: 補齊前台頁面缺口的 schema 與 API` 驗證過；沒帶這個前綴的 commit，即使分支對了也不會出現在 Commits 清單裡）。沒有對應 ticket 的分支才維持純 Conventional Commits、不加前綴。

### 2. 挑選要 add 的檔案

- 只 add 與目前任務相關、已修改/新增的檔案。
- 絕不使用 `git add -A` 或 `git add .` — 一次沖進所有東西容易誤加密鑰或不相關的檔案。
- 明確列出檔名：`git add <file1> <file2> ...`
- 若不確定某個檔案該不該進版控（例如看起來像本機設定、大型 binary、非預期出現的新檔案），先詢問使用者再決定，不要自己猜。

### 3. 敏感檔案掃描

`git add` 之後、commit 之前，執行：

```bash
bash ~/.claude/skills/auto-commit-push/scripts/check_secrets.sh
```

這個 script 會檢查目前 staged 的檔案清單，比對常見敏感檔案樣式（`.env`、`*credential*`、`*secret*`、`id_rsa`、`*.pem`、`*.key`、service account json 等），`.env.example` 這類範本檔案不會被誤判。

- 若命中（exit code 非 0），印出命中的檔名，執行 `git restore --staged <file>` 移除該檔案，並告知使用者發現了什麼、為何沒有繼續 commit。
- 不能因為腳本擋下來就加 `--no-verify` 或忽略警告硬 commit。

### 4. 產生 Conventional Commits 訊息

根據 staged diff 判斷 type（`feat` / `fix` / `refactor` / `style` / `docs` / `test` / `chore` / `perf` 等），寫一行精簡的祈使句 subject（英文）。

如果 diff 裡混雜多種不相關的改動，主動建議拆成多個 commit、列出建議的分組方式讓使用者確認，不要硬塞成一則訊息，也不要自己擅自拆分後直接執行。

commit message 結尾固定加上一行：

```
Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
```

用 heredoc 傳遞訊息以確保格式正確：

```bash
git commit -m "$(cat <<'EOF'
[sc-49] <type>: <subject>

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

（`[sc-49]` 只在分支帶對應 ticket 編號時才加；無關 ticket 的分支就沒有這段前綴，直接 `<type>: <subject>`。）

不要加 `--no-verify`、`--no-gpg-sign`，也不要用 `-c commit.gpgsign=false` 之類的方式繞過簽名。

若 pre-commit hook 失敗：commit 並沒有真的發生，所以修好問題、重新 `git add` 後要建立一個「新的」commit，不要對（不存在的）上一個 commit 做 `--amend`。

### 5. Push 前的安全檢查

commit 完成後執行：

```bash
bash ~/.claude/skills/auto-commit-push/scripts/check_push_safety.sh
```

這個 script 會：

- 檢查目前分支：若是 `main` 或 `master`，回傳非 0 — 這時停下來告知使用者，不自動 push，除非使用者明確要求才手動處理。
- `git fetch` 更新 remote-tracking 分支（純讀取，不影響工作目錄），比較本地與 upstream 的 ahead/behind。若偵測到落後 remote（代表需要 rebase 或 merge 才能 push，或只能靠 force push 同步），回傳非 0 — 這時停下來詢問使用者要怎麼處理，不要自動 rebase/merge/force push。

只有 script 回傳 0 時才繼續：

```bash
git push            # 已有 upstream
git push -u origin <branch>   # 尚未設定 upstream 時
```

一般情況（非 main/master、且與 remote 沒有分歧）不需要每次都先問使用者才 push — 使用者要的就是「自動」；只有上面兩種風險情況才需要停下來詢問。

### 6. 驗證

```bash
git status
```

確認 working tree 乾淨、push 成功。

### 7.（若分支帶 Shortcut ticket 編號）確認自動掛進 Commits / Merge Requests

Shortcut 的 GitLab 整合是被動掃描，不是靠留言或呼叫 API 手動寫入：

- **Merge Requests**：只要 MR 的來源分支名稱含 `sc-XXXXX`，不管 MR 標題寫什麼，整合都會自動把它掛進 story 的「Merge Requests」清單——這件事分支一推上去、有人開 MR 就會自動發生，不需要額外動作。
- **Commits**：整合只認 **commit message 裡的 `[sc-49]` 這類前綴**（見步驟 4），跟分支名稱無關。所以只要步驟 4 有照規矩加前綴，push 上去後整合會自己把這筆 commit 掛進 story 的「Commits」清單，一樣不需要額外動作。
- **不要**用 `mcp__shortcut__stories-create-comment` 手動貼 commit 清單當留言充數——那只是留言，不會出現在 story 真正的 Commits/Merge Requests 區塊，等於沒有整合到。
- 若事後想確認有沒有真的掛上，可以用 `mcp__shortcut__stories-get-by-id`（帶 `full: true`）看 story 的 `commits` / `pull_requests` 欄位有沒有出現這次的 hash / MR。已經 push 出去但 commit message 忘記加前綴的舊 commit，整合不會回溯補掛，只能認了或之後補一個有正確前綴的 commit。

### 8. 回報

回報時保持精簡：commit hash（短）、commit message 第一行、push 結果，不需要贅述做了哪些步驟。
