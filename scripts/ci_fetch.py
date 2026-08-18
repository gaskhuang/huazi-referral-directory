#!/usr/bin/env python3
"""CI 用的簡報抓取：用 OAuth refresh token 換 access token，直接打 Slides API。

只用標準函式庫，CI 上不需要安裝任何套件，也不需要 gws CLI。
需要三個環境變數（在 GitHub repo secrets 設定）：
    GOOGLE_CLIENT_ID
    GOOGLE_CLIENT_SECRET
    GOOGLE_REFRESH_TOKEN
"""
import json, os, sys, urllib.parse, urllib.request

DECK_ID = "1j9lY9x0Iswm-aR6bdR7NBVLIFX7g100DEz7DNt4hXnw"
TOKEN_URL = "https://oauth2.googleapis.com/token"
API = "https://slides.googleapis.com/v1/presentations/"


def need(name):
    v = os.environ.get(name, "").strip()
    if not v:
        sys.exit(f"✗ 缺少環境變數 {name}（請在 GitHub repo secrets 設定）")
    return v


def access_token():
    body = urllib.parse.urlencode({
        "client_id": need("GOOGLE_CLIENT_ID"),
        "client_secret": need("GOOGLE_CLIENT_SECRET"),
        "refresh_token": need("GOOGLE_REFRESH_TOKEN"),
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=body,
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)["access_token"]
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300]
        sys.exit(f"✗ 換 access token 失敗（HTTP {e.code}）：{detail}\n"
                 f"  refresh token 可能已撤銷，重跑 scripts/get_refresh_token.py 取得新的。")


def main():
    tok = access_token()
    req = urllib.request.Request(API + DECK_ID,
                                 headers={"Authorization": "Bearer " + tok})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            doc = json.load(resp)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300]
        sys.exit(f"✗ 讀取簡報失敗（HTTP {e.code}）：{detail}")

    if "slides" not in doc:
        sys.exit(f"✗ 回應沒有 slides 欄位：{str(doc)[:200]}")

    os.makedirs("data/raw", exist_ok=True)
    with open("data/raw/deck.json", "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False)
    print(f"→ 抓到簡報「{doc.get('title', '').strip()}」，共 {len(doc['slides'])} 頁")


if __name__ == "__main__":
    main()
