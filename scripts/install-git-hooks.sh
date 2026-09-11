#!/usr/bin/env bash
# 把 portable-dev-tools 的 git hooks 安裝到目標儲存庫。
# 用法：install-git-hooks.sh [目標儲存庫路徑]   （預設為目前目錄）
set -euo pipefail

src="$(cd "$(dirname "${BASH_SOURCE[0]}")/../hooks" && pwd)"
target="${1:-$PWD}"

root=$(git -C "$target" rev-parse --show-toplevel 2>/dev/null) || {
  echo "錯誤：$target 不是 git 儲存庫" >&2; exit 1; }

dest="$root/.git/hooks"
mkdir -p "$dest" "$root/.claude/state"

for h in pre-push post-commit; do
  if [ -e "$dest/$h" ] && ! cmp -s "$src/$h" "$dest/$h"; then
    backup="$dest/$h.backup.$(date +%Y%m%d%H%M%S)"
    mv "$dest/$h" "$backup"
    echo "已備份既有 hook → $backup"
  fi
  cp "$src/$h" "$dest/$h"
  chmod +x "$dest/$h"
  echo "已安裝 $h"
done

echo
echo "完成。目標：$root"
echo "review marker：$root/.claude/state/reviewed"
echo "停用方式：rm $dest/pre-push $dest/post-commit"
