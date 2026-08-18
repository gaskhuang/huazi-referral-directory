# 華資 三層引薦名冊

BNI 華資分會的成員名冊網站，把每位夥伴簡報裡的**一般引薦 / 理想引薦 / 夢幻引薦**攤在同一頁，
搭配搜尋與小組篩選，會前一分鐘就能找到今天該幫誰、該找誰。

資料來源是分會的「2026年 華資45秒會員簡報」，由腳本自動解析，沒有人工改寫內容。

## 每週更新

簡報改完之後跑這一串就好：

```bash
./scripts/weekly-update.sh
```

會抓最新簡報、重新解析、內容有變動才 commit 並 push，GitHub Pages 隨後自動重新部署。
不需要登入任何帳號。

## 目錄結構

```
docs/              # 網站本體（GitHub Pages 直接吃這個資料夾）
  index.html
  assets/styles.css
  assets/app.js
  data/members.js  # 由 scripts/build.py 產生
scripts/
  fetch_public.py  # 從公開匯出下載 pptx 並攤平版面 → data/slides.json（免憑證）
  weekly-update.sh # 本機一鍵更新：抓 → 解析 → 產出 → push
  fetch.sh         # 舊路線：透過 gws 走 Slides API（需登入，已非主要路徑）
  extract.py       # 舊路線：攤平 Slides API 的 JSON
  parse.py         # 解析成員欄位 → data/members.json、data/intros.json
  build.py         # 打包成網站資料 → docs/data/members.js
```

## 資料來源

原始簡報（原生 Google Slides，每週更新的就是這一份）：

<https://docs.google.com/presentation/d/1j9lY9x0Iswm-aR6bdR7NBVLIFX7g100DEz7DNt4hXnw/edit>

## 解析邏輯說明

整份簡報是 61 頁的單一檔案，內容混了三種頁面，`parse.py` 依這些特徵分流：

| 頁面類型 | 判斷方式 | 數量 |
|---|---|---|
| 分組隔頁 | 整頁只有一個文字框、內容含「華資【…組】」 | 5 |
| 小組介紹頁 | 沒有「三層引薦」這個標籤 | 8 |
| 純圖片頁 | 完全沒有文字框 | 5 |
| 成員頁 | 其餘 | 43 |

成員頁的欄位用「版面座標 + 標籤錨點」判斷：

- **姓名列**：頭部區含中文姓名的框，有編號的優先；都沒編號時取較下方那個（公司行永遠在姓名之上）
- **三層引薦**：先找含「一般引薦」的框，找不到再退回左下區塊面積最大的框
- **本週我有 / 我要**：以標籤開頭比對，標籤框內沒內容時往正下方找最近的框
- **我的專業**：姓名列下方、三層引薦區之上的所有非標籤框
- **專業標籤**：抓 `#` 開頭的 hashtag，簡報裡不少人用它標專長

重複頁（同一位夥伴放了兩張內容相同的投影片）會依三層引薦內容自動去除，實際輸出 41 位。

簡報裡本來就空白的欄位，網站上顯示「尚未填寫」，不會補字。

## 已知的資料缺口

這些是簡報本身就缺的，不是解析錯誤：

- 黃俊凱、張崇德、林威呈、劉晉誠 — 簡報上沒有寫編號
- 黃建凱 — 沒有公司／職稱那一行
- 丁禹勝 — 沒有專業別，也沒有 hashtag 可以遞補
- 工廠數位轉型組、工程組 — 沒有「目標客戶 / 補強專業別」那幾頁（他們的介紹頁是圖片）

## 每週自動更新（GitHub Actions）

排程：**台灣時間每週四 02:00**（workflow 裡是 UTC 週三 18:00）。
定義在 [.github/workflows/weekly-update.yml](.github/workflows/weekly-update.yml)。

**不需要任何憑證。** 簡報的共用設定是「知道連結的人都能存取」，所以 Google 的
匯出端點不帶 token 就能下載：

```
https://docs.google.com/presentation/d/<ID>/export/pptx
```

CI 下載這份 pptx，用 python-pptx 讀版面座標，後面照舊跑 parse → build。
簡報內容沒變動時不會產生空提交。

> 注意：這條路完全依賴簡報維持「知道連結的人都能存取」。
> 哪天改成僅限特定人員，workflow 會下載到一個很小的 HTML 錯誤頁而中止（腳本有擋），
> 那時就得改回 OAuth 憑證的做法。

### 本機手動更新

```bash
./scripts/weekly-update.sh
```

跟 CI 走完全同一條路（公開匯出 + python-pptx），一樣不需要登入。
第一次執行會自動建 `.venv` 並裝好 python-pptx。

### 兩個要知道的限制

- GitHub 的排程在整點負載高時可能延遲數分鐘到一小時，不是準點觸發。
- **repo 連續 60 天沒有任何 commit，GitHub 會自動停用排程**。這個 repo 每週都會被 workflow 自己推一版，正常情況不會踩到；但如果簡報連兩個月都沒改，就不會有提交，那時要回 Actions 頁面手動啟用。
