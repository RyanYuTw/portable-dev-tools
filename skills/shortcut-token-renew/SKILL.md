---
name: shortcut-token-renew
description: Check whether the Shortcut API token (SHORTCUT_API_TOKEN) is still valid, and if expired, help create a new token, delete the old one, and sync the new value into every known local config file. Use when a Shortcut-related call returns 401, or when asked to check/renew the Shortcut token. Can also run as a pre-check before commit & push on a branch tied to a Shortcut ticket.
---

# Shortcut Token Renewal

Shortcut API tokens have a short lifetime. Once expired, every Shortcut-related
call (REST API, `shortcut-api` skill, etc.) returns 401. This skill fixes the
"detect expiry → issue new token → delete old token → sync config files" flow.

## Hard constraint: issuing/deleting a token can only be done on the website

Shortcut has no API endpoint to self-issue or self-revoke a token — it can
only be done at
`https://app.shortcut.com/{workspace}/settings/account/api-tokens`, and
logging in there normally requires a human present (password + 2FA/SSO). So
this flow is inherently two-part:

- **Fully scriptable, no human needed**: checking whether the token is still
  valid, and writing a new token value into every config file. These are
  plain bash + curl/perl scripts under `scripts/`, with no dependency on any
  specific agent runtime — any agent that can run a shell command can call
  them directly.
- **Needs an agent with browser control plus a human**: logging into the
  Shortcut website, clicking "Create Token", clicking "Delete Token". If the
  current agent has no browser tool, print the steps and have the user do
  them by hand.

## Full flow

### 1. Check whether the current token is still valid

```bash
bash ~/.codex/skills/shortcut-token-renew/scripts/check_shortcut_token.sh
```

- exit 0: valid, stop here.
- exit 2: `SHORTCUT_API_TOKEN` was never set — tell the user and stop (this is
  not "expired", it was never configured).
- exit 1: expired — continue to the renewal flow below.

### 2. Issue a new token (needs a browser)

If the current agent has a browser tool:

1. Navigate to
   `https://app.shortcut.com/{workspace}/settings/account/api-tokens` (the
   workspace slug is usually known from the old token value or a URL the
   user already provided; ask if unsure).
2. If redirected to the login page, stop and tell the user to log in by hand
   in that window (including 2FA/SSO if any); wait for their confirmation
   before continuing. **Never** touch the credential fields or submit the
   login form on the user's behalf.
3. Once logged in, note the **Name** and **Access** of the token being
   replaced from the existing list (e.g. "Read + Write + Admin" maps to the
   "Full access" radio) so the new token gets the same name and scope.
4. Click **Create Token**, fill in the same name, pick the same permission
   level, submit.
5. The page shows the new token value exactly once. Read it via the browser
   tool's DOM/element output — **never print this value in your visible
   reply**; pipe it straight into the next step.

If the current agent has no browser tool: print steps 1-5 above so the user
can do them manually, and have them paste the new token back to you (still
don't echo it back verbatim as confirmation — go straight to step 3).

### 3. Write the new token into every config file

Always pass the new value via stdin, never as a command-line argument (that
would leak into shell history / `ps` output):

```bash
printf '%s' "$NEW_TOKEN" | bash ~/.codex/skills/shortcut-token-renew/scripts/update_shortcut_token.sh
```

This updates (only touches files that already reference
`SHORTCUT_API_TOKEN`):
- `~/.zshrc`, `~/.zprofile`, `~/.bash_profile`, `~/.bashrc`
- `~/.claude/settings.local.json`
- `~/.codex/config.toml`

If the token lives somewhere else (a project `.env`, CI secrets), this
script won't reach it — tell the user to update that manually.

### 4. Delete the old token

Back in the browser, find the row for the token noted in step 2.3, click
**Delete token**, confirm in the dialog. Verify the page shows a "deleted"
confirmation and the list no longer has the old entry.

### 5. Verify

```bash
bash ~/.codex/skills/shortcut-token-renew/scripts/check_shortcut_token.sh
```

**Note**: if this is happening inside an already-running agent
session/process, that process's environment variables were fixed at
startup — updating config files won't make the *running* process pick up
the new value immediately. A new session/process is needed for that. The
command above only verifies the value stored in the config files is itself
valid.

## Integrating with commit & push

If the branch or task needs to sync a Shortcut ticket (e.g. branch name
contains `sc-XXXXX`), run step 1's health check at the start of the
commit-and-push flow; only go through steps 2-5 if it's actually expired.
Skip entirely for repos/commits that don't touch Shortcut.

## Security notes

- Never let the new token value appear in visible reply text — only pass it
  through tool parameters (browser tool reads, script stdin).
- Never use `-p'token-value'`-style flags that leave secrets in shell
  history or `ps` output — always use stdin or environment variables.
- Credential entry is always done by the human, never by the agent.
- Confirm a config update succeeded by comparing value *length*, not by
  printing the actual value (old/new tokens are normally the same format).
