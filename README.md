# 📈 LINE Stock Bot

<p align="center">
  <a href="#english">English</a> | <a href="#chinese">繁體中文</a>
</p>

---

<div id="english">

## 🇺🇸 English Version

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Vercel](https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://vercel.com/)
[![LINE](https://img.shields.io/badge/LINE-00C300?style=for-the-badge&logo=line&logoColor=white)](https://developers.line.biz/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)

A minimalist yet powerful **Taiwan Stock Analysis Bot** for LINE. Get real-time stock insights, fundamental analysis, and institutional tracking directly in your chat.



### ✨ Key Features
- **Instant Analysis**: Send a stock ID (e.g., `2330`, `0050`) and get a comprehensive report in seconds.
- **Smart Decision Engine**: Combines fundamental data (Gross Margin, Revenue YoY) with institutional chip tracking (Institutional Buy).
- **Rich UI (Flex Messages)**: Visualized results with color-coded "BUY" or "HOLD" indicators.
- **Customizable Thresholds**: Control strategy parameters via a simple Google Sheet.
- **Cloud-Native**: Deploy once, run forever on Vercel.

### 🛠️ Tech Stack
- **Backend**: FastAPI (Python)
- **Messaging**: LINE Messaging API v3
- **Database/Config**: Google Sheets API
- **Deployment**: Vercel

### 🚀 Getting Started
1. **Environment Variables**: Set `LINE_CHANNEL_SECRET`, `LINE_CHANNEL_ACCESS_TOKEN`, `GOOGLE_CREDENTIALS`, and `SPREADSHEET_ID`.

</div>

---

<div id="chinese">

## 🇹🇼 繁體中文版本

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Vercel](https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://vercel.com/)
[![LINE](https://img.shields.io/badge/LINE-00C300?style=for-the-badge&logo=line&logoColor=white)](https://developers.line.biz/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)

一款極簡且強大的 **台股分析 LINE 機器人**。直接在聊天視窗中獲取即時個股洞察、基本面分析與法人籌碼追蹤。


### ✨ 核心功能
- **即時分析**：輸入股票代號（如 `2330`、`0050`），數秒內即可獲得完整分析報告。
- **智能決策引擎**：結合基本面數據（毛利率、營收年增率）與法人籌碼追蹤（法人買超）。
- **豐富 UI (Flex Messages)**：視覺化分析結果，結合綠色「買進」與橘色「觀望」指示燈。
- **自定義閾值**：可透過 Google 試算表輕易調整策略參數（如毛利率門檻等）。
- **雲端原生**：基於 Vercel 佈署，高可用且低成本。

### 🛠️ 技術棧
- **後端**: FastAPI (Python)
- **通訊**: LINE Messaging API v3
- **數據存儲/設定**: Google Sheets API
- **佈署平台**: Vercel

### 🚀 快速上手
1. **環境變數**：請設定 `LINE_CHANNEL_SECRET`、`LINE_CHANNEL_ACCESS_TOKEN`、`GOOGLE_CREDENTIALS` 與 `SPREADSHEET_ID`。


### 📈 策略邏輯
- **一般個股**：分析 毛利率 > `min_margin`, 營收 YoY > `min_revenue_yoy`, 且 法人買超 > `min_inst_buy`。
- **ETF 系列**：主要專注於法人買超量（ETF 會跳過基本面財報比對）。

</div>

---
*Disclaimer: This bot is for educational purposes only. | 本機器人僅供教育用途。*
