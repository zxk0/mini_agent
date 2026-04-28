"""
Skill: 时间查询
当用户想知道当前时间/日期时使用此 Skill。
"""
from datetime import datetime

SKILL_NAME        = "⏰ 当前时间"
SKILL_DESCRIPTION = "返回当前系统日期和时间"


def run(user_input: str) -> str:
    now = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
    return f"现在是 {now}"
