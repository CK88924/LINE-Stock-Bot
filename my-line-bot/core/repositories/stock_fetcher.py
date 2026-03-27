import aiohttp
import asyncio
from datetime import datetime, timedelta, timezone

async def fetch_yahoo_finance(session: aiohttp.ClientSession, stock_id: str) -> dict:
    """1. 去 Yahoo 抓取真實股價與成交量 (使用最穩定的 v8/chart 端點)"""
    suffixes = [".TW", ".TWO"]
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    for suffix in suffixes:
        yahoo_symbol = f"{stock_id}{suffix}"
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}"
        try:
            async with session.get(url, headers=headers, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    chart_result = data.get("chart", {}).get("result", [])
                    if not chart_result:
                        continue
                        
                    meta = chart_result[0].get("meta", {})
                    price = meta.get("regularMarketPrice", 0.0)
                    if not price or price == 0.0:
                        continue
                        
                    volume = meta.get("regularMarketVolume", 0)
                    return {"price": price, "volume": volume}
        except Exception as e:
            print(f"Yahoo API Error for {yahoo_symbol}: {e}")
            continue
    return {} 

async def fetch_finmind_inst_buy(session: aiohttp.ClientSession, stock_id: str) -> int:
    """2. 去 FinMind 抓取投信買賣超"""
    try:
        tz_tw = timezone(timedelta(hours=8))
        today = datetime.now(tz_tw)
        end_date = today.strftime("%Y-%m-%d")
        start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        
        url = f"https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockInstitutionalInvestorsBuySell&data_id={stock_id}&start_date={start_date}&end_date={end_date}"
        async with session.get(url, timeout=5) as response:
            if response.status == 200:
                data = await response.json()
                records = data.get("data", [])
                if not records:
                    return 0
                    
                latest_date = records[-1]["date"]
                net_buy = 0
                for row in records:
                    if row["date"] == latest_date and row["name"] == "Investment_Trust":
                        net_buy += (row.get("buy", 0) - row.get("sell", 0)) / 1000
                return int(net_buy)
    except Exception as e:
        print(f"FinMind InstBuy Error: {e}")
    return 0 

async def fetch_finmind_revenue(session: aiohttp.ClientSession, stock_id: str) -> float:
    """3. 去 FinMind 抓取最新月營收 YoY"""
    try:
        tz_tw = timezone(timedelta(hours=8))
        # 抓過去 4 個月，確保能拿到最新公佈的月份
        start_date = (datetime.now(tz_tw) - timedelta(days=120)).strftime("%Y-%m-%d")
        url = f"https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockMonthRevenue&data_id={stock_id}&start_date={start_date}"
        
        async with session.get(url, timeout=5) as response:
            if response.status == 200:
                data = await response.json()
                records = data.get("data", [])
                if records:
                    latest = records[-1]
                    rev = latest.get("revenue", 0)
                    rev_last_year = latest.get("revenue_month_last_year", 0)
                    if rev_last_year > 0:
                        # 計算 YoY 百分比: ((當月 - 去年同月) / 去年同月) * 100
                        return round(((rev - rev_last_year) / rev_last_year) * 100, 2)
    except Exception as e:
        print(f"FinMind Revenue Error: {e}")
    return 0.0

async def fetch_finmind_margin(session: aiohttp.ClientSession, stock_id: str) -> float:
    """4. 去 FinMind 抓取最新季財報計算毛利率"""
    try:
        tz_tw = timezone(timedelta(hours=8))
        # 抓過去 8 個月，確保能拿到最新一季的財報
        start_date = (datetime.now(tz_tw) - timedelta(days=240)).strftime("%Y-%m-%d")
        url = f"https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockFinancialStatements&data_id={stock_id}&start_date={start_date}"
        
        async with session.get(url, timeout=5) as response:
            if response.status == 200:
                data = await response.json()
                records = data.get("data", [])
                if not records:
                    return 0.0
                    
                latest_date = records[-1]["date"]
                revenue = 0
                gross_profit = 0
                
                for row in records:
                    if row["date"] == latest_date:
                        t = row.get("type", "")
                        # 匹配台灣財報科目名稱
                        if t in ["營業收入", "營業收入淨額"]:
                            revenue = row.get("value", 0)
                        elif t in ["營業毛利（毛損）", "營業毛利（毛損）淨額", "營業毛利(毛損)", "營業毛利"]:
                            gross_profit = row.get("value", 0)
                            
                if revenue > 0:
                    # 計算毛利率: (營業毛利 / 營業收入) * 100
                    return round((gross_profit / revenue) * 100, 2)
    except Exception as e:
        print(f"FinMind Margin Error: {e}")
    return 0.0

async def fetch_stock_info(stock_id: str) -> dict:
    """大總管：動態派車，整合所有真實數據"""
    is_etf = stock_id.startswith("00")
    
    async with aiohttp.ClientSession() as session:
        # 基本班底：股價與投信買超
        tasks = [
            fetch_yahoo_finance(session, stock_id),
            fetch_finmind_inst_buy(session, stock_id)
        ]
        
        # 如果是個股，追加兩台車去抓真實財報
        if not is_etf:
            tasks.append(fetch_finmind_revenue(session, stock_id))
            tasks.append(fetch_finmind_margin(session, stock_id))
            
        # 🚀 齊發！同時等待所有 API 回應
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        yahoo_data = results[0] if isinstance(results[0], dict) else {}
        inst_buy = results[1] if isinstance(results[1], int) else 0
        
        if not yahoo_data:
            return {}
            
        # 拆解財報數據 (如果是 ETF，預設就是 0.0，因為大腦本來就不看)
        revenue_yoy = 0.0
        gross_margin = 0.0
        
        if not is_etf:
            revenue_yoy = results[2] if isinstance(results[2], float) else 0.0
            gross_margin = results[3] if isinstance(results[3], float) else 0.0
            
        return {
            "stock_id": stock_id,
            "price": yahoo_data.get("price", 0.0),
            "volume": yahoo_data.get("volume", 0),
            "revenue_yoy": revenue_yoy,
            "gross_margin": gross_margin,
            "institutional_buy": inst_buy
        }