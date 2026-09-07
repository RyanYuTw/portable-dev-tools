---
name: git-commit-sc
description: "Generate git commit messages with Shortcut ticket numbers in format [sc-XXXXX] type: subject. Analyzes staged changes, determines commit type automatically, and outputs ready-to-use git commit commands. Use when user wants to commit with a Shortcut ticket reference."
license: MIT
metadata:
  author: TNL
  version: 1.0.0
---

# Git Commit with Shortcut Ticket

Automatically generate properly formatted git commit messages that include Shortcut ticket numbers.

## Commit Message Format

```
[sc-<ticket_number>] <type>: <subject>
```

### Commit Types

- **feat**: 新功能 (New feature)
- **fix**: 修復 bug (Bug fix)
- **refactor**: 重構 (Refactoring, no functional change)
- **style**: 格式調整 (Formatting, no logic change)
- **docs**: 文件更新 (Documentation)
- **test**: 測試相關 (Tests)
- **chore**: 建置或工具相關 (Build tools, dependencies)

## When to Use

- User mentions committing with a Shortcut ticket
- User provides a ticket number and wants to commit
- User asks for help writing a commit message
- User says "commit this to sc-12345"

## Workflow

### 1. Get Ticket Number

If not provided, ask:
```
請提供 Shortcut ticket number (例如: 12345 或 sc-12345)
```

### 2. Check Staged Changes

```bash
# Check what's staged
git diff --staged --stat

# If nothing staged, check unstaged changes
if [ -z "$(git diff --staged)" ]; then
  echo "⚠️  No staged changes. Checking unstaged changes..."
  git diff --stat
  echo ""
  echo "Please stage your changes first:"
  echo "  git add <files>"
fi
```

### 3. Analyze Changes

```bash
# Get detailed diff for analysis
git diff --staged
```

Analyze the diff to determine:
- **Type**: What kind of change is this?
  - New files/features → `feat`
  - Bug fixes → `fix`
  - Code restructuring → `refactor`
  - Formatting only → `style`
  - Documentation → `docs`
  - Tests → `test`
  - Build/config → `chore`

- **Subject**: Concise description (max 72 chars)
  - Start with lowercase verb
  - No period at the end
  - Be specific but brief

### 4. Generate Commit Command

**Simple commit (one-liner):**
```bash
git commit -m "[sc-<ticket>] <type>: <subject>"
```

**With body (complex changes):**
```bash
git commit -m "[sc-<ticket>] <type>: <subject>" -m "<body explaining why/how>"
```

## Examples

### Example 1: New Feature
```bash
# Changes: Added new caching command for articles
git commit -m "[sc-12345] feat: add article cache build command"
```

### Example 2: Bug Fix with Body
```bash
# Changes: Fixed N+1 query issue in category counting
git commit -m "[sc-67890] fix: resolve category count query issue" \
  -m "Fixed N+1 query problem in CountCategoryArticleCommand by using eager loading"
```

### Example 3: Refactoring
```bash
# Changes: Extracted duplicate code into helper method
git commit -m "[sc-11111] refactor: extract cache key generation to helper"
```

### Example 4: Multiple Files
```bash
# Changes: Updated controller, model, and tests
git commit -m "[sc-22222] feat: add article filtering by category" \
  -m "- Added category filter in ArticleController
- Updated Article model with scope
- Added integration tests"
```

## Implementation Steps

When user triggers this skill:

1. **Extract ticket number**
   ```bash
   # Handle various formats
   TICKET=$(echo "$INPUT" | grep -oE '[0-9]+' | head -1)
   ```

2. **Check git status**
   ```bash
   if ! git diff --staged --quiet; then
     echo "✅ Found staged changes"
     git diff --staged --stat
   else
     echo "❌ No staged changes"
     git status --short
     exit 1
   fi
   ```

3. **Analyze and suggest**
   - Read the diff output
   - Identify file types and change patterns
   - Determine appropriate commit type
   - Write concise subject line

4. **Present options**
   ```
   Based on your changes, I suggest:
   
   Option A (Recommended):
   git commit -m "[sc-12345] feat: add user authentication"
   
   Option B (With details):
   git commit -m "[sc-12345] feat: add user authentication" \
     -m "Implemented JWT-based auth with refresh tokens"
   
   Would you like to use one of these, or modify them?
   ```

5. **Execute if confirmed**
   ```bash
   # Only run if user confirms
   git commit -m "[sc-12345] feat: add user authentication"
   ```

## Best Practices

### Subject Line Rules
- Use imperative mood ("add" not "added" or "adds")
- Keep under 72 characters
- Don't capitalize first word after type
- No period at the end
- Be specific: "add user auth" not "update code"

### When to Add Body
Add a body when:
- Changes affect multiple areas
- Complex logic needs explanation
- Breaking changes
- Important context for reviewers

### Type Selection Guide
```
New feature          → feat
Bug fix              → fix
No functional change → refactor
Whitespace/format    → style
README/comments      → docs
Test files           → test
package.json/config  → chore
```

## Edge Cases

### No Changes Staged
```bash
if [ -z "$(git diff --staged)" ]; then
  echo "⚠️  No changes staged for commit"
  echo ""
  echo "Unstaged changes:"
  git status --short
  echo ""
  echo "Stage files with: git add <files>"
  exit 1
fi
```

### Invalid Ticket Number
```bash
if ! [[ "$TICKET" =~ ^[0-9]+$ ]]; then
  echo "❌ Invalid ticket number: $TICKET"
  echo "Please provide a numeric ticket ID (e.g., 12345)"
  exit 1
fi
```

### Multiple Logical Changes
```
⚠️  Your diff contains multiple unrelated changes:
  - Feature: New authentication
  - Fix: Category bug
  - Refactor: Extract helpers

Consider splitting into separate commits:
  1. git add <auth-files> && git commit -m "[sc-12345] feat: ..."
  2. git add <bug-files> && git commit -m "[sc-12346] fix: ..."
```

## Quick Reference

```bash
# Check what will be committed
git diff --staged --stat

# Stage specific files
git add file1.js file2.js

# Stage all changes
git add .

# Unstage files
git restore --staged <file>

# Amend last commit
git commit --amend -m "[sc-12345] feat: updated subject"
```

## Co-Authoring

If pair programming, add co-author:
```bash
git commit -m "[sc-12345] feat: add feature" \
  -m "Co-authored-by: Name <email@example.com>"
```

## Notes

- Always analyze the actual diff, don't assume
- Keep subject lines concise and descriptive
- Use body for "why", not "what" (diff shows "what")
- Verify ticket number is valid before committing
- Don't commit if changes are too broad (suggest splitting)
