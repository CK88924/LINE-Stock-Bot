import aiohttp
import asyncio
from datetime import datetime, timedelta, timezone

async def fetch_yahoo_finance(session: aiohttp.ClientSession, stock_id: str) -> dict:
    """1. 去 Yahoo 抓取真實股價與成交量"""
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
                    if not chart_result: continue
                    meta = chart_result[0].get("meta", {})
                    price = meta.get("regularMarketPrice", 0.0)
                    if price == 0.0: continue
                    return {"price": price, "volume": meta.get("regularMarketVolume", 0)}
        except Exception:
            continue
    return {} 

async def fetch_finmind_inst_buy(session: aiohttp.ClientSession, stock_id: str) -> int:
    """2. 去 FinMind 抓取投信買賣超 (防呆：專抓投信有交易的最後一天)"""
    try:
        tz_tw = timezone(timedelta(hours=8))
        today = datetime.now(tz_tw)
        # 拉長到 14 天，避免遇到農曆新年等長假
        start_date = (today - timedelta(days=14)).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")
        url = f"https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockInstitutionalInvestorsBuySell&data_id={stock_id}&start_date={start_date}&end_date={end_date}"
        
        async with session.get(url, timeout=5) as response:
            if response.status == 200:
                data = await response.json()
                records = data.get("data", [])
                
                # 💡 終極修正：只挑出「投信」的紀錄，然後找出投信有交易的最新日期
                trust_records = [r for r in records if r.get("name") == "Investment_Trust"]
                if not trust_records: return 0
                
                latest_date = max([r["date"] for r in trust_records])
                net_buy = sum([(r.get("buy", 0) - r.get("sell", 0)) for r in trust_records if r["date"] == latest_date])
                return int(net_buy / 1000)
    except Exception as e:
        print(f"FinMind InstBuy Error: {e}")
    return 0 

async def fetch_finmind_revenue(session: aiohttp.ClientSession, stock_id: str) -> float:
    """3. 去 FinMind 抓取最新月營收 YoY"""
    try:
        tz_tw = timezone(timedelta(hours=8))
        start_date = (datetime.now(tz_tw) - timedelta(days=400)).strftime("%Y-%m-%d")
        url = f"https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockMonthRevenue&data_id={stock_id}&start_date={start_date}"
        async with session.get(url, timeout=5) as response:
            if response.status == 200:
                data = await response.json()
                records = data.get("data", [])
                if records:
                    latest = records[-1]
                    latest_year, latest_month, latest_rev = latest.get("revenue_year"), latest.get("revenue_month"), latest.get("revenue", 0)
                    last_year_rev = next((r.get("revenue", 0) for r in records if r.get("revenue_year") == latest_year - 1 and r.get("revenue_month") == latest_month), 0)
                    if last_year_rev > 0:
                        return round(((latest_rev - last_year_rev) / last_year_rev) * 100, 2)
    except Exception:
        pass
    return 0.0

async def fetch_finmind_margin(session: aiohttp.ClientSession, stock_id: str) -> float:
    """4. 去 FinMind 抓取最新季財報計算毛利率 (防呆：中英文科目通殺)"""
    try:
        tz_tw = timezone(timedelta(hours=8))
        start_date = (datetime.now(tz_tw) - timedelta(days=365)).strftime("%Y-%m-%d")
        url = f"https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockFinancialStatements&data_id={stock_id}&start_date={start_date}"
        
        async with session.get(url, timeout=5) as response:
            if response.status == 200:
                data = await response.json()
                records = data.get("data", [])
                if not records: return 0.0
                
                # 將所有有資料的日期由新到舊排序
                dates = sorted(list(set([r["date"] for r in records])), reverse=True)
                
                # 💡 終極修正：中英文可能出現的科目名稱通通放進來比對
                rev_keys = ["營業收入", "營業收入淨額", "OperatingRevenue", "Revenue"]
                margin_keys = ["營業毛利（毛損）", "營業毛利", "營業毛利（毛損）淨額", "GrossProfit"]
                
                # 從最新的財報季開始找，只要找到有營收和毛利的季就立刻結算
                for d in dates:
                    revenue = 0
                    gross_profit = 0
                    for r in records:
                        if r["date"] == d:
                            t = r.get("type", "")
                            if t in rev_keys: revenue = r.get("value", 0)
                            if t in margin_keys: gross_profit = r.get("value", 0)
                    if revenue > 0:
                        return round((gross_profit / revenue) * 100, 2)
    except Exception:
        pass
    return 0.0

async def fetch_stock_info(stock_id: str) -> dict:
    """大總管：動態派車，整合所有真實數據"""
    is_etf = stock_id.startswith("00")
    
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_yahoo_finance(session, stock_id), fetch_finmind_inst_buy(session, stock_id)]
        if not is_etf:
            tasks.extend([fetch_finmind_revenue(session, stock_id), fetch_finmind_margin(session, stock_id)])
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        yahoo_data = results[0] if isinstance(results[0], dict) else {}
        inst_buy = results[1] if isinstance(results[1], int) else 0
        
        if not yahoo_data: return {}
            
        revenue_yoy, gross_margin = 0.0, 0.0
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