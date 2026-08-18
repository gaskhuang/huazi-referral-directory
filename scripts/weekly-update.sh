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

for cmd in gws python3 git; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "✗ 找不到 $cmd，中止"
    exit 1
  fi
done

echo "→ 1/4 抓取簡報"
./scripts/fetch.sh

echo "→ 2/4 攤平版面"
python3 scripts/extract.py

echo "→ 3/4 解析成員"
python3 scripts/parse.py

echo "→ 4/4 產出網站資料"
python3 scripts/build.py

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
