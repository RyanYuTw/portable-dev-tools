#!/usr/bin/env bash
# 檢查 SHORTCUT_API_TOKEN 是否還有效。
# exit 0: 有效；exit 1: 已過期/失效；exit 2: 未設定。
# 純 bash + curl，不依賴任何特定 agent 工具，Claude Code 或 Codex 都能直接執行。
set -euo pipefail

if [ -z "${SHORTCUT_API_TOKEN:-}" ]; then
  echo "SHORTCUT_API_TOKEN 未設定"
  exit 2
fi

status="$(curl -s -o /dev/null -w '%{http_code}' \
  -H "Shortcut-Token: $SHORTCUT_API_TOKEN" \
  "https://api.app.shortcut.com/api/v3/member")"

if [ "$status" = "200" ]; then
  echo "✅ SHORTCUT_API_TOKEN 有效"
  exit 0
else
  echo "⚠️  SHORTCUT_API_TOKEN 已失效（HTTP $status），需要重新申請"
  exit 1
fi
