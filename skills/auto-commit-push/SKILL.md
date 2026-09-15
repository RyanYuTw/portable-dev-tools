---
name: auto-commit-push
description: >-
  Analyze the git diff, produce a Conventional Commits message, safely stage
  only relevant files (never .env/credentials, never `git add -A`/`git add .`),
  commit, push to the current branch, and offer to open a GitLab merge request
  afterwards. Use when the user asks to commit, auto-commit, "commit and push",
  or any request to automate the git commit/push flow, even if they don't say
  "conventional commits" or "push" explicitly. Built-in guardrails: asks
  whether to show the staged diff before committing, detects sensitive files,
  detects main/master, detects a diverged/behind branch — stops and asks the
  user in those cases instead of acting blindly.
---

# Auto Commit & Push

Goal: make "produce a good commit + push safely" a fixed, repeatable
procedure so the user doesn't have to restate the rules every time, while
keeping the human in the loop on the risky decisions (main branch, diverged
branch, sensitive files).

## Full flow

### 1. Gather current state (can run in parallel)

```bash
git status --short
git diff              # unstaged
git diff --staged     # staged but not committed
git log --oneline -10 # match this repo's recent commit style
```

**Jira/GitLab traceability (only when the current task is Jira-tracked):**

- Use the child Jira key in the commit subject, for example `feat(PROJ-124): add case merge authorization`.
- A parent key alone is not enough to identify a Jira subtask.
- If the task is Jira-tracked but no child key is known, stop before committing and ask for the key or direct the user to `jira-breakdown`.
- A commit creates execution evidence; it does not by itself prove that the Jira child is complete.
- After the commit is pushed, `jira-breakdown` may link the commit and transition the child only after MR merge, CI/acceptance evidence, and the exact Jira transition are verified.

### 2. Choose files to stage

- Only add files relevant to the current task that are actually
  modified/new.
- Never use `git add -A` or `git add .` — that risks sweeping in secrets or
  unrelated files.
- List filenames explicitly: `git add <file1> <file2> ...`
- If unsure whether a file belongs in version control (looks like local
  config, a large binary, an unexpected new file), ask the user first rather
  than guessing.

### 3. Secret scan

After `git add`, before commit:

```bash
bash ~/.codex/skills/auto-commit-push/scripts/check_secrets.sh
```

This checks the staged file list against common sensitive-file patterns
(`.env`, `*credential*`, `*secret*`, `id_rsa`, `*.pem`, `*.key`, service
account JSON, etc.); template files like `.env.example` are not
false-flagged.

- If it matches (non-zero exit), print the matched filenames, run
  `git restore --staged <file>`, and tell the user what was found and why
  the commit didn't proceed.
- Never bypass this with `--no-verify` or by ignoring the warning.

### 4. Offer the diff before committing

After the secret scan passes, before running `git commit`, ask the user once:

> 要先看 staged 的 git diff 嗎？（y = 顯示，Enter/n = 直接 commit）

- Default is **not** to show it — if the user says no, is silent, or the
  session is non-interactive, go straight to the commit.
- If the user says yes, show `git diff --staged` (start with
  `git diff --staged --stat` and follow with the full diff if the change is
  large), let them react, then commit.
- Ask only once per commit, and never skip the question just because the
  change looks small.
- This is a review checkpoint, not a permission gate: the user asking for the
  diff doesn't mean the commit is cancelled — wait for their reaction, then
  proceed unless they say to stop or change something.

### 5. Write a Conventional Commits message

Infer the type (`feat` / `fix` / `refactor` / `style` / `docs` / `test` /
`chore` / `perf` / ...) from the staged diff, write one concise imperative
subject line.

If the diff mixes multiple unrelated changes, propose splitting into
multiple commits and confirm the grouping with the user — don't force it
into one message, and don't silently split and commit on your own.

Always end the message with:

```
Co-Authored-By: Codex <noreply@openai.com>
```

Use a heredoc so formatting is preserved:

```bash
git commit -m "$(cat <<'EOF'
<type>: <subject>

Co-Authored-By: Codex <noreply@openai.com>
EOF
)"
```

Never add `--no-verify`, `--no-gpg-sign`, or `-c commit.gpgsign=false`.

If a pre-commit hook fails: the commit did not actually happen, so fix the
issue, re-`git add`, and create a **new** commit — don't `--amend` a commit
that doesn't exist.

### 6. Pre-push safety check

After committing:

```bash
bash ~/.codex/skills/auto-commit-push/scripts/check_push_safety.sh
```

This checks:

- Current branch: if `main` or `master`, exits non-zero — stop and tell the
  user, don't auto-push unless they explicitly ask.
- `git fetch` (read-only, doesn't touch the working tree) to compare
  local vs. upstream ahead/behind. If behind (needs rebase/merge or a force
  push to reconcile), exits non-zero — stop and ask the user how they want
  to resolve it; never auto-rebase/merge/force-push.

Only continue once the script exits 0:

```bash
git push                       # upstream already set
git push -u origin <branch>    # no upstream yet
```

For the normal case (not main/master, not diverged) there's no need to ask
before pushing — "automate this" is the whole point; only the two risk cases
above warrant stopping.

### 7. Verify

```bash
git status
```

Confirm the working tree is clean and the push succeeded.

### 8. Offer to open a merge request

After a successful push, ask the user once:

> 要幫你發 merge request 嗎？（y = 建立，Enter/n = 跳過）

- Default is **not** to create one — "no", silence, or a non-interactive
  session means skip it and just report the push.
- Don't ask at all when the push didn't happen (stopped on main/master or on a
  diverged branch). If the branch already has an open MR, report that MR's URL
  instead of asking — never open a second one for the same branch.
- If the user says yes, create it with the GitLab MCP `create_merge_request`
  (`gitlab.dbodm.com`):
  - project: resolve it from `git remote get-url origin`, never guess it
  - source: the current branch; target: the project's default branch
  - title: the commit subject, keeping the Jira key when there is one
  - description: what changed and how it was verified, plus the Jira key
- Report the MR URL. Do not merge, approve, or assign reviewers unless the
  user asks.

### 9. Report

Keep it brief: short commit hash, first line of the commit message, push
result, and the MR URL when one was created. No need to narrate every step
taken.
