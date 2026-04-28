"""
Skill 开发模板
==============
复制此文件到 skills/ 目录，修改以下三项即可完成一个新 Skill：
  1. SKILL_NAME        - 显示在界面上的名称（可含 emoji）
  2. SKILL_DESCRIPTION - 功能说明
  3. run(user_input)   - 核心逻辑，接收用户输入字符串，返回结果字符串

可选：在 run() 中调用外部 API、操作文件、执行系统命令……
"""

SKILL_NAME        = "🆕 我的新 Skill"
SKILL_DESCRIPTION = "在这里填写功能描述"


def run(user_input: str) -> str:
    # ↓ 在这里写你的逻辑
    return f"你输入了：{user_input}（这是模板，请修改 run() 函数）"
