---
name: auto-commit-push
description: Analyze the git diff, produce a Conventional Commits message, safely stage only relevant files (never .env/credentials, never `git add -A`/`git add .`), commit, and push to the current branch. Use when the user asks to commit, auto-commit, "commit and push", or any request to automate the git commit/push flow, even if they don't say "conventional commits" or "push" explicitly. Built-in guardrails: detects sensitive files, detects main/master, detects a diverged/behind branch — stops and asks the user in those cases instead of acting blindly.
---

# Auto Commit & Push

Goal: make "produce a good commit + push safely" a fixed, repeatable
procedure so the user doesn't have to restate the rules every time, while
keeping the human in the loop on the risky decisions (main branch, diverged
branch, sensitive files).

## Full flow

### 0. (Optional) Shortcut token health check

Only needed if this branch/task will use the Shortcut integration (e.g. the
branch name contains `sc-XXXXX`, or the user wants ticket status synced).
Skip entirely for commits unrelated to Shortcut.

```bash
bash ~/.codex/skills/shortcut-token-renew/scripts/check_shortcut_token.sh
```

- exit 0: skip, go to step 1.
- exit 1 (expired): follow
  [shortcut-token-renew](../shortcut-token-renew/SKILL.md) to renew, then
  come back and continue.
- exit 2 (never configured): ignore if unrelated to this task, continue to
  step 1.

### 1. Gather current state (can run in parallel)

```bash
git status --short
git diff              # unstaged
git diff --staged     # staged but not committed
git log --oneline -10 # match this repo's recent commit style
```

**If the current branch name encodes a Shortcut ticket** (e.g. `sc-49` in
`ryan.yu/sc-49/misc`), the commit subject needs a `[sc-49]` prefix — this is
the exact format the GitLab↔Shortcut integration scans commit messages for
to auto-link a commit into the story's "Commits" list (verified against
this workspace: only commits with a `[sc-NN]` prefix showed up there, ones
without it did not, even on a correctly-named branch). Branches unrelated to
a ticket keep plain Conventional Commits with no prefix.

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

### 4. Write a Conventional Commits message

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
[sc-49] <type>: <subject>

Co-Authored-By: Codex <noreply@openai.com>
EOF
)"
```

(Only add the `[sc-49]`-style prefix when the branch is tied to that ticket
— see step 1. Otherwise it's just `<type>: <subject>`.)

Never add `--no-verify`, `--no-gpg-sign`, or `-c commit.gpgsign=false`.

If a pre-commit hook fails: the commit did not actually happen, so fix the
issue, re-`git add`, and create a **new** commit — don't `--amend` a commit
that doesn't exist.

### 5. Pre-push safety check

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

### 6. Verify

```bash
git status
```

Confirm the working tree is clean and the push succeeded.

### 7. (If the branch is tied to a Shortcut ticket) confirm it landed in Commits / Merge Requests

The GitLab↔Shortcut integration is a passive scanner, not something you
write into via a comment or API call:

- **Merge Requests**: any MR whose source branch name contains `sc-XXXXX`
  gets auto-linked into the story's "Merge Requests" list regardless of MR
  title — this happens automatically once the branch is pushed and an MR is
  opened, no extra action needed.
- **Commits**: the integration only recognizes the `[sc-49]`-style prefix
  *in the commit message* (see step 1/4) — branch name alone doesn't link
  individual commits. If step 4 added the prefix correctly, the push already
  gets the commit linked into the story's "Commits" list automatically.
- **Do not** post a manual comment listing commits as a substitute — a
  comment is not the same as a real entry in the Commits/Merge Requests
  section and doesn't count as integration.
- To confirm it actually landed, query the story (e.g. via the Shortcut API
  or MCP tool with full detail) and check its `commits` / `pull_requests`
  fields for this push's hash/MR. A commit already pushed without the
  prefix won't get backfilled by the integration — either accept that, or
  push a follow-up commit with the correct prefix.

### 8. Report

Keep it brief: short commit hash, first line of the commit message, push
result. No need to narrate every step taken.
