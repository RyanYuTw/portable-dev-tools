#!/usr/bin/env bash
# 安裝這個 plugin 儲存庫自己用的 git hooks（與 install-git-hooks.sh 不同，
# 後者是安裝給「使用本 plugin 的專案」）。
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
dest="$root/.git/hooks"
mkdir -p "$dest"

cp "$root/hooks/pre-push-codex-sync" "$dest/pre-push"
chmod +x "$dest/pre-push"
echo "已安裝 pre-push → $dest/pre-push"
echo "作用：推送前確認 Codex 快取已與工作目錄一致"
