#!/bin/zsh
# 從 Google Slides 抓下華資 45 秒會員簡報（需要 gws CLI 已登入）
set -e
cd "$(dirname "$0")/.."
DECK_ID="1j9lY9x0Iswm-aR6bdR7NBVLIFX7g100DEz7DNt4hXnw"
mkdir -p data/raw
echo "→ 抓取簡報 $DECK_ID"
gws slides presentations get --params "{\"presentationId\":\"$DECK_ID\"}" 2>/dev/null > data/raw/deck.json
python3 - <<'PY'
import json
d=json.load(open('data/raw/deck.json',encoding='utf-8'))
if 'slides' not in d:
    raise SystemExit(f"抓取失敗：{d}")
print(f"→ 完成，{len(d['slides'])} 頁")
PY
