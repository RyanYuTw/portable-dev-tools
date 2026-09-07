# Jira REST API fallback

Only use this fallback when no Atlassian MCP connector is available.

## Configuration

The helper reads configuration from environment variables without printing secret values:

- `JIRA_BASE_URL`: Jira Cloud site; defaults to `https://dboem.atlassian.net` if unset
- `JIRA_EMAIL`: Atlassian account email (used for API auth, not the assignee)
- `JIRA_API_TOKEN`: Atlassian API token
- `JIRA_PROJECT_KEY`: target Jira project key; `--project` overrides it; defaults to `KNDU` if unset
- `JIRA_ISSUE_TYPE`: issue type name; defaults to `Task`, and `--issue-type` overrides it
- `JIRA_ASSIGNEE_EMAIL`: assignee's Atlassian account email; `--assignee` overrides it; defaults to `ryan.yu@dboem.com` if unset

Never commit tokens, place them in command arguments, or include them in Jira descriptions.

## Plan format

The plan is a JSON array. Each item requires `summary` and `description`; `labels` and `assignee` are optional (an item-level `assignee` overrides `--assignee`/`JIRA_ASSIGNEE_EMAIL`):

```json
[
  {
    "summary": "[帳號管理] 完成停用帳號流程",
    "description": "背景、證據、驗收條件、測試方式與完成定義",
    "labels": ["帳號管理", "後端"],
    "assignee": "ryan.yu@dboem.com"
  }
]
```

The helper always adds `自動建立` and removes duplicate labels.

## Safety and endpoints

- Search: `POST /rest/api/3/search/jql`
- Resolve assignee: `GET /rest/api/3/user/search?query={email}` (take the single matching `accountId`; abort if zero or more than one match)
- Create: `POST /rest/api/3/issue` with `fields.assignee.accountId`
- Read back: `GET /rest/api/3/issue/{key}?fields=summary,status,labels,assignee`

The helper defaults to dry-run. Use `--apply` only after the user confirms the exact Jira write, including the assignee. It does not delete issues or transition workflow status.

```bash
python3 /path/to/task-to-jira/scripts/sync_jira.py \
  --plan /path/to/generated-plan.json \
  --project KNDU
```

`--project`, `--assignee`, `JIRA_BASE_URL`, and `JIRA_PROJECT_KEY` all default to the dboem KNDU board and `ryan.yu@dboem.com`; pass explicit values only to target something else.

After preview and confirmation, repeat with `--apply` and read the affected issues back from Jira.
