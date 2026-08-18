#!/bin/zsh
# 每週更新：重抓簡報 → 解析 → 產出網站資料 → 有變動才 commit & push
# 手動執行：./scripts/weekly-update.sh
set -euo pipefail

cd "$(dirname "$0")/.."
REPO="$(pwd)"
LOG_DIR="$REPO/logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/update-$(date +%Y%m%d-%H%M%S).log"

exec > >(tee -a "$LOG") 2>&1

echo "=========================================="
echo "華資名冊更新  $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

# launchd 的 PATH 很乾淨，把常用位置補回去
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.npm-global/bin:$PATH"

if ! command -v git >/dev/null 2>&1; then
  echo "✗ 找不到 git，中止"
  exit 1
fi

# 解析 pptx 需要 python-pptx；本機用專案 venv，沒有就建一個
PY_BIN="$REPO/.venv/bin/python"
if [[ ! -x "$PY_BIN" ]]; then
  echo "→ 建立 .venv 並安裝 python-pptx"
  python3 -m venv "$REPO/.venv"
  "$REPO/.venv/bin/pip" install --quiet python-pptx
fi
if ! "$PY_BIN" -c "import pptx" 2>/dev/null; then
  "$REPO/.venv/bin/pip" install --quiet python-pptx
fi

echo "→ 1/3 抓取簡報並攤平版面"
"$PY_BIN" scripts/fetch_public.py

echo "→ 2/3 解析成員"
"$PY_BIN" scripts/parse.py

echo "→ 3/3 產出網站資料"
"$PY_BIN" scripts/build.py

if git diff --quiet -- docs/data/members.js data/members.json; then
  echo "✓ 簡報內容沒有變動，不需要更新網站"
  exit 0
fi

echo "→ 內容有變動，推上 GitHub"
git add -A -- docs data
git -c user.name="gaskhuang" -c user.email="gskgino@gmail.com" \
    commit -q -m "每週更新：同步 $(date '+%Y-%m-%d') 版簡報"
git push -q origin main

echo "✓ 已推送，GitHub Pages 幾分鐘後會重新部署"
echo "   https://gaskhuang.github.io/huazi-referral-directory/"

# 只留最近 12 份日誌
ls -1t "$LOG_DIR"/update-*.log 2>/dev/null | tail -n +13 | xargs rm -f 2>/dev/null || true
