# Jira REST API adapter

## 認證與設定

腳本只從環境變數讀取設定，不讀取或輸出 `.env` 內容：

- `JIRA_BASE_URL`：例如 `https://your-team.atlassian.net`
- `JIRA_EMAIL`：Atlassian 帳號 email
- `JIRA_API_TOKEN`：Atlassian API token
- `JIRA_PROJECT_KEY`：目標 Jira project key；也可用 `--project` 覆蓋

對個人腳本使用 Jira Cloud REST API v3 的 Basic auth（email + API token）；token 不可提交至 repository、命令列 history 或 Jira description。

## 端點

- 查重：`POST /rest/api/3/search/jql`，取 `summary`, `labels`, `status`。
- 建立：`POST /rest/api/3/issue`，欄位包含 `project.key`, `issuetype.name`, `summary`, `description`（ADF）、`labels`。
- 讀回：`GET /rest/api/3/issue/{key}?fields=summary,status,labels`。
- 狀態：先 `GET /rest/api/3/issue/{key}/transitions`，再對精確匹配的 transition id 呼叫 `POST`；找不到目標狀態就回報阻塞，不猜 id。

## 安全邊界

`sync_jira.py` 預設 dry-run；只有 `--apply` 才建立 issue。建立前由上層流程完成去重與預覽，並在外部寫入前取得使用者確認。腳本不提供刪除 issue 功能。

## 執行

```bash
python3 /path/to/investment-contact-jira/scripts/sync_jira.py \
  --plan /path/to/generated-plan.json
```

確認預覽、設定四個環境變數後，才改用 `--apply`。腳本會在目標專案內以完整 summary 去重。
