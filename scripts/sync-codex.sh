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
#   scripts/sync-codex.sh --check      # 只驗證目前快取，不提版本也不安裝
#   MARKETPLACE=personal scripts/sync-codex.sh
#
# 版本會同時寫進 .codex-plugin/plugin.json（帶 +codex.<timestamp> 建置識別）
# 與 .claude-plugin 的 plugin.json / marketplace.json（只放基底版本）。
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
manifest="$root/.codex-plugin/plugin.json"
marketplace="${MARKETPLACE:-personal}"

[ -f "$manifest" ] || { echo "錯誤：找不到 $manifest" >&2; exit 1; }
command -v codex >/dev/null || { echo "錯誤：找不到 codex 指令" >&2; exit 1; }

plugin=$(python3 -c "import json;print(json.load(open('$manifest'))['name'])")

# ── --check：只驗證，不提版本也不安裝 ────────────────────
if [ "${1:-}" = "--check" ]; then
  # 三個 manifest 的基底版本必須一致。手動改了其中一個而忘了另外兩個時，
  # Claude Code 與 Codex 會回報不同版本，而全樹比對抓不到這種內部不一致。
  version_drift=$(python3 - "$root" <<'PY'
import json, os, sys
root = sys.argv[1]
found = {}
codex = os.path.join(root, ".codex-plugin", "plugin.json")
if os.path.exists(codex):
    found[".codex-plugin/plugin.json"] = json.load(
        open(codex, encoding="utf-8")).get("version", "").split("+")[0]
cp = os.path.join(root, ".claude-plugin", "plugin.json")
if os.path.exists(cp):
    found[".claude-plugin/plugin.json"] = json.load(
        open(cp, encoding="utf-8")).get("version", "")
mp = os.path.join(root, ".claude-plugin", "marketplace.json")
if os.path.exists(mp):
    d = json.load(open(mp, encoding="utf-8"))
    if "version" in d.get("metadata", {}):
        found["marketplace.json metadata"] = d["metadata"]["version"]
    for i, e in enumerate(d.get("plugins", [])):
        if "version" in e:
            found["marketplace.json plugins[%d]" % i] = e["version"]
if len(set(found.values())) > 1:
    for k, v in found.items():
        print("  %-34s %s" % (k, v))
PY
)
  if [ -n "$version_drift" ]; then
    echo "manifest 版本不一致：" >&2
    printf '%s\n' "$version_drift" >&2
    echo >&2
    echo "請執行 scripts/sync-codex.sh 讓三個 manifest 對齊。" >&2
    exit 1
  fi

  cache=$(ls -d "$HOME/.codex/plugins/cache/${marketplace}/${plugin}"/*/ 2>/dev/null | sort -V | tail -1)
  if [ -z "$cache" ]; then
    echo "Codex 尚未安裝此 plugin。請執行 scripts/sync-codex.sh" >&2
    exit 1
  fi
  cache="${cache%/}"
  drift=$(diff -r -q \
    -x '.git' -x 'node_modules' -x '__pycache__' -x '.DS_Store' -x '*.pyc' -x 'venv' -x '.venv' \
    "$root" "$cache" 2>&1) || true
  if [ -n "$drift" ]; then
    echo "Codex 快取落後於工作目錄：" >&2
    printf '%s\n' "$drift" | sed 's/^/  /' >&2
    echo >&2
    echo "請先執行 scripts/sync-codex.sh 再推送。" >&2
    exit 1
  fi
  echo "Codex 快取與來源一致（$(basename "$cache")）✓"
  exit 0
fi

# ── 提版本 ───────────────────────────────────────────────
# 必須在重裝之前就把 .claude-plugin 一起更新——快照是整個目錄的複本，
# 晚一步寫入的話快照裡的 .claude-plugin 會落後，下面的全樹比對就會失敗。
new_version=$(python3 - "$root" "${1:-}" <<'PY'
import json, os, sys, datetime

root, explicit = sys.argv[1], sys.argv[2]

def save(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")

codex_manifest = os.path.join(root, ".codex-plugin", "plugin.json")
data = json.load(open(codex_manifest, encoding="utf-8"))
base = (explicit or data.get("version", "0.0.0")).split("+")[0]
if not explicit:
    parts = base.split(".")
    while len(parts) < 3:
        parts.append("0")
    parts[2] = str(int(parts[2]) + 1)
    base = ".".join(parts)

# Codex 需要每次都是新的版本字串，否則會沿用舊快照。
data["version"] = f"{base}+codex.{datetime.datetime.now():%Y%m%d%H%M%S}"
save(codex_manifest, data)

# Claude Code 端只放基底版本，不帶建置識別。只覆寫既有欄位，不新增。
plugin_json = os.path.join(root, ".claude-plugin", "plugin.json")
if os.path.exists(plugin_json):
    d = json.load(open(plugin_json, encoding="utf-8"))
    if "version" in d:
        d["version"] = base
        save(plugin_json, d)

marketplace_json = os.path.join(root, ".claude-plugin", "marketplace.json")
if os.path.exists(marketplace_json):
    d = json.load(open(marketplace_json, encoding="utf-8"))
    touched = False
    if "version" in d.get("metadata", {}):
        d["metadata"]["version"] = base
        touched = True
    for entry in d.get("plugins", []):
        if "version" in entry:
            entry["version"] = base
            touched = True
    if touched:
        save(marketplace_json, d)

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

# 比對整棵樹，不是只比 skills——曾經發生過 README 落後一版而驗證仍回報成功。
# 排除的都是不隨 plugin 發佈的雜訊。
diff_output=$(diff -r -q \
  -x '.git' -x 'node_modules' -x '__pycache__' -x '.DS_Store' -x '*.pyc' -x 'venv' -x '.venv' \
  "$root" "$cache" 2>&1) || true

if [ -n "$diff_output" ]; then
  echo "快取與來源不一致：" >&2
  printf '%s\n' "$diff_output" | sed 's/^/  /' >&2
  echo "同步驗證失敗" >&2
  exit 1
fi

for dir in skills hooks scripts; do
  [ -d "$root/$dir" ] || continue
  printf '  %-8s %s 個檔案 ✓\n' "$dir" "$(find "$root/$dir" -type f | wc -l | tr -d ' ')"
done
printf '  %-8s 全樹比對通過 ✓\n' "整體"

echo
echo "同步完成。記得提交版本變更：.codex-plugin/plugin.json 與 .claude-plugin/。"
