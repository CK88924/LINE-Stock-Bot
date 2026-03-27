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
              {"type": "text", "text": f"${price}", "size": "sm", "color": "#111111", "align": "end", "flex": 2, "weight": "bold"}
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
