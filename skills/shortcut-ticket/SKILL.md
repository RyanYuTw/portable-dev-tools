---
description: Fetch and display Shortcut ticket details by story ID or URL
args:
  ticket_id: Story ID (e.g., sc-123456) or Shortcut URL
---

# Shortcut Ticket Reader

Fetches detailed information from a Shortcut story including:
- Title and description
- Current state and workflow
- Story type and priority
- Comments and activity
- Associated tasks and blockers
- Story owner and requesters

## Usage

You can provide either:
1. A story ID: `sc-123456`
2. A full Shortcut URL: `https://app.shortcut.com/tnlmedia/story/123456/...`

## Instructions

1. Extract the story ID from the input:
   - If it's a URL like `https://app.shortcut.com/tnlmedia/story/123456/...`, extract `123456`
   - If it's in format `sc-123456`, extract `123456`
   - If it's just a number `123456`, use it directly

2. Use the Shortcut API to fetch story details:
   ```bash
   curl -X GET \
     -H "Content-Type: application/json" \
     -H "Shortcut-Token: ${SHORTCUT_API_TOKEN}" \
     "https://api.app.shortcut.com/api/v3/stories/STORY_ID"
   ```

3. Format and display the response including:
   - **Story ID**: sc-{id}
   - **Title**: {name}
   - **State**: {workflow_state_id name}
   - **Type**: {story_type}
   - **Priority**: {priority}
   - **Description**: {description}
   - **Owner**: {owner names}
   - **URL**: https://app.shortcut.com/tnlmedia/story/{id}
   - **Comments**: Recent comments if any
   - **Tasks**: List of tasks with completion status
   - **Blockers**: Any blocked/blocking relationships

4. If the API returns an error (e.g., 404, 401):
   - Check if SHORTCUT_API_TOKEN environment variable is set
   - Verify the story ID is correct
   - Provide a helpful error message

## Environment Setup

This skill requires a Shortcut API token. To set it up:

```bash
# Get your token from: https://app.shortcut.com/settings/account/api-tokens
export SHORTCUT_API_TOKEN="your-token-here"
```

Or add it to your ~/.claude/settings.json:

```json
{
  "env": {
    "SHORTCUT_API_TOKEN": "your-token-here"
  }
}
```

## Example

Input: `sc-102893` or `https://app.shortcut.com/tnlmedia/story/102893/...`

Output:
```
📋 Shortcut Story: sc-102893

Title: Override CDN cache headers with s-maxage
State: Completed
Type: Feature
Priority: Medium

Description:
Add s-maxage and stale-while-revalidate directives to CDN cache headers...

Owner: Ryan Yu
URL: https://app.shortcut.com/tnlmedia/story/102893

Tasks:
✓ Update cache headers in API
✓ Test with CDN provider
✗ Update documentation

Comments: 3 comments (most recent 2 days ago)
```
