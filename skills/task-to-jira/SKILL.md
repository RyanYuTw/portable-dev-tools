---
name: task-to-jira
description: "Analyze a requested software feature against repository evidence, split unfinished work into testable tasks, preview progress, and synchronize confirmed tasks to Jira. Use when the user asks to break implementation work into Jira issues or keep implementation status aligned with Jira."
---

# Task to Jira

Turn a feature request and repository evidence into independently executable, verifiable Jira work items. This skill tracks implementation work; it does not modify product code unless the user separately asks for implementation.

## Analyze the feature

Treat the current repository root as the project root. Establish the feature boundary from the user's page, requirement, issue, design, or named files. Inspect only evidence relevant to that boundary, such as routes, UI code, controllers or handlers, services, persistence, migrations, permissions, integrations, and tests.

Do not assume a framework, architecture, CRUD shape, or file naming convention. Search for the actual feature name and follow its runtime path. When a live page is available, compare visible behavior with code and API behavior.

Classify each capability as:

- `已完成`: implementation, automated tests, and observable verification all exist.
- `執行中`: meaningful implementation exists, but acceptance evidence is incomplete.
- `待執行`: missing or still placeholder/static behavior.
- `阻塞`: completion depends on an unresolved external decision or unavailable dependency.

Create Jira drafts only for unfinished or unproven work. Report completed capabilities in the progress summary without duplicating them as new issues.

## Repository and feature naming

Every draft is named after the repository it lands in and the feature it implements:

- `{repo-name}`: `basename -s .git "$(git remote get-url origin)"`, falling back to
  `basename "$(git rev-parse --show-toplevel)"` when there is no remote. Keep the
  original spelling (`ims`, `aims-front`); do not translate or re-case it.
- `{function-name}`: the feature boundary of this batch, in Traditional Chinese and
  **without spaces**, because Jira labels reject them (`案件合併`, not `案件 合併`).

## Split work

Split by independently deliverable behavior, not by arbitrary file or technical layer. A task may span UI, API, persistence, permissions, and tests when those pieces are required for one verifiable outcome. Separate tasks when they can be implemented and accepted independently.

Every draft must contain:

1. `summary`: `[{repo-name}] 動詞＋可交付結果`, with the feature folded into the title
   itself rather than kept in a separate bracket — for example
   `[ims] 案件合併加上授權檢查並回傳 403`. Traditional Chinese unless the user requests
   another language. The bracket holds the repository name only.
2. `description`: background, repository evidence, relevant contracts or permissions, acceptance criteria, verification, and definition of done.
3. `labels`: `{repo-name}`, `{function-name}`, plus 1-3 more labels for what this
   ticket actually touches (`前端`, `後端`, `API`, `資料庫`, `權限`, `測試`, `文件`,
   `設定`). Traditional Chinese except the repo name, no spaces in any label, no
   English synonyms, and nothing invented that the ticket does not touch. Do not add
   an `自動建立` label.
4. `status`: recommended local status using `待執行`, `執行中`, `驗收中`, or `已完成`.
5. `verification`: exact test command or observable check when known.
6. `assignee`: default to `ryan.yu@dboem.com` unless the user names a different assignee for that task.

Avoid vague tasks such as “完成前端” or “處理 API.” Acceptance criteria must describe observable behavior and important failure or permission paths.

## Preview and progress

Before writing to Jira, show the complete task list and a progress summary:

```text
盤點範圍：<feature>
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

Do not count “Jira issue created” as implementation completion.

## Synchronize Jira

Prefer an available Atlassian MCP connector. Use [references/rest-api.md](references/rest-api.md) and `scripts/sync_jira.py` only when MCP is unavailable.

Default target unless the user specifies otherwise:

- Site: `https://dboem.atlassian.net`
- Project key: `KNDU`
- Board: `https://dboem.atlassian.net/jira/core/projects/KNDU/board?groupBy=none`
- Assignee: `ryan.yu@dboem.com`

1. Confirm the Jira site, project key, issue type, target labels, and workflow status names from the environment or Jira metadata, falling back to the defaults above. Do not guess any identifier the defaults don't cover.
2. Search the target project and compare the full summary before creating anything. Narrow the search with the `{repo-name}` and `{function-name}` labels or the `[{repo-name}]` summary prefix, but do not rely on labels alone, nor on sequence numbers or creation time, for deduplication.
3. Present the exact create/update preview. Immediately before the external write, obtain user confirmation listing issue count, summaries, project, issue type, intended status, and assignee.
4. Create or update only the confirmed issues, setting `assignee` on each (resolve the email to an account ID first; see [references/rest-api.md](references/rest-api.md)). Match workflow transitions by exact returned name; never guess transition IDs.
5. Read every affected issue back from Jira and report its key, URL, status, labels, and assignee.
6. Report local implementation progress separately from Jira synchronization progress.

Stop and ask for direction if the Jira project, issue type, required field, or intended status cannot be verified.

## Commit-to-subtask traceability

Use the child Jira key in the commit message, for example:

~~~text
feat(KNDU-124): add case merge authorization
~~~

A parent key alone is not enough to identify a child task. When a commit or MR contains a Jira key:

1. Parse the key and read the Jira issue.
2. Verify that it belongs to the target project and is a Sub-task or other approved child issue type.
3. Add the commit/MR URL and verification evidence to that child issue.
4. Treat the linked commit as 已執行 evidence, not proof of completion.
5. Auto-transition the child only when the commit is pushed, the MR is merged, CI is successful or acceptance evidence is explicit, and the exact completed transition was read from Jira metadata.
6. Read the child issue back and report the resulting status.

If multiple child keys occur in one commit, link each candidate but require confirmation before completing any of them. A local commit without a pushed GitLab URL or test evidence must not automatically mark a Jira child as completed.
