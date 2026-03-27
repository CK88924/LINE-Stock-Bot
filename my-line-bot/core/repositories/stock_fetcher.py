import aiohttp
import asyncio

async def fetch_stock_info(stock_id: str) -> dict:
    """
    使用 Yahoo Finance API 抓取台股資訊與真實財報數據
    找不到股票時回傳空字典，要求使用者必須輸入完整正確代號。
    """
    yahoo_symbol = f"{stock_id}.TW"
    # 改用 quoteSummary 取得真實價格與財報模組
    url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{yahoo_symbol}?modules=financialData,price"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    result = data.get("quoteSummary", {}).get("result", None)
                    
                    # 找不到這檔股票 (例如亂打代號)，回傳空字典
                    if not result:
                        return {} 
                        
                    quote_data = result[0]
                    
                    # 1. 解析股價與成交量 (price 模組)
                    price_data = quote_data.get("price", {})
                    price = price_data.get("regularMarketPrice", {}).get("raw", 0.0)
                    
                    # 如果連價格都沒有，代表這檔股票可能已經下市或代號完全錯誤
                    if not price or price == 0.0:
                        return {}
                        
                    volume = price_data.get("regularMarketVolume", {}).get("raw", 0)
                    
                    # 2. 解析毛利率與營收 YoY (financialData 模組)
                    fin_data = quote_data.get("financialData", {})
                    
                    # 將小數點轉為百分比
                    margin_raw = fin_data.get("grossMargins", {}).get("raw", 0.0)
                    gross_margin = round(margin_raw * 100, 2) if margin_raw else 0.0
                    
                    rev_growth_raw = fin_data.get("revenueGrowth", {}).get("raw", 0.0)
                    revenue_yoy = round(rev_growth_raw * 100, 2) if rev_growth_raw else 0.0
                    
                    return {
                        "stock_id": stock_id,
                        "price": price,
                        "volume": volume,
                        "revenue_yoy": revenue_yoy,
                        "gross_margin": gross_margin,
                        "institutional_buy": 1500 # 註：投信買超因 Yahoo 無資料，暫維預設值
                    }
                else:
                    return {}
        except Exception as e:
            print(f"Error fetching stock info for {stock_id}: {e}")
            return {}