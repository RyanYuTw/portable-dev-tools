# Portable Dev Tools

Portable Agent Plugins 1.0 bundle for Claude Code and Codex.

## Included components

### Skills

Response and workflow

- `caveman`: concise response modes.
- `open-vscode`: opens files or projects in VS Code.

Git and issue tracking

- `auto-commit-push`: analyzes changes, writes a Conventional Commits message, stages safely, commits, and pushes.
- `git-commit-sc`: commit helper for Shortcut-referenced work.
- `shortcut-commit-sync`: links commits to Shortcut tickets when an integration is available.
- `shortcut-api`: queries Shortcut story details through the REST API.
- `shortcut-ticket`: fetches and displays a Shortcut ticket by ID or URL.
- `shortcut-token-renew`: checks and renews an expired `SHORTCUT_API_TOKEN` across local config files.
- `shortcut-meeting-minutes`: generates meeting minutes from Shortcut data and exports them to DOCX.
- `task-to-jira`: analyzes a feature, splits unfinished implementation into verifiable tasks, and synchronizes confirmed work to Jira.

Documents and slides

- `pdf-markitdown-first`: converts PDFs to Markdown with MarkItDown before reading them.
- `office-file-generator`: generates DOCX, XLSX, PPTX, PDF, and charts.
- `html-slide-builder`: builds Reveal.js interactive decks and deploys them to GitHub Pages.
- `mckinsey-slides`: consulting-style slide templates.

Data and integrations

- `crawl4ai`: web crawling and extraction with Crawl4AI.
- `gdrive-crud`: Google Drive CRUD through a service account.

### MCP servers

- Context7 MCP: current library documentation.
- Playwright MCP: browser automation and web testing.
- GitHub MCP: repositories, issues, pull requests, and Actions.
- GitLab MCP: projects, issues, merge requests, pipelines, and APIs on `gitlab.dbodm.com`.
- Atlassian Rovo MCP: Jira Cloud, Confluence, and Compass.
- Shortcut MCP: stories, epics, iterations, and workflows.
- Fetch MCP: retrieves and converts web pages for the model.
- NotebookLM MCP: source-grounded answers from NotebookLM notebooks.

## Requirements

- Node.js 18 or newer and `npx` for Playwright, GitLab, and Shortcut MCP.
- `uv`/`uvx` for Fetch MCP.
- The `notebooklm-mcp` CLI on `PATH` for NotebookLM MCP (`uv tool install notebooklm-mcp-cli`), authenticated with `nlm login`.
- Python 3.10 or newer for the skills that ship scripts (`crawl4ai`, `gdrive-crud`, `html-slide-builder`, `shortcut-meeting-minutes`).
- A GitHub fine-grained personal access token in `GITHUB_PERSONAL_ACCESS_TOKEN`.
- A GitLab personal access token for `gitlab.dbodm.com` in `GITLAB_PERSONAL_ACCESS_TOKEN` (this instance has no native MCP endpoint, so GitLab MCP runs via `@zereight/mcp-gitlab` with a PAT instead of OAuth).
- A Shortcut API token in `SHORTCUT_API_TOKEN`.
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

## Security

GitHub MCP can write to repositories, issues, and pull requests according to token permissions. Prefer a fine-grained token restricted to selected repositories and the minimum required permissions. Review write operations before approval.
