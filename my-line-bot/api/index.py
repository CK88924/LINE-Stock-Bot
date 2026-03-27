import os
import sys
import logging
import asyncio

# 加入根目錄到 sys.path 確保可匯入 core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse

from core.config import settings
from core.services.strategy_service import analyze_and_decide
from core.views.line_flex_builder import build_stock_flex_message

from linebot.v3 import WebhookParser
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    AsyncApiClient,
    AsyncMessagingApi,
    Configuration,
    ReplyMessageRequest,
    FlexMessage,
    FlexContainer
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)

app = FastAPI()
logging.basicConfig(level=logging.INFO)

configuration = Configuration(access_token=settings.LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(settings.LINE_CHANNEL_SECRET)

@app.get("/")
async def root():
    return JSONResponse(content={"status": "alive", "message": "LINE Stock Bot is running"})

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    # favicon is stored at ../public/favicon.ico relative to this index.py file
    favicon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public", "favicon.ico")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    return JSONResponse(status_code=404, content={"message": "Favicon not found"})

@app.post("/api/index.py")
@app.post("/")
async def callback(request: Request):
    signature = request.headers.get("X-Line-Signature", "")
    body = await request.body()
    body_str = body.decode("utf-8")

    try:
        events = parser.parse(body_str, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    async with AsyncApiClient(configuration) as async_api_client:
        line_bot_api = AsyncMessagingApi(async_api_client)
        
        for event in events:
            if not isinstance(event, MessageEvent):
                continue
            if not isinstance(event.message, TextMessageContent):
                continue

            user_text = event.message.text.strip()
            
            # 簡單過濾，若使用者輸入非英文與數字 (通常台股代號為純數字)
            if not user_text.isalnum():
                continue
                
            stock_id = user_text
            
            # 核心：非同步擷取資料與判定
            result_data = await analyze_and_decide(stock_id)
            
            # 視圖：將策略轉為 Flex Message JSON Dict
            flex_dict = build_stock_flex_message(result_data)
            
            try:
                # v3 寫法：轉換為 FlexContainer 類別
                flex_container = FlexContainer.from_dict(flex_dict)
                flex_message = FlexMessage(alt_text=f"{stock_id} 策略分析", contents=flex_container)
                
                # 傳遞回 LINE 伺服器
                await line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[flex_message]
                    )
                )
            except Exception as e:
                logging.error(f"Error sending LINE message: {e}")

    return JSONResponse(content={"status": "OK"})
