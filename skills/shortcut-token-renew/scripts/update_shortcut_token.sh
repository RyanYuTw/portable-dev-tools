#!/usr/bin/env bash
# 把新的 SHORTCUT_API_TOKEN 值寫進所有已知的設定檔，取代舊值。
# 新 token 一律從 stdin 讀入（不當成命令列參數，避免出現在 ps/shell history）。
# 用法：printf '%s' "$NEW_TOKEN" | update_shortcut_token.sh
#
# 純 bash + perl，不依賴任何特定 agent 工具，Claude Code 或 Codex 都能直接執行。
set -euo pipefail

NEW_TOKEN="$(cat)"
if [ -z "$NEW_TOKEN" ]; then
  echo "❌ 沒有從 stdin 讀到 token" >&2
  exit 1
fi
export NEW_TOKEN

# 只列出已知、明確屬於「本機設定檔」的位置；絕不掃描 ~/.claude/projects 底下的
# 對話紀錄（那些是歷史 log，不是生效中的設定，改了也沒用、還會弄髒 log）。
CANDIDATES=(
  "$HOME/.zshrc"
  "$HOME/.zprofile"
  "$HOME/.bash_profile"
  "$HOME/.bashrc"
  "$HOME/.claude/settings.local.json"
  "$HOME/.codex/config.toml"
)

updated=0
for f in "${CANDIDATES[@]}"; do
  [ -f "$f" ] || continue
  grep -q 'SHORTCUT_API_TOKEN' "$f" || continue

  case "$f" in
    *.json)
      perl -0pi -e 's/("SHORTCUT_API_TOKEN":\s*")[^"]*(")/$1.$ENV{NEW_TOKEN}.$2/e' "$f"
      ;;
    *.toml)
      perl -0pi -e 's/(SHORTCUT_API_TOKEN\s*=\s*")[^"]*(")/$1.$ENV{NEW_TOKEN}.$2/e' "$f"
      ;;
    *)
      perl -0pi -e 's/(SHORTCUT_API_TOKEN=")[^"]*(")/$1.$ENV{NEW_TOKEN}.$2/e' "$f"
      ;;
  esac
  echo "已更新: $f"
  updated=$((updated + 1))
done

unset NEW_TOKEN

if [ "$updated" -eq 0 ]; then
  echo "⚠️  沒有找到任何已知設定檔含有 SHORTCUT_API_TOKEN，未做任何變更" >&2
  exit 1
fi

echo "共更新 $updated 個檔案（token 內容不會印出）"
