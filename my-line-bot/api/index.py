import os
import sys
import logging
import asyncio

# 加入根目錄到 sys.path 確保可匯入 core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse

from core.config import settings
from core.services.strategy_service import analyze_and_decide, get_strategy_recommendation
from core.services.progress_service import calculate_progress
from core.services.expense_service import calculate_expenses
from core.views.line_flex_builder import (
    build_stock_flex_message,
    build_progress_flex_message,
    build_strategy_flex_message,
    build_expense_flex_message
)

from linebot.v3 import WebhookParser
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    AsyncApiClient,
    AsyncMessagingApi,
    Configuration,
    ReplyMessageRequest,
    FlexMessage,
    TextMessage,
    FlexContainer,
    QuickReply,
    QuickReplyItem,
    MessageAction
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
    # favicon is stored directly in the api folder at api/favicon.ico
    favicon_path = os.path.join(os.path.dirname(__file__), "favicon.ico")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path, media_type="image/x-icon")
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
            
            # 取得用戶的 line user id 并去空格
            user_id = getattr(event.source, "user_id", "").strip()
            is_authorized_user = (user_id == "U16a829b0c0ad6b0aa565bb6a54944c88")
            logging.info(f"DEBUG: Received message from user_id: '{user_id}' (len={len(user_id)}), is_authorized: {is_authorized_user}")
            
            # 清理表情符號以進行指令比對
            clean_text = user_text.replace("📊", "").replace("💡", "").replace("📅", "").strip()
            
            # 定義 Quick Reply 鍵盤按鈕 (僅限授權用戶使用)
            quick_reply = None
            if is_authorized_user:
                quick_reply = QuickReply(
                    items=[
                        QuickReplyItem(action=MessageAction(label="📊 目前進度", text="目前進度")),
                        QuickReplyItem(action=MessageAction(label="💡 推進建議", text="推進建議")),
                        QuickReplyItem(action=MessageAction(label="📅 開銷檢查", text="開銷檢查"))
                    ]
                )
            
            # 路由處理
            # 如果是授權用戶，且輸入為指令，則進行指令處理
            if is_authorized_user and clean_text == "目前進度":
                try:
                    progress_data = await calculate_progress()
                    flex_dict = build_progress_flex_message(progress_data)
                    flex_container = FlexContainer.from_dict(flex_dict)
                    flex_message = FlexMessage(alt_text="大水庫財務進度 📊", contents=flex_container, quick_reply=quick_reply)
                    
                    await line_bot_api.reply_message(
                        ReplyMessageRequest(reply_token=event.reply_token, messages=[flex_message])
                    )
                except Exception as e:
                    logging.error(f"Error processing progress command: {e}")
                    try:
                        await line_bot_api.reply_message(
                            ReplyMessageRequest(
                                reply_token=event.reply_token,
                                messages=[TextMessage(text=f"處理進度查詢時發生錯誤: {e}", quick_reply=quick_reply)]
                            )
                        )
                    except Exception:
                        pass
                continue
                
            elif is_authorized_user and clean_text == "推進建議":
                try:
                    strategy_data = await get_strategy_recommendation()
                    flex_dict = build_strategy_flex_message(strategy_data)
                    flex_container = FlexContainer.from_dict(flex_dict)
                    flex_message = FlexMessage(alt_text="投資推進建議 💡", contents=flex_container, quick_reply=quick_reply)
                    
                    await line_bot_api.reply_message(
                        ReplyMessageRequest(reply_token=event.reply_token, messages=[flex_message])
                    )
                except Exception as e:
                    logging.error(f"Error processing strategy command: {e}")
                    try:
                        await line_bot_api.reply_message(
                            ReplyMessageRequest(
                                reply_token=event.reply_token,
                                messages=[TextMessage(text=f"處理推進建議時發生錯誤: {e}", quick_reply=quick_reply)]
                            )
                        )
                    except Exception:
                        pass
                continue
                
            elif is_authorized_user and clean_text == "開銷檢查":
                try:
                    expense_data = await calculate_expenses()
                    flex_dict = build_expense_flex_message(expense_data)
                    flex_container = FlexContainer.from_dict(flex_dict)
                    flex_message = FlexMessage(alt_text="年度固定開銷檢查 📅", contents=flex_container, quick_reply=quick_reply)
                    
                    await line_bot_api.reply_message(
                        ReplyMessageRequest(reply_token=event.reply_token, messages=[flex_message])
                    )
                except Exception as e:
                    logging.error(f"Error processing expense command: {e}")
                    try:
                        await line_bot_api.reply_message(
                            ReplyMessageRequest(
                                reply_token=event.reply_token,
                                messages=[TextMessage(text=f"處理開銷檢查時發生錯誤: {e}", quick_reply=quick_reply)]
                            )
                        )
                    except Exception:
                        pass
                continue
                
            # 檢查是否為台灣個股代號 (通用查詢股票，所有人都可以使用)
            elif clean_text.isalnum() and 4 <= len(clean_text) <= 6:
                stock_id = clean_text
                result_data = await analyze_and_decide(stock_id)
                
                if result_data.get("error"):
                    try:
                        await line_bot_api.reply_message(
                            ReplyMessageRequest(
                                reply_token=event.reply_token,
                                messages=[TextMessage(text=result_data.get("message"), quick_reply=quick_reply)]
                            )
                        )
                    except Exception as e:
                        logging.error(f"Error sending LINE text message: {e}")
                    continue
                
                flex_dict = build_stock_flex_message(result_data)
                
                try:
                    flex_container = FlexContainer.from_dict(flex_dict)
                    flex_message = FlexMessage(alt_text=f"{stock_id} 策略分析", contents=flex_container, quick_reply=quick_reply)
                    
                    await line_bot_api.reply_message(
                        ReplyMessageRequest(reply_token=event.reply_token, messages=[flex_message])
                    )
                except Exception as e:
                    logging.error(f"Error sending LINE message: {e}")
                continue
                
            # 如果是授權用戶，但輸入非上述項目，則回覆大水庫功能歡迎選單
            elif is_authorized_user:
                welcome_msg = (
                    "👋 您好！我是大水庫財務助理。\n\n"
                    "請點擊下方選單按鈕進行快速查詢，或直接輸入台灣股票/ETF代號（例如：00919、2330）進行即時個股與籌碼策略分析！"
                )
                try:
                    await line_bot_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[TextMessage(text=welcome_msg, quick_reply=quick_reply)]
                        )
                    )
                except Exception as e:
                    logging.error(f"Error sending default menu message: {e}")
            
            # 其他一般使用者，輸入非股票代號直接過濾跳過，不進行任何回覆，完全不影響原先功能
            else:
                continue

    return JSONResponse(content={"status": "OK"})
