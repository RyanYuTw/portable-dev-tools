#!/usr/bin/env bash
# 檢查目前 git staged 的檔案是否包含常見的敏感檔案樣式。
# exit 0: 安全可繼續 commit； exit 1: 偵測到疑似敏感檔案，需要人工確認。
set -euo pipefail

staged="$(git diff --staged --name-only || true)"

if [ -z "$staged" ]; then
  echo "沒有 staged 檔案可檢查"
  exit 0
fi

hits=()
while IFS= read -r f; do
  [ -z "$f" ] && continue
  base="$(basename "$f")"
  # This scanner is itself named check_secrets.sh; do not flag its filename.
  [ "$base" = "check_secrets.sh" ] && continue
  case "$base" in
    .env|.env.local|.env.production|.env.development|.env.staging|.env.test|*.env)
      hits+=("$f") ;;
    *credential*|*credentials*|*secret*|*secrets*|*password*)
      hits+=("$f") ;;
    id_rsa|id_rsa.pub|id_ed25519|id_ed25519.pub|id_ecdsa|id_dsa)
      hits+=("$f") ;;
    *.pem|*.key|*.pfx|*.p12|*.keystore|*.jks)
      hits+=("$f") ;;
    *service-account*.json|*serviceaccount*.json)
      hits+=("$f") ;;
  esac
done <<< "$staged"

if [ "${#hits[@]}" -gt 0 ]; then
  echo "⚠️  偵測到疑似敏感檔案已被 staged："
  printf '  - %s\n' "${hits[@]}"
  echo ""
  echo "若不應該 commit 這些檔案，執行：git restore --staged <file>"
  exit 1
fi

echo "✅ 未偵測到敏感檔案"
exit 0
