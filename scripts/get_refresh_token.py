#!/usr/bin/env python3
"""在本機跑一次 Google OAuth，把 GitHub Actions 要用的憑證直接設進 repo secrets。

這支只在你自己的電腦上跑。預設會用 gh CLI 把三個值直接送進 GitHub，
token 不會顯示在畫面上、也不用複製貼上。

用法：
    python3 scripts/get_refresh_token.py            # 授權後直接設定 secrets
    python3 scripts/get_refresh_token.py --print    # 只印出來，自己手動設
"""
import http.server, json, os, secrets, shutil, subprocess, sys, threading
import urllib.parse, urllib.request, webbrowser

REPO = "gaskhuang/huazi-referral-directory"

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

    values = {
        "GOOGLE_CLIENT_ID": cid,
        "GOOGLE_CLIENT_SECRET": csec,
        "GOOGLE_REFRESH_TOKEN": rt,
    }

    if "--print" in sys.argv:
        print("=" * 60)
        print("以下三個值請自行設成 GitHub repo secrets，設完把畫面清掉：\n")
        for k, v in values.items():
            print(f"{k} = {v}")
        print("=" * 60)
        return

    if not shutil.which("gh"):
        sys.exit("✗ 找不到 gh CLI。改用 --print 自己設，或先安裝 gh。")

    print("\n→ 用 gh 把三個值設進 GitHub repo secrets（不會顯示在畫面上）")
    for k, v in values.items():
        try:
            subprocess.run(["gh", "secret", "set", k, "--repo", REPO],
                           input=v, text=True, check=True,
                           stdout=subprocess.DEVNULL)
            print(f"   ✓ {k}")
        except subprocess.CalledProcessError as e:
            sys.exit(f"✗ 設定 {k} 失敗（gh 回傳 {e.returncode}）")

    print("\n→ 立刻觸發一次 workflow 驗證")
    try:
        subprocess.run(["gh", "workflow", "run", "weekly-update.yml", "--repo", REPO],
                       check=True, stdout=subprocess.DEVNULL)
        print("   ✓ 已觸發，看執行結果：")
        print(f"   gh run watch --repo {REPO}")
        print(f"   或 https://github.com/{REPO}/actions")
    except subprocess.CalledProcessError:
        print("   ! 自動觸發失敗，到 Actions 頁面手動按 Run workflow 即可")


if __name__ == "__main__":
    main()
