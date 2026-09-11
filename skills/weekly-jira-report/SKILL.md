---
name: weekly-jira-report
description: Generate a read-only weekly engineering report from Jira subtask status, estimates, worklogs, GitLab commits, and merge requests, including per-ticket execution progress and subtask-based completion.
---

# Weekly Jira report

Use this skill for a weekly report, engineering progress report, Jira progress summary, or GitLab development summary for a tracked project.

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

Collect read-only evidence from Jira and GitLab:

- Jira child issue key, parent key, summary, status, resolution, assignee, priority, estimate, time spent, updated date, and relevant worklogs.
- Jira status changes or comments during the period when available.
- GitLab commits and merge requests during the period, including commit hash, subject, author, branch, MR, and linked Jira key.
- Test or verification evidence mentioned in Jira, MR descriptions, or commit messages.

Suggested tools:

- Atlassian: searchJiraIssuesUsingJql, getJiraIssue, getTransitionsForJiraIssue.
- GitLab: list_commits, list_merge_requests, get_merge_request, get_merge_request_notes.

Use a stable key such as Jira issue key plus commit hash to deduplicate evidence. Query by explicit dates; do not treat all historical activity as this week's work.

## Classify work

### 未執行

Include a child task when its verified status is not started and there is no reliable execution evidence in the report period. Show key, summary, assignee, priority, estimate, and blocker if present.

### 已執行

Show one row per Jira ticket. Include a child task when there is a worklog, status change, relevant commit, MR activity, or explicit progress comment during the period. Aggregate that ticket's evidence into the same row; do not merge several tickets into one generic activity row.

Show evidence type and date, current Jira status, this-period activity, linked commit/MR, and ticket progress. Do not imply that 已執行 means 已完成.

### 已完成事項

Include a child task only when its verified status/resolution means completed, or when an explicit acceptance/test result proves completion. Show completion evidence, linked commit/MR, and verification result.

### 阻塞與待確認

Separate permission failures, missing assignee, missing estimates, unavailable worklogs, and unresolved external decisions from normal unfinished work.

## Calculate progress

Progress is based on child-task completion, never on the number of parent tickets or Jira records created.

When every child has a verified comparable estimate:

    completion percentage =
      sum(estimate of completed child tasks)
      / sum(estimate of all in-scope child tasks) × 100

When estimates are missing or incomparable, use the count fallback:

    completion percentage =
      completed child-task count
      / total in-scope child-task count × 100

Round to one decimal place. Always show numerator, denominator, weighting mode, and included child tasks. Do not count blocked or unknown tasks as complete.

For the per-ticket view:

- completed status/resolution: ticket progress 100%;
- verified not-started status with no period evidence: ticket progress 0%;
- in-progress/review status: show 執行中 and evidence; use a numeric partial percentage only when the ticket has verified checklist/subtask evidence;
- unknown or blocked: show 待確認 or 阻塞, and exclude it from the completed numerator.

Also report completed children, executed children, not-started children, total/completed estimate when available, and this-period activity separately from all-time completion.

## Output format

Produce Traditional Chinese Markdown with:

1. 週報標題、週期、時區、資料來源、產生時間。
2. 摘要：子任務完成數、完成度公式、執行數、未執行數、阻塞數。
3. 工作進度：公式、分子/分母、加權或數量模式。
4. 未執行。
5. 已執行，每張 Jira ticket 一列。
6. 已完成事項，附驗收證據。
7. 阻塞與風險。
8. 下週建議。
9. 資料限制與待人工確認。

Use this table shape:

| Jira ticket | 父任務 | 子任務 | 負責人 | 目前狀態 | Ticket 進度 | 預估 | 本週執行證據 | 完成證據 |
|---|---|---|---|---|---:|---:|---|---|

Do not invent missing values. Use 未設定、無資料、待確認 as appropriate.

## Example request

請產生 KNDU 專案 2026-09-01 至 2026-09-07 的週報，時區 Asia/Taipei。以 Jira 子任務完成度計算工作進度，每張 ticket 顯示本週 commit、MR、worklog 與目前進度；只讀取，不修改 Jira 或 GitLab。

