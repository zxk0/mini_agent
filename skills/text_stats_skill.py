"""
Skill: 文本统计
统计用户输入文本的字符数、词数、行数。
"""
SKILL_NAME        = "📊 文本统计"
SKILL_DESCRIPTION = "统计输入文本的字符数、词数、行数"


def run(user_input: str) -> str:
    chars = len(user_input)
    words = len(user_input.split())
    lines = user_input.count("\n") + 1
    return (
        f"📋 文本统计结果：\n"
        f"  字符数：{chars}\n"
        f"  词语数：{words}\n"
        f"  行  数：{lines}"
    )
