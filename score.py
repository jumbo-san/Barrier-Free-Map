def judge_reliability(投稿数):
    """
    投稿数で信頼性を判断する
       ３件以上 → 確認済み
       ２件以下 → 確認中
    """
    if 投稿数 >= 3:
        return "confirmed"
    else:
        return "checking"

def get_status_icon(status):
    """信頼性ステータスアイコンに変換する"""
    icons = {
        "confirmed": "✅確認済み",
        "checking": "🔄確認中",  
    }
    return icons.get(status, "🔄確認中")