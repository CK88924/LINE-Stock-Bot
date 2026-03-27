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