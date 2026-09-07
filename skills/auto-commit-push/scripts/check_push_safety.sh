#!/usr/bin/env bash
# 檢查目前分支是否適合自動 push。
# exit 0: 安全可繼續 push； exit 1: 偵測到 main/master 或分支落後 remote，需要人工確認。
set -euo pipefail

branch="$(git rev-parse --abbrev-ref HEAD)"

if [ "$branch" = "main" ] || [ "$branch" = "master" ]; then
  echo "⚠️  目前分支是 $branch，不會自動 push。"
  echo "若真的要 push 到 $branch，請手動確認後自行執行 git push。"
  exit 1
fi

upstream="$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)"

if [ -z "$upstream" ]; then
  echo "✅ 分支 $branch 尚未設定 upstream，將以 git push -u origin $branch 建立"
  exit 0
fi

remote_name="${upstream%%/*}"
remote_branch="${upstream#*/}"
git fetch --quiet "$remote_name" "$remote_branch" 2>/dev/null || git fetch --quiet "$remote_name" || true

counts="$(git rev-list --left-right --count "HEAD...$upstream" 2>/dev/null || echo "0 0")"
ahead="$(echo "$counts" | awk '{print $1}')"
behind="$(echo "$counts" | awk '{print $2}')"

if [ "${behind:-0}" -gt 0 ]; then
  echo "⚠️  本地分支落後 remote $behind 個 commit（已分歧），直接 push 會被拒絕或需要 force push。"
  echo "請先跟使用者確認要用 rebase 還是 merge 同步，不要自動處理。"
  exit 1
fi

echo "✅ 分支 $branch 領先 remote $ahead 個 commit，沒有落後，可以安全 push"
exit 0
