import os
import json
from dotenv import load_dotenv

# 載入本地 .env 檔案（如果存在）
load_dotenv()

class Settings:
    @property
    def LINE_CHANNEL_SECRET(self) -> str:
        return os.environ.get("LINE_CHANNEL_SECRET", "")

    @property
    def LINE_CHANNEL_ACCESS_TOKEN(self) -> str:
        return os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")

    @property
    def GOOGLE_CREDENTIALS(self) -> str:
        # 這裡會是一長串 JSON 格式字串
        return os.environ.get("GOOGLE_CREDENTIALS", "{}")

    @property
    def SPREADSHEET_ID(self) -> str:
        return os.environ.get("SPREADSHEET_ID", "")

    def get_google_credentials_dict(self) -> dict:
        try:
            return json.loads(self.GOOGLE_CREDENTIALS)
        except json.JSONDecodeError:
            print("Failed to decode GOOGLE_CREDENTIALS. Is it valid JSON?")
            return {}

# 實例化全域設定物件
settings = Settings()
