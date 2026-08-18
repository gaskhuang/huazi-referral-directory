# 華資 三層引薦名冊

BNI 華資分會的成員名冊網站，把每位夥伴簡報裡的**一般引薦 / 理想引薦 / 夢幻引薦**攤在同一頁，
搭配搜尋與小組篩選，會前一分鐘就能找到今天該幫誰、該找誰。

資料來源是分會的「2026年 華資45秒會員簡報」，由腳本自動解析，沒有人工改寫內容。

## 每週更新

簡報改完之後跑這一串就好：

```bash
./scripts/fetch.sh && python3 scripts/extract.py && python3 scripts/parse.py && python3 scripts/build.py
```

需要先安裝並登入 [`gws`](https://github.com/) CLI（Google Workspace CLI）。

跑完 `git add -A && git commit && git push`，GitHub Pages 會自動重新部署。

## 目錄結構

```
docs/              # 網站本體（GitHub Pages 直接吃這個資料夾）
  index.html
  assets/styles.css
  assets/app.js
  data/members.js  # 由 scripts/build.py 產生
scripts/
  fetch.sh         # 從 Google Slides 抓簡報 → data/raw/deck.json
  extract.py       # 攤平版面座標與文字 → data/slides.json
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
