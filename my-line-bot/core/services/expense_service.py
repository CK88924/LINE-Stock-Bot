from datetime import datetime, timezone, timedelta
from core.repositories.sheets_db import get_annual_expenses

async def calculate_expenses() -> dict:
    """
    計算年度與當月開銷：
    1. 取得工作表5的年度固定支出項目
    2. 取得台灣目前時間(UTC+8)的月份
    3. 計算本月預計支出與全年度總支出
    4. 提醒未來三個月內預計支出的項目
    """
    expenses = await get_annual_expenses()
    
    # 取得台灣目前月份
    tz_tw = timezone(timedelta(hours=8))
    current_month = datetime.now(tz_tw).month
    
    this_month_expenses = 0.0
    total_annual_expenses = 0.0
    this_month_items = []
    
    # 未來三個月包含當月、下個月、下下個月 (1-indexed, 1-12)
    next_3_months = [
        current_month,
        ((current_month) % 12) + 1,
        ((current_month + 1) % 12) + 1
    ]
    
    upcoming_reminders = []
    
    for e in expenses:
        cost = e["cost"]
        month = e["month"]
        item = e["item"]
        
        total_annual_expenses += cost
        
        if month == current_month:
            this_month_expenses += cost
            this_month_items.append(e)
            
        if month in next_3_months:
            upcoming_reminders.append(e)
            
    # 按月份排序提醒項目
    # 由於月份可能跨年 (例如 12, 1, 2)，排序時依據它在 next_3_months 中的索引來排
    upcoming_reminders.sort(key=lambda x: next_3_months.index(x["month"]))
    
    return {
        "current_month": current_month,
        "this_month_expenses": this_month_expenses,
        "this_month_items": this_month_items,
        "total_annual_expenses": total_annual_expenses,
        "upcoming_reminders": upcoming_reminders,
        "all_expenses": expenses
    }
