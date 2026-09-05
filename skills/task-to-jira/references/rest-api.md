# Jira REST API fallback

Only use this fallback when no Atlassian MCP connector is available.

## Configuration

The helper reads configuration from environment variables without printing secret values:

- `JIRA_BASE_URL`: Jira Cloud site, for example `https://your-team.atlassian.net`
- `JIRA_EMAIL`: Atlassian account email
- `JIRA_API_TOKEN`: Atlassian API token
- `JIRA_PROJECT_KEY`: target Jira project key; `--project` overrides it
- `JIRA_ISSUE_TYPE`: issue type name; defaults to `Task`, and `--issue-type` overrides it

Never commit tokens, place them in command arguments, or include them in Jira descriptions.

## Plan format

The plan is a JSON array. Each item requires `summary` and `description`; `labels` is optional:

```json
[
  {
    "summary": "[帳號管理] 完成停用帳號流程",
    "description": "背景、證據、驗收條件、測試方式與完成定義",
    "labels": ["帳號管理", "後端"]
  }
]
```

The helper always adds `自動建立` and removes duplicate labels.

## Safety and endpoints

- Search: `POST /rest/api/3/search/jql`
- Create: `POST /rest/api/3/issue`
- Read back: `GET /rest/api/3/issue/{key}?fields=summary,status,labels`

The helper defaults to dry-run. Use `--apply` only after the user confirms the exact Jira write. It does not delete issues or transition workflow status.

```bash
python3 /path/to/task-to-jira/scripts/sync_jira.py \
  --plan /path/to/generated-plan.json \
  --project PROJ
```

After preview and confirmation, repeat with `--apply` and read the affected issues back from Jira.
