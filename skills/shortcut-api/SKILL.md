---
name: shortcut-api
description: "Query Shortcut.com story details via API. Use when user mentions a Shortcut ticket number (sc-XXXXX) or needs to fetch story information. Requires SHORTCUT_API_TOKEN environment variable."
license: MIT
metadata:
  author: TNL
  version: 1.0.0
---

# Shortcut API Skill

Query Shortcut.com stories via the official API. This skill provides direct API access to fetch story details, search stories, and extract ticket information.

## When to Use

- User mentions a Shortcut ticket number (e.g., "sc-123456", "SC-123456")
- User asks about a specific story's details
- User wants to search for stories by keyword
- User needs to check story status, description, or labels

## Prerequisites

Set the Shortcut API token as an environment variable:

```bash
export SHORTCUT_API_TOKEN="your-token-here"
```

Get your token from: https://app.shortcut.com/settings/account/api-tokens

## Usage Patterns

### 1. Query Single Story by ID

Extract the story ID from user input (remove "sc-" prefix if present):

```bash
# Example: For "sc-123456" or "123456"
STORY_ID="123456"

curl -s -H "Shortcut-Token: $SHORTCUT_API_TOKEN" \
  "https://api.app.shortcut.com/api/v3/stories/${STORY_ID}" | \
  python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(f'''
📋 Story: sc-{d['id']}

**Title**: {d['name']}
**Type**: {d['story_type']}
**State**: {d.get('workflow_state_id', 'N/A')}
**URL**: {d['app_url']}

**Description**:
{d.get('description', 'No description')}

**Labels**: {', '.join([l['name'] for l in d.get('labels', [])])}
''')
except Exception as e:
    print(f'❌ Error: {e}')
    sys.exit(1)
"
```

### 2. Search Stories by Keyword

```bash
KEYWORD="your search term"

curl -s -H "Shortcut-Token: $SHORTCUT_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"${KEYWORD}\", \"page_size\": 10}" \
  "https://api.app.shortcut.com/api/v3/search/stories" | \
  python3 -c "
import sys, json
try:
    result = json.load(sys.stdin)
    stories = result.get('data', [])
    print(f'Found {len(stories)} stories:\n')
    for s in stories[:5]:
        print(f'• sc-{s[\"id\"]}: {s[\"name\"]} ({s[\"story_type\"]})')
        print(f'  {s[\"app_url\"]}\n')
except Exception as e:
    print(f'❌ Error: {e}')
"
```

### 3. Extract Story ID from User Input

```bash
# Handle various formats: "sc-123456", "SC-123456", "123456", or URL
INPUT="sc-123456"  # or user input

# Extract numeric ID
STORY_ID=$(echo "$INPUT" | grep -oE '[0-9]+' | head -1)

if [ -z "$STORY_ID" ]; then
  echo "❌ Invalid story ID format"
  exit 1
fi

echo "Story ID: $STORY_ID"
```

### 4. Get Story with Full Details

```bash
STORY_ID="123456"

curl -s -H "Shortcut-Token: $SHORTCUT_API_TOKEN" \
  "https://api.app.shortcut.com/api/v3/stories/${STORY_ID}"
```

Returns JSON with fields:
- `id`: Story ID (number)
- `name`: Story title
- `description`: Story description (Markdown)
- `story_type`: `feature` | `bug` | `chore`
- `workflow_state_id`: Current workflow state
- `labels`: Array of label objects
- `app_url`: Web URL to story
- `owners`: Array of owner objects
- `comments`: Array of comment objects (if expanded)
- `tasks`: Array of task objects

## Error Handling

```bash
# Check if token is set
if [ -z "$SHORTCUT_API_TOKEN" ]; then
  echo "❌ SHORTCUT_API_TOKEN not set"
  echo "Get token from: https://app.shortcut.com/settings/account/api-tokens"
  exit 1
fi

# Check API response
RESPONSE=$(curl -s -w "\n%{http_code}" -H "Shortcut-Token: $SHORTCUT_API_TOKEN" \
  "https://api.app.shortcut.com/api/v3/stories/${STORY_ID}")

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_CODE" != "200" ]; then
  echo "❌ API Error (HTTP $HTTP_CODE)"
  echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
  exit 1
fi
```

## Implementation Notes

- Always validate `SHORTCUT_API_TOKEN` before making API calls
- Extract numeric story ID from user input (handle "sc-" prefix)
- Use Python for JSON parsing to ensure clean output
- Include story URL in responses for quick access
- Limit search results to 5-10 items for readability
- Format output with clear sections and emoji for better UX

## API Reference

Base URL: `https://api.app.shortcut.com/api/v3`

Headers:
- `Shortcut-Token: <your-token>`
- `Content-Type: application/json` (for POST/PUT)

Endpoints:
- GET `/stories/{story-id}` - Get single story
- POST `/search/stories` - Search stories
- GET `/stories/{story-id}/comments` - Get story comments
- GET `/workflows` - Get workflow states

Documentation: https://developer.shortcut.com/api/rest/v3
