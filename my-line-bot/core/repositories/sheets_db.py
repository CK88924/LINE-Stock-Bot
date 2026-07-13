import asyncio
import time  # 引入 time 模組來做快取計時
import gspread_asyncio
import aiohttp
from datetime import datetime, timedelta, timezone
from google.oauth2.service_account import Credentials
from core.config import settings

def get_creds():
    creds_dict = settings.get_google_credentials_dict()
    if not creds_dict:
        raise ValueError("Invalid GOOGLE_CREDENTIALS configuration.")
    creds = Credentials.from_service_account_info(creds_dict)
    scoped = creds.with_scopes([
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ])
    return scoped

agcm = gspread_asyncio.AsyncioGspreadClientManager(get_creds)

_settings_cache = None
_cache_time = 0
CACHE_TTL = 300  # 5 分鐘快取

async def get_client():
    return await agcm.authorize()

async def get_user_settings() -> dict:
    """ Reads settings from '設定' sheet with 5 minute cache """
    global _settings_cache, _cache_time
    
    # 🚨 修正：改用標準的 time.time()，避免 async loop 版本棄用警告
    now = time.time()
    
    if _settings_cache is not None and (now - _cache_time) < CACHE_TTL:
        return _settings_cache

    client = await get_client()
    try:
        sh = await client.open_by_key(settings.SPREADSHEET_ID)
        worksheet = await sh.worksheet("設定")
        values = await worksheet.get_all_values()
        
        new_settings = {}
        for row in values:
            if len(row) >= 2 and row[0].strip() and row[0] != "Parameter":
                key = row[0].strip()
                val = row[1].strip()
                try:
                    new_settings[key] = float(val) if '.' in val else int(val)
                except ValueError:
                    new_settings[key] = val
                    
        _settings_cache = new_settings
        _cache_time = now
        return _settings_cache
    except Exception as e:
        print(f"Error reading settings: {e}")
        return _settings_cache or {}

async def upsert_stock_data(stock_id: str, data: list):
    """
    動態 Upsert 寫入資料庫: 
    使用 stock_id 搜尋 A 欄，若存在則覆蓋該列，不存在則新增到最底下
    """
    client = await get_client()
    try:
        sh = await client.open_by_key(settings.SPREADSHEET_ID)
        worksheet = await sh.worksheet("資料庫")
        
        # 尋找 stock_id
        cell = await worksheet.find(stock_id, in_column=1)
        if cell:
            row_index = cell.row
            range_name = f"A{row_index}"
            
            # 🚨 修正：明確指定 values 與 range_name 參數，完美相容 gspread v5 與 v6
            await worksheet.update(values=[data], range_name=range_name)
        else:
            await worksheet.append_row(data)
    except Exception as e:
        print(f"Error upserting stock data: {e}")

async def get_financial_user_settings() -> dict:
    """ Reads settings from 'USER_SETTINGS' sheet """
    client = await get_client()
    try:
        sh = await client.open_by_key(settings.SPREADSHEET_ID)
        worksheet = await sh.worksheet("USER_SETTINGS")
        values = await worksheet.get_all_values()
        
        if len(values) < 2:
            return {}
        
        headers = [h.strip() for h in values[0]]
        row = values[1]
        
        settings_dict = {}
        for i, header in enumerate(headers):
            if i < len(row):
                val = row[i].strip()
                try:
                    settings_dict[header] = float(val) if '.' in val else int(val)
                except ValueError:
                    settings_dict[header] = val
        return settings_dict
    except Exception as e:
        print(f"Error reading USER_SETTINGS: {e}")
        return {}

async def get_my_holdings() -> list:
    """ Reads holdings from 'MY_HOLDINGS' sheet """
    client = await get_client()
    try:
        sh = await client.open_by_key(settings.SPREADSHEET_ID)
        worksheet = await sh.worksheet("MY_HOLDINGS")
        values = await worksheet.get_all_values()
        
        holdings = []
        if len(values) <= 1:
            return holdings
            
        # Header: ['Ticker', 'Shares']
        for row in values[1:]:
            if len(row) >= 2 and row[0].strip():
                ticker = row[0].strip()
                try:
                    shares = float(row[1].strip())
                except ValueError:
                    shares = 0.0
                holdings.append({"ticker": ticker, "shares": shares})
        return holdings
    except Exception as e:
        print(f"Error reading MY_HOLDINGS: {e}")
        return []

async def get_annual_expenses() -> list:
    """ Reads annual expenses from '工作表5' (ANNUAL_EXPENSES) sheet """
    client = await get_client()
    try:
        sh = await client.open_by_key(settings.SPREADSHEET_ID)
        # 為了容錯，優先讀取 '工作表5'，如果不存在則讀取 'ANNUAL_EXPENSES'
        try:
            worksheet = await sh.worksheet("工作表5")
        except Exception:
            worksheet = await sh.worksheet("ANNUAL_EXPENSES")
            
        values = await worksheet.get_all_values()
        
        expenses = []
        if len(values) <= 1:
            return expenses
            
        # Header: ['Item', 'Cost', 'Month']
        for row in values[1:]:
            if len(row) >= 3 and row[0].strip():
                item = row[0].strip()
                try:
                    cost = float(row[1].strip())
                except ValueError:
                    cost = 0.0
                try:
                    month = int(float(row[2].strip()))
                except ValueError:
                    month = 1
                expenses.append({"item": item, "cost": cost, "month": month})
        return expenses
    except Exception as e:
        print(f"Error reading ANNUAL_EXPENSES: {e}")
        return []

async def get_stock_db_data() -> dict:
    """ Reads all data from '資料庫' sheet and returns a dict keyed by stock_id """
    client = await get_client()
    try:
        sh = await client.open_by_key(settings.SPREADSHEET_ID)
        worksheet = await sh.worksheet("資料庫")
        values = await worksheet.get_all_values()
        
        db_data = {}
        if len(values) <= 1:
            return db_data
            
        # Header: ['股票代號', '分析時間', '最新股價', '成交量', '毛利率(%)', '營收YoY(%)', '三大法人買超', '結算決策']
        for row in values[1:]:
            if len(row) >= 3 and row[0].strip():
                stock_id = row[0].strip()
                try:
                    price = float(row[2].strip())
                except ValueError:
                    price = 0.0
                try:
                    volume = float(row[3].strip())
                except ValueError:
                    volume = 0.0
                try:
                    margin = float(row[4].strip())
                except ValueError:
                    margin = 0.0
                try:
                    rev_yoy = float(row[5].strip())
                except ValueError:
                    rev_yoy = 0.0
                try:
                    inst_buy = float(row[6].strip())
                except ValueError:
                    inst_buy = 0.0
                decision = row[7].strip() if len(row) >= 8 else ""
                
                db_data[stock_id] = {
                    "stock_id": stock_id,
                    "updated_at": row[1].strip() if len(row) >= 2 else "",
                    "price": price,
                    "volume": volume,
                    "margin": margin,
                    "rev_yoy": rev_yoy,
                    "inst_buy": inst_buy,
                    "decision": decision
                }
        return db_data
    except Exception as e:
        print(f"Error reading stock database: {e}")
        return {}

async def fetch_dividend_past_year(ticker: str) -> float:
    """ Fetch the sum of cash dividends distributed in the past 365 days from FinMind """
    try:
        async with aiohttp.ClientSession() as session:
            # 查詢過去 450 天的除息資料，以包含當前的完整年度除息事件
            start_date = (datetime.now() - timedelta(days=450)).strftime('%Y-%m-%d')
            url = f"https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockDividend&data_id={ticker}&start_date={start_date}"
            async with session.get(url, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    records = data.get("data", [])
                    if not records:
                        return 0.0
                    
                    total_div = 0.0
                    today = datetime.now()
                    one_year_ago = today - timedelta(days=365)
                    
                    for r in records:
                        date_str = r.get("CashExDividendTradingDate") or r.get("date")
                        if not date_str:
                            continue
                        try:
                            dt = datetime.strptime(date_str, "%Y-%m-%d")
                            if one_year_ago <= dt <= today:
                                cash = float(r.get("CashEarningsDistribution") or 0.0)
                                total_div += cash
                        except Exception:
                            continue
                    return total_div
    except Exception as e:
        print(f"Error fetching dividend for {ticker}: {e}")
        return 0.0