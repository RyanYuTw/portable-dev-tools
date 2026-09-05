---
name: shortcut-commit-sync
description: "Synchronize Git commits with Shortcut tickets when a commit request includes a Shortcut ticket number or identifier."
---

# Shortcut Commit Sync

Use this skill when creating a Git commit and the user supplies or the commit
message contains a Shortcut ticket reference, such as `sc-49` or `SC-49`.

## Required behavior

- Treat the supplied ticket number as a Shortcut ticket identifier, not as an
  unrelated numeric value.
- Create the Git commit first, then record the resulting commit SHA, commit
  message, repository, and branch in that Shortcut ticket's commits/activity
  field using the connected Shortcut integration.
- Preserve the exact ticket identifier when locating the ticket. Do not infer
  a different story, project, or workspace from the number.
- If the Shortcut integration is unavailable or not connected, complete the Git
  commit when authorized but clearly report that the Shortcut synchronization
  did not occur. Never claim that a ticket was updated without a successful
  tool result.
- If the ticket cannot be found or the update fails, keep the Git commit and
  report the specific synchronization failure; do not amend, revert, or create
  another commit solely to retry the Shortcut update.
- Do not put credentials, tokens, or other secrets into commit messages or
  skill files.

## Ticket reference handling

Recognize common references such as `sc-49`, `SC-49`, or a user-provided
Shortcut ticket number associated with the current commit request. If a commit
message contains several possible numbers and the intended ticket is unclear,
ask before committing rather than updating the wrong ticket.

The skill only governs the Git-to-Shortcut synchronization step. It does not
authorize pushing Git branches, changing ticket status, assigning tickets, or
editing other Shortcut fields unless the user separately requests those
actions.
