import asyncio
from core.repositories.sheets_db import (
    get_my_holdings,
    get_stock_db_data,
    get_financial_user_settings,
    fetch_dividend_past_year
)
from core.services.strategy_service import analyze_and_decide

async def calculate_progress() -> dict:
    """
    計算目前投資進度：
    1. 取得持股資料 (MY_HOLDINGS)
    2. 取得資料庫股價，若缺失則自動呼叫分析補足
    3. 取得財務設定 (USER_SETTINGS)
    4. 非同步向 FinMind API 抓取過去一年的總配息
    5. 計算總年配息、達標率、距離目標額
    """
    holdings = await get_my_holdings()
    db_data = await get_stock_db_data()
    user_settings = await get_financial_user_settings()
    
    target_dividend = float(user_settings.get("TARGET_ANNUAL_DIVIDEND", 0.0))
    
    # 檢查是否有任何持股在資料庫中無股價，有的話執行即時爬取與更新
    missing_tasks = []
    for h in holdings:
        ticker = h["ticker"]
        if ticker not in db_data or db_data[ticker].get("price", 0.0) == 0.0:
            missing_tasks.append(analyze_and_decide(ticker))
            
    if missing_tasks:
        await asyncio.gather(*missing_tasks, return_exceptions=True)
        # 重新讀取最新的資料庫資料
        db_data = await get_stock_db_data()
        
    # 非同步併發讀取配息資訊
    div_tasks = [fetch_dividend_past_year(h["ticker"]) for h in holdings]
    div_results = await asyncio.gather(*div_tasks, return_exceptions=True)
    
    total_annual_dividend = 0.0
    holdings_breakdown = []
    
    for i, h in enumerate(holdings):
        ticker = h["ticker"]
        shares = h["shares"]
        
        div_per_share = div_results[i] if not isinstance(div_results[i], Exception) else 0.0
        annual_dividend = div_per_share * shares
        total_annual_dividend += annual_dividend
        
        price = db_data.get(ticker, {}).get("price", 0.0)
        market_val = price * shares
        
        holdings_breakdown.append({
            "ticker": ticker,
            "shares": shares,
            "price": price,
            "market_val": market_val,
            "dividend_per_share": div_per_share,
            "annual_dividend": annual_dividend
        })
        
    achievement_rate = (total_annual_dividend / target_dividend * 100) if target_dividend > 0 else 0.0
    distance_to_target = max(0.0, target_dividend - total_annual_dividend)
    
    return {
        "holdings": holdings_breakdown,
        "total_annual_dividend": total_annual_dividend,
        "target_annual_dividend": target_dividend,
        "achievement_rate": achievement_rate,
        "distance_to_target": distance_to_target
    }
