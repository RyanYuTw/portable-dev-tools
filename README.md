# Portable Dev Tools

Portable Agent Plugins 1.0 bundle for Claude Code and Codex.

## Included components

### Skills

Response and workflow

- `open-vscode`: opens files or projects in VS Code.

Git and issue tracking

- `auto-commit-push`: analyzes changes, writes a Conventional Commits message, stages safely, commits, and pushes.
- `task-to-jira`: analyzes a feature, splits unfinished implementation into verifiable tasks, and synchronizes confirmed work to Jira.
- `weekly-jira-report`: generates a read-only weekly report with per-ticket execution evidence and child-task completion progress.
- `jira-breakdown`: splits a requirement into Jira tasks and sub-tasks, fills start/due dates, priority, category and labels, and asks who to assign before writing.
- `jira-ticket-plan`: reads a Jira ticket with its parent and siblings, verifies it against the repository, and proposes an execution plan that waits for approval.
- `weekly-report-mail`: turns the weekly report into a mail, collects the figures only a human can supply, and sends it after explicit confirmation.
- `ims-frontend-integration`: integrates IMS frontend OTP/JWT authentication, builds, and deployment synchronization.

Documents and slides

- `pdf-markitdown-first`: converts PDFs to Markdown with MarkItDown before reading them.
- `office-file-generator`: generates DOCX, XLSX, PPTX, PDF, and charts.
- `html-slide-builder`: builds Reveal.js interactive decks and deploys them to GitHub Pages.
- `mckinsey-slides`: consulting-style slide templates.

Data and integrations

- `crawl4ai`: web crawling and extraction with Crawl4AI.
- `gdrive-crud`: Google Drive CRUD through a service account.

Engineering workflow (imported from [obra/superpowers](https://github.com/obra/superpowers), MIT — see `licenses/superpowers-LICENSE.txt`)

- `brainstorming`: structured idea exploration before committing to an approach.
- `writing-plans`: turns a brainstormed approach into a checkbox-tracked implementation plan.
- `executing-plans`: executes a written plan task-by-task with review checkpoints (single session).
- `subagent-driven-development`: executes a written plan by dispatching implementer/reviewer subagents per task.
- `dispatching-parallel-agents`: fans independent work out to parallel subagents.
- `using-git-worktrees`: creates and manages isolated git worktrees for a task.
- `test-driven-development`: RED-GREEN-REFACTOR cycle and guidance on writing meaningful tests.
- `systematic-debugging`: root-cause-first debugging process for bugs, test failures, and unexpected behavior.
- `requesting-code-review`: prepares and requests a code review before merging.
- `receiving-code-review`: process for triaging and acting on code review feedback.
- `finishing-a-development-branch`: closes out a branch — merge/PR, worktree cleanup, follow-ups.
- `verification-before-completion`: checklist to verify work actually satisfies the task before reporting done.
- `writing-skills`: guidance for authoring new Claude Code / Codex skills.

Only the 13 task skills were imported. The upstream `using-superpowers` meta-skill and its `SessionStart` hook (which force a skill-relevance check before every response) were intentionally left out — they are a global behavior change across this whole plugin and conflict with this repo's choice to keep enforcement in git hooks rather than agent-level hooks (see "Git hooks" below). These skills trigger the same way every other skill in this repo does: by relevance of their own `description`.

### MCP servers

- Context7 MCP: current library documentation.
- Playwright MCP: browser automation and web testing.
- GitHub MCP: repositories, issues, pull requests, and Actions.
- GitLab MCP: projects, issues, merge requests, pipelines, and APIs on `gitlab.dbodm.com`.
- Atlassian Rovo MCP: Jira Cloud, Confluence, and Compass.
- Fetch MCP: retrieves and converts web pages for the model.
- codebase-memory MCP: local tree-sitter/LSP knowledge graph of the repo (search, call chains, impact analysis) for large-repo code exploration; 100% local, no API key. Launched via `npx codebase-memory-mcp@latest` with no CLI args, so it starts as a plain stdio MCP server — the vendor's own auto-installer (which rewrites `~/.claude.json`, installs its own hooks/skills/subagents across ~45 clients, and runs a shared background daemon) was intentionally **not** run; see [manual configuration](https://github.com/DeusData/codebase-memory-mcp#manual-mcp-configuration) upstream. First use downloads a large (~40 MB compressed / ~300 MB installed) checksum-verified native binary per machine — expect a slow first launch.

## Requirements

- Node.js 18 or newer and `npx` for Playwright, GitLab, and codebase-memory MCP.
- `uv`/`uvx` for Fetch MCP.
- Python 3.10 or newer for the skills that ship scripts (`crawl4ai`, `gdrive-crud`, `html-slide-builder`).
- `graphviz` (`dot`) is optional, only needed by `writing-skills`' diagram renderer.
- A GitHub fine-grained personal access token in `GITHUB_PERSONAL_ACCESS_TOKEN`.
- A GitLab personal access token for `gitlab.dbodm.com` in `GITLAB_PERSONAL_ACCESS_TOKEN` (this instance has no native MCP endpoint, so GitLab MCP runs via `@zereight/mcp-gitlab` with a PAT instead of OAuth).
- `GDRIVE_SA_KEY_PATH` pointing at a Google service account key file for `gdrive-crud`.
- Network access to Context7, GitHub, and GitLab MCP endpoints.
- Browser access for Atlassian OAuth authorization.

Do not commit tokens. Store every credential in the shell or a secret manager on each computer. Skill reference files use placeholders such as `FIREBASE_API_KEY`; replace them locally and never commit the real values.

## Claude Code

Install from a marketplace or load the plugin directory for development:

```sh
claude --plugin-dir /path/to/portable-dev-tools
```

Claude Code asks for approval before it uses project or plugin MCP servers.

## Codex

Install the marketplace entry, then start a new thread so skills and MCP tools load:

```sh
codex plugin add portable-dev-tools@personal
```

## Cross-computer sharing

Put this directory in a private or public Git repository. Clone it on another computer, set the required environment variables there, and install it from that clone's marketplace. Machine-specific credentials remain outside Git.

The version-controlled source of truth is the `skills/` directory and `.mcp.json`. Local Codex runtime settings and bundled app MCPs—such as `node_repl` and `computer-use`, which depend on a specific installation and absolute paths—are intentionally not copied into this portable plugin. Install or update the plugin after syncing so the shared skills and MCP servers are loaded by Codex.

## Git hooks

Enforcement lives in git hooks rather than agent-specific hooks, so it applies to Codex, Claude Code and a bare terminal alike. Agent-level hooks resolve the repository from the session working directory, which checks the wrong repository as soon as a command changes directory.

~~~sh
scripts/install-git-hooks.sh /path/to/repo
~~~

- `pre-push`: refuses the push while the full SHA of `HEAD` is absent from `.claude/state/reviewed`, and prints the review options for both tools.
- `post-commit`: extracts the Jira keys from the commit message and prints the follow-up actions — transition a not-started ticket to in progress, ask before completing a sub-task, map the category from the commit type.

Record a reviewed commit with `echo <full-sha> >> .claude/state/reviewed`. Remove both files from `.git/hooks/` to disable them.

## Syncing to Codex

Codex caches a plugin as a **version-locked snapshot**, not a live link to this directory. Editing files here without changing the version leaves Codex running the previous snapshot, and `codex plugin add` reports success either way — a silent staleness that has already bitten us once.

~~~sh
scripts/sync-codex.sh            # bump the patch version, reinstall, verify
scripts/sync-codex.sh 0.7.0      # set the version explicitly
~~~

The script bumps `.codex-plugin/plugin.json`, reinstalls from the `personal` marketplace (override with `MARKETPLACE=`), then compares the **whole tree** against this directory and exits non-zero on any difference — so a stale cache fails loudly instead of passing quietly. Only VCS and build noise is excluded (`.git`, `node_modules`, `__pycache__`, `.DS_Store`, `*.pyc`, `venv`, `.venv`); everything the plugin ships, documentation included, is checked. Commit the version change afterwards.

The order matters: **finish every edit, then sync, then commit the version bump** (`git commit --amend` folds it into the same commit). Syncing halfway through leaves GitHub ahead of Codex with nothing to show for it — a mistake made twice while building this, which is why it is now enforced rather than documented:

~~~sh
scripts/install-plugin-hooks.sh   # once per clone
scripts/sync-codex.sh --check     # what the hook runs
~~~

That installs a `pre-push` hook in this repository which refuses to push while the Codex cache lags behind the working tree, and names the files that differ.

Claude Code needs none of this: it reads this directory through a directory marketplace, so edits apply to the next session directly.

## Jira/GitLab workflow

For a Jira-tracked GitLab change:

1. Use `task-to-jira` to inspect the repository, split unfinished work into independently verifiable Jira tasks, and preview the exact fields before any Jira write.
2. Put the child Jira key in the commit subject, for example `feat(KNDU-124): add case merge authorization`.
3. Treat a linked commit as execution evidence. Only auto-complete the child after the pushed commit is in a merged MR and CI/acceptance evidence succeeds.
4. Use `weekly-jira-report` to show one row per Jira ticket, including status, this-period commits/MRs/worklogs, ticket progress, and completion evidence.

The GitLab MCP uses `GITLAB_PERSONAL_ACCESS_TOKEN` and `https://gitlab.dbodm.com/api/v4`; the Atlassian MCP uses browser OAuth. Keep both credentials outside Git.

The detailed Traditional Chinese setup and operation manual is available at [docs/AI-Jira-GitLab-工作流設定操作手冊.md](docs/AI-Jira-GitLab-工作流設定操作手冊.md).

## Codex-to-Claude synchronization

This repository is the portable synchronization boundary between Codex and Claude Code:

- Shared Skills live under `skills/` and are loaded by both plugin runtimes.
- Shared MCP servers live in `.mcp.json` and use environment variables or OAuth, not machine-specific secrets.
- The current shared MCP set includes Context7, Playwright, GitHub, GitLab, Atlassian, and Fetch.
- Codex-only runtime services such as `node_repl`, computer-use backends, and absolute application paths stay in Codex local configuration and are not copied into Claude Code.

To use the synchronized bundle in Claude Code:

~~~sh
claude --plugin-dir /path/to/portable-dev-tools
~~~

After pulling a newer version, start a new Claude Code session so the updated Skills and MCP definitions are reloaded. Set the required environment variables on that computer before using GitHub, GitLab, or Google Drive.

## Security

GitHub MCP can write to repositories, issues, and pull requests according to token permissions. Prefer a fine-grained token restricted to selected repositories and the minimum required permissions. Review write operations before approval.
