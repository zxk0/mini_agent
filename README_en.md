# Mini Agent

> Minimalist Agent learning program — Tkinter GUI + customizable LLM + Skill plugin system.

## Features

- **GUI Interface** — Clean UI built with Tkinter
- **Customizable LLM** — base_url / api_key / model all configurable
- **Skill Plugin System** — Drop Python files into `skills/` directory, auto-loaded
- **Zero Dependencies** — Just `pip install openai`

## Install

```bash
pip install openai
```

## Configure

Edit `config.json`:

```json
{
  "base_url": "https://your-api-endpoint.com/v1",
  "api_key": "your-api-key",
  "model": "your-model-name",
  "system_prompt": "You are a helpful AI assistant."
}
```

## Run

```bash
python agent.py
```

## Skill Plugin Development

Create Python files in the `skills/` directory — the system auto-loads them.

See `skills/_template_skill.py` for the plugin template.

## Built-in Skills

| File | Function |
|------|----------|
| `calculator_skill.py` | Calculator |
| `text_stats_skill.py` | Text statistics |
| `time_skill.py` | Time query |
| `weather_skill.py` | Weather query |

## Project Structure

```
mini_agent/
├── README.md              # This file
├── README_en.md           # English version
├── agent.py               # Main program (Tkinter UI + Agent logic)
├── agent_lc.py            # LangChain version (optional)
├── config.json            # Config file (API URL / key)
├── requirements.txt       # Dependencies
├── requirements_lc.txt    # LangChain dependencies
└── skills/
    ├── _template_skill.py   # Plugin template
    ├── calculator_skill.py  # Calculator
    ├── text_stats_skill.py  # Text statistics
    ├── time_skill.py        # Time
    └── weather_skill.py      # Weather
```
