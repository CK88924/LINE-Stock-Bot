import asyncio
from datetime import datetime, timezone, timedelta
from core.repositories.stock_fetcher import fetch_stock_info
from core.repositories.sheets_db import get_user_settings, upsert_stock_data

async def analyze_and_decide(stock_id: str) -> dict:
    """
    核心大腦：非同步併發抓取資料與試算表設定，並進行策略比對
    """
    stock_task = fetch_stock_info(stock_id)
    settings_task = get_user_settings()
    
    results = await asyncio.gather(stock_task, settings_task, return_exceptions=True)
    stock_data = results[0] if not isinstance(results[0], Exception) else {}
    user_settings = results[1] if not isinstance(results[1], Exception) else {}
    
    if not stock_data:
        return {"error": True, "message": f"查無代號 {stock_id}，請確認是否輸入完整的台股代號（如 0050、2330）。"}
        
    min_margin = float(user_settings.get("MIN_MARGIN_PERCENT", 30.0))
    min_revenue_yoy = float(user_settings.get("MIN_REVENUE_YOY", 5.0))
    # Institutional Buy 本意即為三大法人，這裡我們繼續沿用此變數名稱
    min_inst_buy = int(user_settings.get("MIN_INSTITUTIONAL_BUY", 1000))
    
    price = stock_data.get("price", 0.0)
    vol = stock_data.get("volume", 0)
    margin = stock_data.get("gross_margin", 0.0)
    rev_yoy = stock_data.get("revenue_yoy", 0.0)
    inst_buy = stock_data.get("institutional_buy", 0)
    
    is_etf = stock_id.startswith("00")
    
    decision = "買進 (BUY)"
    reasons = []
    
    if is_etf:
        # 💡 修正：將輸出的文字改為「三大法人買超」
        if inst_buy < min_inst_buy:
            reasons.append(f"三大法人買超 {inst_buy} < 門檻 {min_inst_buy}")
    else:
        # 💡 修正：將輸出的文字改為「三大法人買超」
        if margin < min_margin:
            reasons.append(f"毛利率 {margin}% < 門檻 {min_margin}%")
        if rev_yoy < min_revenue_yoy:
            reasons.append(f"營收YoY {rev_yoy}% < 門檻 {min_revenue_yoy}%")
        if inst_buy < min_inst_buy:
            reasons.append(f"三大法人買超 {inst_buy} < 門檻 {min_inst_buy}")
        
    if reasons:
         decision = "觀望 (HOLD)"
    else:
         success_msg = "符合籌碼面進場指標！(ETF不看財報)" if is_etf else "符合所有基本面與籌碼面指標！"
         reasons.append(success_msg)
         
    tz_tw = timezone(timedelta(hours=8))
    current_time = datetime.now(tz_tw).strftime("%Y-%m-%d %H:%M:%S")
    
    db_row = [
        stock_id,
        current_time,
        price,
        vol,
        margin,
        rev_yoy,
        inst_buy,
        decision
    ]
    
    await upsert_stock_data(stock_id, db_row)
    
    
    return {
        "stock_id": stock_id,
        "time": current_time,
        "price": price,
        "volume": vol,
        "margin": margin,
        "rev_yoy": rev_yoy,
        "inst_buy": inst_buy,
        "decision": decision,
        "reasons": reasons
    }

async def get_strategy_recommendation() -> dict:
    """
    推進建議服務：
    1. 讀取 USER_SETTINGS 中的每月薪水 (MONTHLY_SALARY)、ETF目標 (TARGET_ANNUAL_DIVIDEND) 與焦點標的 (STRATEGY_FOCUS_TICKER)
    2. 取得焦點標的之最新股價，並計算買進「一張 (1000股)」之成本
    3. 計算「本月可買」(等於 MONTHLY_SALARY) 與「下張差額」(一張成本 - 每月薪水，最少為 0)
    4. 呼叫進度服務取得目前總年配息
    5. 取得焦點標的過去一年總配息，計算距離目標額之額外持股股數、總成本、以及達標所需月份 (不含複利之保守估計)
    """
    from core.services.progress_service import calculate_progress
    from core.repositories.sheets_db import get_financial_user_settings, get_stock_db_data, fetch_dividend_past_year
    
    user_settings = await get_financial_user_settings()
    db_data = await get_stock_db_data()
    
    monthly_salary = float(user_settings.get("MONTHLY_SALARY", 0.0))
    target_dividend = float(user_settings.get("TARGET_ANNUAL_DIVIDEND", 0.0))
    focus_ticker = str(user_settings.get("STRATEGY_FOCUS_TICKER", "")).strip()
    
    # 確保焦點標的在資料庫中有資料
    if focus_ticker not in db_data or db_data[focus_ticker].get("price", 0.0) == 0.0:
        await analyze_and_decide(focus_ticker)
        db_data = await get_stock_db_data()
        
    focus_data = db_data.get(focus_ticker, {})
    focus_price = float(focus_data.get("price", 0.0))
    
    # 一張 (1000股) 成本
    one_lot_cost = focus_price * 1000
    diff_for_next_lot = max(0.0, one_lot_cost - monthly_salary)
    
    # 取得目前進度以獲得距離目標配息的差額
    progress_data = await calculate_progress()
    total_annual_dividend = progress_data["total_annual_dividend"]
    remaining_dividend_needed = max(0.0, target_dividend - total_annual_dividend)
    
    # 取得焦點標的的每股年配息
    focus_dividend_per_share = await fetch_dividend_past_year(focus_ticker)
    
    if focus_dividend_per_share > 0:
        additional_shares_needed = remaining_dividend_needed / focus_dividend_per_share
        total_cost_needed = additional_shares_needed * focus_price
        months_needed = total_cost_needed / monthly_salary if monthly_salary > 0 else 0.0
    else:
        additional_shares_needed = 0.0
        total_cost_needed = 0.0
        months_needed = 0.0
        
    return {
        "monthly_salary": monthly_salary,
        "target_annual_dividend": target_dividend,
        "focus_ticker": focus_ticker,
        "focus_price": focus_price,
        "one_lot_cost": one_lot_cost,
        "diff_for_next_lot": diff_for_next_lot,
        "total_annual_dividend": total_annual_dividend,
        "remaining_dividend_needed": remaining_dividend_needed,
        "focus_dividend_per_share": focus_dividend_per_share,
        "additional_shares_needed": additional_shares_needed,
        "total_cost_needed": total_cost_needed,
        "months_needed": months_needed
    }