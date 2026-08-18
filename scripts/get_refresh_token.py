#!/usr/bin/env python3
"""在本機跑一次 Google OAuth，取得 GitHub Actions 要用的 refresh token。

這支只在你自己的電腦上跑，token 直接印在你的終端機，不會傳給任何人。
沿用 gws 已經有的 OAuth client（~/.config/gws/client_secret.json）。

用法：
    python3 scripts/get_refresh_token.py
"""
import http.server, json, os, secrets, sys, threading, urllib.parse, urllib.request, webbrowser

CLIENT_FILE = os.path.expanduser("~/.config/gws/client_secret.json")
SCOPE = "https://www.googleapis.com/auth/presentations.readonly"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
PORT = 8765
REDIRECT = f"http://localhost:{PORT}/"

result = {}


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        result.update({k: v[0] for k, v in q.items()})
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        ok = "code" in result
        self.wfile.write(("<h2>" + ("授權完成，回到終端機看 refresh token。"
                                    if ok else "授權失敗，回終端機看訊息。") +
                          "</h2>").encode())

    def log_message(self, *a):
        pass


def main():
    if not os.path.exists(CLIENT_FILE):
        sys.exit(f"✗ 找不到 {CLIENT_FILE}\n"
                 f"  這支腳本沿用 gws 的 OAuth client，請先確認 gws 已設定完成。")

    conf = json.load(open(CLIENT_FILE))["installed"]
    cid, csec = conf["client_id"], conf["client_secret"]
    state = secrets.token_urlsafe(16)

    params = urllib.parse.urlencode({
        "client_id": cid, "redirect_uri": REDIRECT, "response_type": "code",
        "scope": SCOPE, "access_type": "offline", "prompt": "consent", "state": state,
    })
    url = f"{AUTH_URL}?{params}"

    srv = http.server.HTTPServer(("localhost", PORT), Handler)
    threading.Thread(target=srv.handle_request, daemon=True).start()

    print("→ 開啟瀏覽器完成授權；若沒自動開，手動貼上這個網址：\n")
    print(url + "\n")
    try:
        webbrowser.open(url)
    except Exception:
        pass

    for _ in range(600):
        if result:
            break
        import time
        time.sleep(0.5)

    if result.get("state") != state:
        sys.exit("✗ state 不符，可能被攔截，請重跑一次。")
    if "code" not in result:
        sys.exit(f"✗ 沒拿到授權碼：{result}")

    body = urllib.parse.urlencode({
        "code": result["code"], "client_id": cid, "client_secret": csec,
        "redirect_uri": REDIRECT, "grant_type": "authorization_code",
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=body,
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        tok = json.load(resp)

    rt = tok.get("refresh_token")
    if not rt:
        sys.exit("✗ Google 沒有回 refresh_token，請到帳戶權限頁移除此應用後重跑。")

    print("=" * 60)
    print("以下三個值要設成 GitHub repo secrets（貼進去之後就把畫面清掉）：\n")
    print(f"GOOGLE_CLIENT_ID     = {cid}")
    print(f"GOOGLE_CLIENT_SECRET = {csec}")
    print(f"GOOGLE_REFRESH_TOKEN = {rt}")
    print("\n或直接用 gh 逐一設定（會提示你貼上值）：")
    print("  gh secret set GOOGLE_CLIENT_ID     --repo gaskhuang/huazi-referral-directory")
    print("  gh secret set GOOGLE_CLIENT_SECRET --repo gaskhuang/huazi-referral-directory")
    print("  gh secret set GOOGLE_REFRESH_TOKEN --repo gaskhuang/huazi-referral-directory")
    print("=" * 60)


if __name__ == "__main__":
    main()
