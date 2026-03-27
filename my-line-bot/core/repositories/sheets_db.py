import asyncio
import time  # 引入 time 模組來做快取計時
import gspread_asyncio
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