def build_stock_flex_message(data: dict) -> dict:
    """
    將策略分析結果打包成 LINE Flex Message (JSON 格式)
    """
    stock_id = data.get("stock_id", "Unknown")
    decision = data.get("decision", "觀望 (HOLD)")
    price = data.get("price", 0.0)
    reasons = "\n".join(data.get("reasons", []))
    
    # 依據決策決定顏色
    header_color = "#4CAF50" if "買進" in decision else "#FF9800"
    
    flex_msg = {
      "type": "bubble",
      "header": {
        "type": "box",
        "layout": "vertical",
        "contents": [
          {
            "type": "text",
            "text": f"台股標的：{stock_id} 策略分析",
            "weight": "bold",
            "color": "#FFFFFF",
            "size": "md"
          }
        ],
        "backgroundColor": header_color
      },
      "body": {
        "type": "box",
        "layout": "vertical",
        "spacing": "sm",
        "contents": [
          {
            "type": "box",
            "layout": "horizontal",
            "contents": [
              {"type": "text", "text": "最新股價", "size": "sm", "color": "#888888", "flex": 1},
              {"type": "text", "text": f"${price:,.2f}", "size": "sm", "color": "#111111", "align": "end", "flex": 2, "weight": "bold"}
            ]
          },
          {
            "type": "box",
            "layout": "horizontal",
            "contents": [
              {"type": "text", "text": "結算決策", "size": "sm", "color": "#888888", "flex": 1},
              {"type": "text", "text": decision, "size": "md", "color": header_color, "align": "end", "flex": 2, "weight": "bold"}
            ]
          },
          {"type": "separator", "margin": "lg"},
          {
            "type": "text",
            "text": "判定原因 / 閾值比對：",
            "size": "xs",
            "color": "#888888",
            "margin": "md"
          },
          {
            "type": "text",
            "text": reasons,
            "size": "sm",
            "wrap": True,
            "color": "#333333",
            "margin": "sm"
          }
        ]
      },
      "footer": {
        "type": "box",
        "layout": "vertical",
        "contents": [
          {
            "type": "text",
            "text": f"分析時間: {data.get('time', '')}",
            "size": "xxs",
            "color": "#AAAAAA",
            "align": "center"
          }
        ]
      }
    }
    
    return flex_msg

def build_progress_flex_message(data: dict) -> dict:
    holdings = data.get("holdings", [])
    total_annual_dividend = data.get("total_annual_dividend", 0.0)
    target_annual_dividend = data.get("target_annual_dividend", 0.0)
    achievement_rate = data.get("achievement_rate", 0.0)
    distance_to_target = data.get("distance_to_target", 0.0)
    
    # 建立持股明細內容
    holdings_contents = []
    for h in holdings:
        ticker = h["ticker"]
        shares = h["shares"]
        price = h["price"]
        annual_div = h["annual_dividend"]
        
        holdings_contents.append({
            "type": "box",
            "layout": "horizontal",
            "margin": "sm",
            "contents": [
                {"type": "text", "text": f"• {ticker}", "size": "sm", "color": "#111111", "flex": 2, "weight": "bold"},
                {"type": "text", "text": f"{shares:,.0f} 股", "size": "xs", "color": "#666666", "align": "center", "flex": 2},
                {"type": "text", "text": f"${price:,.2f}", "size": "xs", "color": "#666666", "align": "center", "flex": 2},
                {"type": "text", "text": f"${annual_div:,.0f}/年", "size": "sm", "color": "#4CAF50", "align": "end", "flex": 3, "weight": "bold"}
            ]
        })
        
    if not holdings_contents:
        holdings_contents.append({
            "type": "text",
            "text": "目前無任何持股紀錄",
            "size": "sm",
            "color": "#888888",
            "align": "center",
            "margin": "md"
        })

    flex_msg = {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "📊 大水庫財務進度", "weight": "bold", "color": "#FFFFFF", "size": "lg"}
            ],
            "backgroundColor": "#2196F3"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": "年度配息目標", "size": "sm", "color": "#888888", "flex": 3},
                        {"type": "text", "text": f"${target_annual_dividend:,.0f}", "size": "sm", "color": "#111111", "align": "end", "flex": 5, "weight": "bold"}
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": "預估年配息額", "size": "sm", "color": "#888888", "flex": 3},
                        {"type": "text", "text": f"${total_annual_dividend:,.0f}", "size": "sm", "color": "#4CAF50", "align": "end", "flex": 5, "weight": "bold"}
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": "大水庫達標率", "size": "sm", "color": "#888888", "flex": 3},
                        {"type": "text", "text": f"{achievement_rate:.2f}%", "size": "md", "color": "#2196F3", "align": "end", "flex": 5, "weight": "bold"}
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": "距離目標差額", "size": "sm", "color": "#888888", "flex": 3},
                        {"type": "text", "text": f"${distance_to_target:,.0f}", "size": "sm", "color": "#F44336", "align": "end", "flex": 5, "weight": "bold"}
                    ]
                },
                {"type": "separator", "margin": "lg"},
                {
                    "type": "text",
                    "text": "📋 核心 ETF 持股明細",
                    "size": "sm",
                    "weight": "bold",
                    "color": "#111111",
                    "margin": "md"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": holdings_contents
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "資料僅供投資規劃參考",
                    "size": "xxs",
                    "color": "#AAAAAA",
                    "align": "center"
                }
            ]
        }
    }
    return flex_msg

def build_strategy_flex_message(data: dict) -> dict:
    monthly_salary = data.get("monthly_salary", 0.0)
    target_annual_dividend = data.get("target_annual_dividend", 0.0)
    focus_ticker = data.get("focus_ticker", "")
    focus_price = data.get("focus_price", 0.0)
    one_lot_cost = data.get("one_lot_cost", 0.0)
    diff_for_next_lot = data.get("diff_for_next_lot", 0.0)
    remaining_dividend_needed = data.get("remaining_dividend_needed", 0.0)
    focus_dividend_per_share = data.get("focus_dividend_per_share", 0.0)
    additional_shares_needed = data.get("additional_shares_needed", 0.0)
    total_cost_needed = data.get("total_cost_needed", 0.0)
    months_needed = data.get("months_needed", 0.0)
    
    # 達標預估時間字串
    if months_needed > 0:
        years = months_needed / 12
        if years >= 1:
            time_estimate_str = f"{months_needed:.1f} 個月 (約 {years:.2f} 年)"
        else:
            time_estimate_str = f"{months_needed:.1f} 個月"
    else:
        time_estimate_str = "已達標！" if remaining_dividend_needed == 0 else "無法預估 (無配息資料)"
        
    flex_msg = {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "💡 推進建議與達標預估", "weight": "bold", "color": "#FFFFFF", "size": "lg"}
            ],
            "backgroundColor": "#FF9800"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": "本月投資預算", "size": "sm", "color": "#888888", "flex": 3},
                        {"type": "text", "text": f"${monthly_salary:,.0f}", "size": "sm", "color": "#111111", "align": "end", "flex": 5, "weight": "bold"}
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": "焦點推進標的", "size": "sm", "color": "#888888", "flex": 3},
                        {"type": "text", "text": f"{focus_ticker} (${focus_price:,.2f})", "size": "sm", "color": "#FF9800", "align": "end", "flex": 5, "weight": "bold"}
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": "推進 1 張成本", "size": "sm", "color": "#888888", "flex": 3},
                        {"type": "text", "text": f"${one_lot_cost:,.0f}", "size": "sm", "color": "#111111", "align": "end", "flex": 5}
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": "下張推進差額", "size": "sm", "color": "#888888", "flex": 3},
                        {"type": "text", "text": f"${diff_for_next_lot:,.0f}", "size": "md", "color": "#F44336" if diff_for_next_lot > 0 else "#4CAF50", "align": "end", "flex": 5, "weight": "bold"}
                    ]
                },
                {"type": "separator", "margin": "lg"},
                {
                    "type": "text",
                    "text": "🚀 終極目標 (大水庫) 達標預估",
                    "size": "sm",
                    "weight": "bold",
                    "color": "#111111",
                    "margin": "md"
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": "尚需年配息差額", "size": "sm", "color": "#888888", "flex": 3},
                        {"type": "text", "text": f"${remaining_dividend_needed:,.0f}", "size": "sm", "color": "#111111", "align": "end", "flex": 5}
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": "需額外買進股數", "size": "sm", "color": "#888888", "flex": 3},
                        {"type": "text", "text": f"{additional_shares_needed:,.0f} 股 ({additional_shares_needed/1000:.2f} 張)", "size": "sm", "color": "#111111", "align": "end", "flex": 5, "weight": "bold"}
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": "預計投入總資金", "size": "sm", "color": "#888888", "flex": 3},
                        {"type": "text", "text": f"${total_cost_needed:,.0f}", "size": "sm", "color": "#111111", "align": "end", "flex": 5}
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": "預估達標時間", "size": "md", "color": "#888888", "flex": 3},
                        {"type": "text", "text": time_estimate_str, "size": "md", "color": "#4CAF50" if months_needed > 0 else "#2196F3", "align": "end", "flex": 5, "weight": "bold"}
                    ]
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "達標估算基於目前股價與配息歷史，且假設每月投入全額薪資預算",
                    "size": "xxs",
                    "color": "#AAAAAA",
                    "wrap": True,
                    "align": "center"
                }
            ]
        }
    }
    return flex_msg

def build_expense_flex_message(data: dict) -> dict:
    current_month = data.get("current_month", 1)
    this_month_expenses = data.get("this_month_expenses", 0.0)
    this_month_items = data.get("this_month_items", [])
    total_annual_expenses = data.get("total_annual_expenses", 0.0)
    upcoming_reminders = data.get("upcoming_reminders", [])
    
    # 本月開銷項目文字
    if this_month_items:
        this_month_text = "\n".join([f"• {e['item']}: ${e['cost']:,.0f}" for e in this_month_items])
    else:
        this_month_text = "無預計之固定開銷項目"
        
    # 未來三個月提醒內容
    reminder_contents = []
    for r in upcoming_reminders:
        reminder_contents.append({
            "type": "box",
            "layout": "horizontal",
            "margin": "sm",
            "contents": [
                {"type": "text", "text": f"{r['month']}月", "size": "sm", "color": "#FF5722", "flex": 2, "weight": "bold"},
                {"type": "text", "text": r["item"], "size": "sm", "color": "#111111", "flex": 5},
                {"type": "text", "text": f"${r['cost']:,.0f}", "size": "sm", "color": "#111111", "align": "end", "flex": 3, "weight": "bold"}
            ]
        })
        
    if not reminder_contents:
        reminder_contents.append({
            "type": "text",
            "text": "未來三個月無預計支出項目",
            "size": "sm",
            "color": "#888888",
            "align": "center",
            "margin": "md"
        })
        
    flex_msg = {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "📅 固定年度開銷檢查", "weight": "bold", "color": "#FFFFFF", "size": "lg"}
            ],
            "backgroundColor": "#E91E63"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": f"本月預計支出 ({current_month}月)", "size": "sm", "color": "#888888", "flex": 5},
                        {"type": "text", "text": f"${this_month_expenses:,.0f}", "size": "md", "color": "#E91E63" if this_month_expenses > 0 else "#4CAF50", "align": "end", "flex": 5, "weight": "bold"}
                    ]
                },
                {
                    "type": "text",
                    "text": this_month_text,
                    "size": "xs",
                    "color": "#555555",
                    "wrap": True,
                    "margin": "sm"
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "md",
                    "contents": [
                        {"type": "text", "text": "固定年度總開銷", "size": "sm", "color": "#888888", "flex": 5},
                        {"type": "text", "text": f"${total_annual_expenses:,.0f}", "size": "sm", "color": "#111111", "align": "end", "flex": 5, "weight": "bold"}
                    ]
                },
                {"type": "separator", "margin": "lg"},
                {
                    "type": "text",
                    "text": "🔔 未來三個月開銷提醒",
                    "size": "sm",
                    "weight": "bold",
                    "color": "#111111",
                    "margin": "md"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": reminder_contents
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "請確保帳戶餘額充足，以自動扣繳固定費用",
                    "size": "xxs",
                    "color": "#AAAAAA",
                    "align": "center"
                }
            ]
        }
    }
    return flex_msg

