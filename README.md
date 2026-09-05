# Portable Dev Tools

Portable Agent Plugins 1.0 bundle for Claude Code and Codex.

## Included components

- `caveman`: concise response modes.
- `shortcut-commit-sync`: links commits to Shortcut tickets when an integration is available.
- Context7 MCP: current library documentation.
- Playwright MCP: browser automation and web testing.
- GitHub MCP: repositories, issues, pull requests, and Actions.

## Requirements

- Node.js 18 or newer and `npx` for Playwright MCP.
- A GitHub fine-grained personal access token in `GITHUB_PERSONAL_ACCESS_TOKEN`.
- Network access to Context7 and GitHub MCP endpoints.

Do not commit tokens. Store `GITHUB_PERSONAL_ACCESS_TOKEN` in the shell or a secret manager on each computer.

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
