#!/usr/bin/env bash
# 把本目錄的 plugin 內容同步進 Codex。
#
# Codex 的 plugin 快取是「版本鎖定的快照」而非活連結：改了檔案但沒動版本號，
# codex plugin add 會沿用舊快照，而且不會報錯。本腳本一次做完提版本與重裝，
# 並在最後驗證快取真的變了，避免靜默使用舊版。
#
# 用法：
#   scripts/sync-codex.sh              # 修訂號 +1（0.6.1 → 0.6.2）
#   scripts/sync-codex.sh 0.7.0        # 指定版本
#   MARKETPLACE=personal scripts/sync-codex.sh
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
manifest="$root/.codex-plugin/plugin.json"
marketplace="${MARKETPLACE:-personal}"

[ -f "$manifest" ] || { echo "錯誤：找不到 $manifest" >&2; exit 1; }
command -v codex >/dev/null || { echo "錯誤：找不到 codex 指令" >&2; exit 1; }

plugin=$(python3 -c "import json;print(json.load(open('$manifest'))['name'])")

# ── 提版本 ───────────────────────────────────────────────
new_version=$(python3 - "$manifest" "${1:-}" <<'PY'
import json, sys, datetime
path, explicit = sys.argv[1], sys.argv[2]
data = json.load(open(path, encoding="utf-8"))
base = (explicit or data.get("version", "0.0.0")).split("+")[0]
if not explicit:
    parts = base.split(".")
    while len(parts) < 3:
        parts.append("0")
    parts[2] = str(int(parts[2]) + 1)
    base = ".".join(parts)
data["version"] = f"{base}+codex.{datetime.datetime.now():%Y%m%d%H%M%S}"
with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
    f.write("\n")
print(data["version"])
PY
)
echo "版本 → $new_version"

# ── 重裝 ─────────────────────────────────────────────────
codex plugin add "${plugin}@${marketplace}" >/dev/null
cache="$HOME/.codex/plugins/cache/${marketplace}/${plugin}/${new_version}"
echo "已安裝 → $cache"

# ── 驗證快取真的是新的 ──────────────────────────────────
[ -d "$cache" ] || { echo "錯誤：預期的快取目錄不存在，Codex 可能沿用了舊快照" >&2; exit 1; }

fail=0
for dir in skills hooks scripts; do
  [ -d "$root/$dir" ] || continue
  src=$(find "$root/$dir" -type f | wc -l | tr -d ' ')
  dst=$(find "$cache/$dir" -type f 2>/dev/null | wc -l | tr -d ' ')
  if [ "$src" = "$dst" ]; then
    printf '  %-8s %s 個檔案 ✓\n' "$dir" "$src"
  else
    printf '  %-8s 來源 %s vs 快取 %s ✗\n' "$dir" "$src" "$dst"; fail=1
  fi
done

if ! diff -r -q "$root/skills" "$cache/skills" >/dev/null 2>&1; then
  echo "  skills 內容與來源不符 ✗" >&2; fail=1
fi

[ "$fail" = 0 ] || { echo "同步驗證失敗" >&2; exit 1; }

echo
echo "同步完成。記得提交 .codex-plugin/plugin.json 的版本變更。"
