import aiohttp
import asyncio

async def fetch_stock_info(stock_id: str) -> dict:
    """
    使用 Yahoo Finance API 抓取台股資訊
    實務上可能需要接證交所或第三方財報 API，這裡為展示而以 YF 股價結合預測數據。
    確保能滿足 Vercel 10 秒執行限制。
    """
    yahoo_symbol = f"{stock_id}.TW"
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    # 預設數據
    result_data = {
        "stock_id": stock_id,
        "price": 0.0,
        "volume": 0,
        "revenue_yoy": 10.5,     # 預設營收 YoY (%)
        "gross_margin": 35.0,    # 預設毛利率 (%)
        "institutional_buy": 1500 # 預設投信買超張數
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    chart_result = data.get("chart", {}).get("result", [])
                    if chart_result:
                        meta = chart_result[0].get("meta", {})
                        result_data["price"] = meta.get("regularMarketPrice", 0.0)
                        result_data["volume"] = meta.get("regularMarketVolume", 0)
        except Exception as e:
            print(f"Error fetching stock info for {stock_id}: {e}")
            
    return result_data
