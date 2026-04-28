"""
Skill: 计算器
支持基本数学表达式计算。
示例输入：2 + 3 * 4
"""
SKILL_NAME        = "🔢 计算器"
SKILL_DESCRIPTION = "计算用户输入的数学表达式（如 2+3*4）"


def run(user_input: str) -> str:
    try:
        # 只允许安全字符
        allowed = set("0123456789+-*/()., ")
        if not all(c in allowed for c in user_input):
            return "只支持基本数学运算（+  -  *  /  ()），请勿输入其他字符"
        result = eval(user_input, {"__builtins__": {}})
        return f"{user_input} = {result}"
    except Exception as e:
        return f"计算出错：{e}"
