import aiohttp
import asyncio
from datetime import datetime, timedelta

async def fetch_yahoo_finance(session: aiohttp.ClientSession, stock_id: str) -> dict:
    """去 Yahoo 抓取股價與財報 (支援上市 .TW 與上櫃 .TWO)"""
    suffixes = [".TW", ".TWO"]
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    for suffix in suffixes:
        yahoo_symbol = f"{stock_id}{suffix}"
        url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{yahoo_symbol}?modules=financialData,price"
        
        try:
            async with session.get(url, headers=headers, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    result = data.get("quoteSummary", {}).get("result", None)
                    
                    if not result:
                        continue 
                        
                    quote_data = result[0]
                    price_data = quote_data.get("price", {})
                    price = price_data.get("regularMarketPrice", {}).get("raw", 0.0)
                    
                    if not price or price == 0.0:
                        continue
                        
                    volume = price_data.get("regularMarketVolume", {}).get("raw", 0)
                    fin_data = quote_data.get("financialData", {})
                    
                    margin_raw = fin_data.get("grossMargins", {}).get("raw", 0.0)
                    gross_margin = round(margin_raw * 100, 2) if margin_raw else 0.0
                    
                    rev_growth_raw = fin_data.get("revenueGrowth", {}).get("raw", 0.0)
                    revenue_yoy = round(rev_growth_raw * 100, 2) if rev_growth_raw else 0.0
                    
                    return {
                        "price": price,
                        "volume": volume,
                        "revenue_yoy": revenue_yoy,
                        "gross_margin": gross_margin
                    }
        except Exception as e:
            print(f"Yahoo API Error for {yahoo_symbol}: {e}")
            continue
            
    return {} # 找不到股票回傳空字典

async def fetch_finmind_inst_buy(session: aiohttp.ClientSession, stock_id: str) -> int:
    """去 FinMind 抓取最新一天的投信淨買賣超 (張數)"""
    try:
        # 抓取過去 7 天的資料，確保能涵蓋到最近的交易日 (避開六日)
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        url = f"https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockInstitutionalInvestorsBuySell&data_id={stock_id}&start_date={start_date}&end_date={end_date}"
        
        async with session.get(url, timeout=5) as response:
            if response.status == 200:
                data = await response.json()
                records = data.get("data", [])
                
                if not records:
                    return 0
                    
                # 找出陣列中最新的一天 (通常在最後面)
                latest_date = records[-1]["date"]
                net_buy = 0
                
                for row in records:
                    # 篩選最新日期，並且主力名稱為「投信」的數據
                    if row["date"] == latest_date and "投信" in row["name"]:
                        # FinMind 的買賣單位是「股」，我們除以 1000 換算成「張」
                        net_buy += (row.get("buy", 0) - row.get("sell", 0)) / 1000
                        
                return int(net_buy)
    except Exception as e:
        print(f"FinMind API Error for {stock_id}: {e}")
        
    return 0 # 發生錯誤或無資料時，防呆回傳 0

async def fetch_stock_info(stock_id: str) -> dict:
    """
    大總管：同時發出 Yahoo 和 FinMind 請求，並將結果合併
    """
    async with aiohttp.ClientSession() as session:
        # 🚨 asyncio.gather 讓兩個 API 同時跑，節省一半以上的等待時間
        yahoo_task = fetch_yahoo_finance(session, stock_id)
        finmind_task = fetch_finmind_inst_buy(session, stock_id)
        
        results = await asyncio.gather(yahoo_task, finmind_task, return_exceptions=True)
        
        # 拆解結果
        yahoo_data = results[0] if isinstance(results[0], dict) else {}
        inst_buy = results[1] if isinstance(results[1], int) else 0
        
        # 防呆機制：如果連 Yahoo 都找不到股價，代表這檔股票不存在
        if not yahoo_data:
            return {}
            
        # 將真實的籌碼數據與財報數據合併回傳
        return {
            "stock_id": stock_id,
            "price": yahoo_data.get("price", 0.0),
            "volume": yahoo_data.get("volume", 0),
            "revenue_yoy": yahoo_data.get("revenue_yoy", 0.0),
            "gross_margin": yahoo_data.get("gross_margin", 0.0),
            "institutional_buy": inst_buy  # ✨ 這裡終於是真實資料了！
        }