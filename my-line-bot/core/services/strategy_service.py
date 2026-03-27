import asyncio
from datetime import datetime
from core.repositories.stock_fetcher import fetch_stock_info
from core.repositories.sheets_db import get_user_settings, upsert_stock_data

async def analyze_and_decide(stock_id: str) -> dict:
    """
    核心大腦：非同步併發抓取資料與試算表設定，並進行策略比對
    回傳決策結果與相關數據。
    確保能滿足 Vercel < 10s 執行限制。
    """
    # 併發執行：抓取股票資訊 與 讀取使用者設定
    stock_task = fetch_stock_info(stock_id)
    settings_task = get_user_settings()
    
    # 收集結果
    results = await asyncio.gather(stock_task, settings_task, return_exceptions=True)
    stock_data = results[0] if not isinstance(results[0], Exception) else {}
    user_settings = results[1] if not isinstance(results[1], Exception) else {}
    
    # 若抓不到基本資料，提供退路
    if not stock_data:
        return {"error": True, "message": f"查無代號 {stock_id}，請確認是否輸入完整的台股代號（如 0050）。"}
        
    # 取出設定閾值 (使用預設值防呆)
    min_margin = float(user_settings.get("MIN_MARGIN_PERCENT", 30.0))
    min_revenue_yoy = float(user_settings.get("MIN_REVENUE_YOY", 5.0))
    min_inst_buy = int(user_settings.get("MIN_INSTITUTIONAL_BUY", 1000))
    
    # 取出股票數據
    price = stock_data.get("price", 0.0)
    vol = stock_data.get("volume", 0)
    margin = stock_data.get("gross_margin", 0.0)
    rev_yoy = stock_data.get("revenue_yoy", 0.0)
    inst_buy = stock_data.get("institutional_buy", 0)
    
    # 策略判定：符合所有條件則標示為買進，否則觀望
    decision = "買進 (BUY)"
    reasons = []
    
    if margin < min_margin:
        reasons.append(f"毛利率 {margin}% < 門檻 {min_margin}%")
    if rev_yoy < min_revenue_yoy:
        reasons.append(f"營收YoY {rev_yoy}% < 門檻 {min_revenue_yoy}%")
    if inst_buy < min_inst_buy:
        reasons.append(f"投信買超 {inst_buy} < 門檻 {min_inst_buy}")
        
    if reasons:
         decision = "觀望 (HOLD)"
    else:
         reasons.append("符合所有進場策略指標！")
         
    # 紀錄當下時間
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 準備寫入資料庫的陣列結構 (對應 A:H 欄)
    # [StockID, Time, Price, Volume, Margin, Rev_YoY, Inst_Buy, Decision]
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
    
    # 將最新數據與結果寫入資料庫
    # 不 await 可能會在 Vercel 被直接砍斷，因此這裡確實等待它完成
    await upsert_stock_data(stock_id, db_row)
    
    # 回傳給 View 層封裝
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
