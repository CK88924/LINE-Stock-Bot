# 🤖 大水庫財務助理 LINE Bot --- 系統設計與開發規範 (README)

> 採用 **Domain-Driven Design (DDD)**、**Clean Architecture** 與
> **Google Sheets + NestJS + LINE Messaging API** 建構的 ETF
> 被動收入管理助理。

------------------------------------------------------------------------

# 專案目標

大水庫財務助理是一套協助 ETF
長期投資者管理持股、年度現金流、大水庫進度與投資規劃的 LINE Bot。

核心特色：

-   📈 即時計算大水庫進度
-   💰 推薦每月投資策略
-   📊 自動同步 ETF 股價與配息
-   📅 管理年度固定支出
-   🤖 LINE Quick Reply 一鍵操作
-   🔄 Cron Job 非同步更新市場資料

------------------------------------------------------------------------

# 系統架構

``` text
LINE User
    │
LINE Messaging API
    │
NestJS Webhook
    │
Financial Bot Engine
 ┌──┼───────────────┐
 │  │               │
 ▼  ▼               ▼
Progress Strategy Expense
 │
Google Sheets
 ├──資料庫
 ├──USER_SETTINGS
 ├──MY_HOLDINGS
 └──ANNUAL_EXPENSES
```

------------------------------------------------------------------------

# Google Sheets Domain

## 1. 資料庫（Market Data）

唯一市場資料來源（Single Source of Truth）

  欄位
  -----------------
  Ticker
  Name
  Price
  QuarterDividend
  UpdatedAt

資料僅允許背景排程更新。

------------------------------------------------------------------------

## 2. USER_SETTINGS

  欄位
  -------------------
  UserId
  MonthlySalary
  MonthlyInvestment
  ReservoirTarget
  CurrentETF

------------------------------------------------------------------------

## 3. MY_HOLDINGS

  Ticker   Lots
  -------- ------

僅保存持股，不保存股價與配息。

------------------------------------------------------------------------

## 4. ANNUAL_EXPENSES

  Expense   Month   Amount
  --------- ------- --------

------------------------------------------------------------------------

# Market Scheduler

流程：

``` text
TWSE / MOPS / Finance API
        │
        ▼
NestJS Cron
        │
Crawler
        │
Google Sheets
```

查詢時：

``` text
LINE Query
     │
Financial Engine
     │
Google Sheets
     │
立即回覆
```

------------------------------------------------------------------------

# LINE Router

``` ts
switch(message){

case "目前進度":
    return progress();

case "推進建議":
    return strategy();

case "開銷檢查":
    return expense();

default:
    return menu();
}
```

------------------------------------------------------------------------

# Financial Engine

    Financial Engine
    │
    ├── Progress Service
    ├── Strategy Service
    └── Expense Service

## Progress

MY_HOLDINGS + 資料庫

輸出：

-   年配息
-   達標率
-   距離目標

## Strategy

USER_SETTINGS + 資料庫

輸出：

-   本月可買
-   下張差額
-   達標預估

## Expense

ANNUAL_EXPENSES

輸出：

-   本月支出
-   年度支出
-   三個月提醒

------------------------------------------------------------------------

# Quick Reply

-   📊 目前進度
-   💡 推進建議
-   📅 開銷檢查

------------------------------------------------------------------------

# 設計原則

-   Domain Driven Design
-   Clean Architecture
-   Single Source of Truth
-   Read / Write Separation
-   Service Layer
-   Repository Pattern
-   非同步資料同步
-   Google Sheets 作為輕量資料庫
