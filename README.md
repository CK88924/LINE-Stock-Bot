# 🤖 LINE ETF & 大水庫財務助理 Bot (LINE Stock Bot)

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Vercel](https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://vercel.com/)
[![LINE](https://img.shields.io/badge/LINE-00C300?style=for-the-badge&logo=line&logoColor=white)](https://developers.line.biz/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)

整合**台股基本面分析**與 **ETF 被動收入（大水庫）管理** 的智慧型 LINE 機器人。本機器人結合了個股籌碼分析與個人長期財務規劃，可透過 Google Sheets 進行輕量級資料管理與參數自訂。

---

## 🚀 核心特色與功能

### 1. 個股/ETF 即時分析（大眾功能）
- 輸入股票或 ETF 代號（如 `2330`、`00919`），數秒內自動完成多重指標檢查：
  - **一般個股**：比對毛利率、營收 YoY 與三大法人買超量。
  - **ETF 系列**：專注於三大法人籌碼買超量，跳過財報基本面檢查。
- 分析結果以綠色「買進 (BUY)」與橘色「觀望 (HOLD)」進行視覺化 Flex Message 呈現。

### 2. 大水庫被動收入管理（授權用戶專屬）
- 📈 **目前進度**：串接 FinMind API 抓取過去 365 天配息歷史，計算預估年配息額、大水庫目標達標率、與目標差額。
- 💡 **推進建議**：依據每月預算與焦點推進標的，計算推進 1 張的預算差額，並推算達成大水庫目標所需的額外股數、投入資金與預估達標時間。
- 📅 **開銷檢查**：自動對照當月（台灣時間）固定支出，並預警未來三個月內即將扣繳的年度開銷項目。
- 🤖 **Quick Reply 鍵盤**：授權用戶專屬的滑動式快捷按鈕，一鍵輕鬆查詢。

---

## 🛠️ 系統架構

```text
LINE User (大眾 / 授權用戶)
    │
LINE Messaging API
    │
FastAPI Webhook (Vercel)
    │
Financial Bot Engine
 ┌──┴───────────────┐
 ▼                  ▼
[一般個股/ETF查詢]    [大水庫財務助理]
                     ├── Progress Service (進度)
                     ├── Strategy Service (建議)
                     └── Expense Service  (開銷)
                            │
                      Google Sheets 試算表
```

---

## 📊 Google Sheets 結構設計

本機器人以您指定的 Google Sheets 作為資料存儲核心，工作表與欄位規格如下：

### 1. `資料庫` (Market Data)
保存個股/ETF 的最新行情數據與分析結果（僅允許程式背景/Webhook 寫入）：
- `股票代號`、`分析時間`、`最新股價`、`成交量`、`毛利率(%)`、`營收YoY(%)`、`三大法人買超`、`結算決策`

### 2. `設定` (Analysis Thresholds)
自訂個股與籌碼篩選的指標門檻：
- `MIN_MARGIN_PERCENT`（最低毛利率，預設 10.0%）
- `MIN_REVENUE_YOY`（最低營收年增率，預設 0.0%）
- `MIN_INSTITUTIONAL_BUY`（最低法人買超量，預設 300 張）

### 3. `USER_SETTINGS` (財務規劃)
大水庫計劃的核心財務設定：
- `MONTHLY_SALARY`（每月薪資/可投資預算，例如 28480）
- `TARGET_ANNUAL_DIVIDEND`（大水庫年度配息目標，例如 120000）
- `STRATEGY_FOCUS_TICKER`（本月推進焦點 ETF，例如 00919）

### 4. `MY_HOLDINGS` (目前持股)
記錄您目前持有的 ETF 庫存（不保存股價，由程式自動比對動態計算）：
- `Ticker`（股票代號）、`Shares`（持有股數）

### 5. `工作表5` (年度固定開銷)
記錄全年度預計扣繳的固定生活或訂閱費用：
- `Item`（項目名稱）、`Cost`（金額）、`Month`（扣繳月份，1-12 數字）

---

## 🛡️ 權限與路由設計

為確保一般大眾查股時不受干擾，機器人對 LINE User ID 進行了權限分流：
- **一般用戶**：僅支援輸入 4~6 碼股票代號，回傳標準分析圖卡（**不附帶任何 Quick Reply 選單**）。輸入其他文字時機器人會保持靜默。
- **專屬授權用戶 (`U738dee194d7cd3baeb028a83ee75e7bf`)**：
  - 開啟專屬 Quick Reply 快捷按鈕。
  - 支援 `目前進度`、`推進建議`、`開銷檢查` 指令。
  - 輸入無效代號時，回傳 ETF 財務助理歡迎導覽選單。

---

## ⚙️ 快速上手與部署

1. **環境變數設定** (在 Vercel 或是本地 `.env` 檔案中設定)：
   - `LINE_CHANNEL_SECRET`：LINE 頻道密鑰。
   - `LINE_CHANNEL_ACCESS_TOKEN`：LINE 頻道存取權杖。
   - `SPREADSHEET_ID`：Google 試算表的 ID。
   - `GOOGLE_CREDENTIALS`：Google 服務帳戶的認證金鑰 JSON 字串。

2. **LINE Developers 後台設定**：
   - 開啟 **`Use webhook`** 功能。
   - 將 Webhook URL 設定為您 Vercel 部署的網址（如 `https://your-app.vercel.app/api/index.py`）。

3. **LINE OA Manager 後台設定**：
   - 將回應模式設定為 **`聊天機器人`**，開啟 **`Webhook`**，並停用 **`自動回應訊息`**（避免罐頭訊息干擾）。

---
*本機器人僅供投資規劃與學術研究用途，不構成任何實際投資建議。*
