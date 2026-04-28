# Mini Agent

> 最简化 Agent 学习程序 — Tkinter 图形界面 + 自定义 LLM + Skill 插件系统

## 核心特性

- **图形界面** - Tkinter 实现的简洁 UI
- **自定义 LLM** - base_url / api_key / model 均可配置
- **Skill 插件系统** - 将 Python 文件放入 `skills/` 目录自动加载
- **零依赖** - 仅需 `pip install openai`

## 安装

```bash
pip install openai
```

## 配置

编辑 `config.json`：

```json
{
  "base_url": "https://your-api-endpoint.com/v1",
  "api_key": "your-api-key",
  "model": "your-model-name",
  "system_prompt": "你是一个有用的 AI 助手。"
}
```

## 运行

```bash
python agent.py
```

## Skill 插件开发

在 `skills/` 目录下创建 Python 文件，系统会自动加载。

示例模板参考 `skills/_template_skill.py`。

## 内置 Skill

| 文件 | 功能 |
|------|------|
| `calculator_skill.py` | 计算器 |
| `text_stats_skill.py` | 文本统计 |
| `time_skill.py` | 时间查询 |
| `weather_skill.py` | 天气查询 |

## 项目结构

```
mini_agent/
├── agent.py              # 主程序（Tkinter UI + Agent 逻辑）
├── agent_lc.py           # LangChain 版本（可选）
├── config.json           # 配置文件（API 地址/密钥）
├── requirements.txt      # 依赖
├── requirements_lc.txt   # LangChain 依赖
└── skills/
    ├── _template_skill.py  # 插件模板
    ├── calculator_skill.py # 计算器
    ├── text_stats_skill.py # 文本统计
    ├── time_skill.py       # 时间
    └── weather_skill.py    # 天气
```