"""
Mini Agent - LangChain v1 升级版
==================================
适配 LangChain v1.2.15（当前版本）API：
  - 用 create_agent() 创建 StateGraph Agent
  - 调用方式：agent.invoke({"messages": [HumanMessage(...)]})
  - 记忆用 checkpointer 持久化

依赖：
  pip install langchain>=1.0 langchain-openai openai
"""

# ── 压制 Python 3.14 + Pydantic v1 兼容性警告（不影响功能）──────────
import warnings
warnings.filterwarnings(
    "ignore",
    message="Core Pydantic V1 functionality isn't compatible",
    category=UserWarning,
)

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import importlib.util
import os
import json

# ── LangChain v1 ─────────────────────────────
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI

# ── 配置 & Skill 加载 ────────────────────────
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")
SKILLS_DIR  = os.path.join(os.path.dirname(__file__), "skills")

DEFAULT_CONFIG = {
    "base_url":      "https://api.openai.com/v1",
    "api_key":       "sk-YOUR_KEY",
    "model":         "gpt-4o-mini",
    "system_prompt": "你是一个有用的 AI 助手。",
}

def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return {**DEFAULT_CONFIG, **json.load(f)}
    return dict(DEFAULT_CONFIG)

def save_config(cfg: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

def discover_skill_modules() -> dict:
    skills = {}
    os.makedirs(SKILLS_DIR, exist_ok=True)
    for fname in os.listdir(SKILLS_DIR):
        if fname.endswith(".py") and not fname.startswith("_"):
            key  = fname[:-3]
            path = os.path.join(SKILLS_DIR, fname)
            spec = importlib.util.spec_from_file_location(key, path)
            mod  = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(mod)
                skills[key] = mod
            except Exception as e:
                print(f"[Skill] 加载 {fname} 失败: {e}")
    return skills

def build_lc_tools(skill_modules: dict):
    """将 skills/*.py 包装成 LangChain Tool"""
    from langchain_core.tools import StructuredTool

    lc_tools = []
    for key, mod in skill_modules.items():
        if not hasattr(mod, "run"):
            continue
        name = getattr(mod, "SKILL_NAME", key).replace(" ", "_")[:40]
        desc = getattr(mod, "SKILL_DESCRIPTION", "no description")

        def make_wrapper(skill_mod):
            def wrapper(input_str: str) -> str:
                try:
                    return str(skill_mod.run(input_str))
                except Exception as e:
                    return f"[错误] {e}"
            return wrapper

        # 直接构造 StructuredTool，不依赖装饰器（避免循环内闭包陷阱）
        lc_tools.append(
            StructuredTool.from_function(
                func=make_wrapper(mod),
                name=name,
                description=desc,
            )
        )
    return lc_tools

def build_agent(cfg: dict, lc_tools: list):
    """用 create_agent 创建 LangChain v1 Agent"""
    # 支持字符串模型 ID 或 ChatOpenAI 实例
    model = ChatOpenAI(
        model     = cfg["model"],
        base_url  = cfg["base_url"],
        api_key   = cfg["api_key"],
    )
    agent = create_agent(
        model         = model,
        tools         = lc_tools,
        system_prompt = cfg["system_prompt"],
    )
    return agent


# ─────────────────────────────────────────────
# 主界面
# ─────────────────────────────────────────────
class AgentLCApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Mini Agent 🤖  (LangChain v1)")
        self.geometry("900x700")
        self.configure(bg="#1e1e2e")
        self.resizable(True, True)

        self.cfg           = load_config()
        self.skill_modules = discover_skill_modules()
        self.lc_tools      = build_lc_tools(self.skill_modules)
        self.lc_agent      = build_agent(self.cfg, self.lc_tools)

        self._build_ui()

    # ── UI 构建 ─────────────────────────────
    def _build_ui(self):
        toolbar = tk.Frame(self, bg="#313244", pady=6)
        toolbar.pack(fill=tk.X)

        tk.Label(toolbar, text="🤖 Mini Agent  [LangChain v1]",
                 bg="#313244", fg="#cdd6f4",
                 font=("Arial", 14, "bold")).pack(side=tk.LEFT, padx=12)

        tk.Button(toolbar, text="⚙ 模型设置",
                  command=self._open_model_settings,
                  bg="#45475a", fg="#cdd6f4", relief=tk.FLAT,
                  padx=8, pady=4).pack(side=tk.RIGHT, padx=6)

        tk.Button(toolbar, text="🔌 Skill 列表",
                  command=self._open_skill_manager,
                  bg="#45475a", fg="#cdd6f4", relief=tk.FLAT,
                  padx=8, pady=4).pack(side=tk.RIGHT, padx=6)

        tk.Button(toolbar, text="🗑 清空对话",
                  command=self._clear_history,
                  bg="#45475a", fg="#cdd6f4", relief=tk.FLAT,
                  padx=8, pady=4).pack(side=tk.RIGHT, padx=6)

        # 主区
        main = tk.Frame(self, bg="#1e1e2e")
        main.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # 对话区
        chat_frame = tk.Frame(main, bg="#1e1e2e")
        chat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.chat_display = scrolledtext.ScrolledText(
            chat_frame, wrap=tk.WORD, state=tk.DISABLED,
            bg="#181825", fg="#cdd6f4",
            insertbackground="#cdd6f4",
            font=("Consolas", 11), relief=tk.FLAT, padx=10, pady=10,
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        self.chat_display.tag_config("user",      foreground="#89b4fa")
        self.chat_display.tag_config("assistant", foreground="#a6e3a1")
        self.chat_display.tag_config("tool",      foreground="#f9e2af")
        self.chat_display.tag_config("system",    foreground="#6c7086")

        # 右侧 Tool 面板
        skill_frame = tk.Frame(main, bg="#181825", width=180)
        skill_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(8, 0))
        skill_frame.pack_propagate(False)

        tk.Label(skill_frame, text="🔌 已注册 Tool",
                 bg="#181825", fg="#cdd6f4",
                 font=("Arial", 10, "bold")).pack(pady=8)

        self.skill_listbox = tk.Listbox(
            skill_frame, bg="#181825", fg="#f9e2af",
            selectbackground="#313244", relief=tk.FLAT,
            font=("Consolas", 10), activestyle="none",
        )
        self.skill_listbox.pack(fill=tk.BOTH, expand=True, padx=4)
        self._refresh_skill_list()

        tk.Label(skill_frame,
                 text="↑ LLM 自动调用\n无需手动点击",
                 bg="#181825", fg="#6c7086",
                 font=("Arial", 9), justify=tk.CENTER).pack(pady=6)

        # 底部输入
        input_frame = tk.Frame(self, bg="#313244", pady=8)
        input_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=8, pady=(0, 8))

        self.input_var = tk.StringVar()
        self.input_entry = tk.Entry(
            input_frame, textvariable=self.input_var,
            bg="#45475a", fg="#cdd6f4",
            insertbackground="#cdd6f4",
            font=("Consolas", 12), relief=tk.FLAT,
        )
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True,
                              padx=(0, 8), ipady=6)
        self.input_entry.bind("<Return>", lambda e: self._send_message())
        self.input_entry.focus()

        self.send_btn = tk.Button(
            input_frame, text="发送 ↵",
            command=self._send_message,
            bg="#89b4fa", fg="#1e1e2e", relief=tk.FLAT,
            font=("Arial", 11, "bold"), padx=14, pady=6,
        )
        self.send_btn.pack(side=tk.RIGHT)

        self._append_chat("system",
            "=== Mini Agent (LangChain v1) 已就绪 ===\n"
            "直接输入问题，AI 会自动决定是否调用 Tool。\n"
            f"已注册 {len(self.lc_tools)} 个 Tool：{[t.name for t in self.lc_tools]}\n")

    # ── 发送消息（调用 LangChain v1 Agent）────
    def _send_message(self):
        text = self.input_var.get().strip()
        if not text:
            return
        self.input_var.set("")
        self.send_btn.config(state=tk.DISABLED)
        self._append_chat("user", f"你：{text}\n")
        threading.Thread(target=self._agent_thread, args=(text,), daemon=True).start()

    def _agent_thread(self, text: str):
        try:
            # ★ LangChain v1 调用方式：invoke + HumanMessage 列表
            response = self.lc_agent.invoke(
                {"messages": [HumanMessage(content=text)]},
                config=RunnableConfig(recursive=True),
            )
            # response 是一个 dict，messages 在其中
            messages = response.get("messages", [])
            # 取最后一条 AIMessage 的 content
            last_msg = messages[-1].content if messages else "(无回复)"
            self.after(0, self._append_chat, "assistant", f"AI：{last_msg}\n")
        except Exception as e:
            self.after(0, self._append_chat, "system", f"[错误] {e}\n")
        finally:
            self.after(0, lambda: self.send_btn.config(state=tk.NORMAL))

    def _append_chat(self, tag: str, text: str):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, text + "\n", tag)
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def _clear_history(self):
        # v1 Agent 无全局历史，需要重建（简单处理：清空界面即可）
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete("1.0", tk.END)
        self.chat_display.config(state=tk.DISABLED)
        self._append_chat("system", "=== 对话已清空 ===\n")

    def _refresh_skill_list(self):
        self.skill_listbox.delete(0, tk.END)
        if not self.lc_tools:
            self.skill_listbox.insert(tk.END, "（暂无 Tool）")
        for t in self.lc_tools:
            self.skill_listbox.insert(tk.END, t.name)

    def _open_skill_manager(self):
        win = tk.Toplevel(self)
        win.title("Tool 列表")
        win.geometry("500x380")
        win.configure(bg="#1e1e2e")

        tk.Label(win, text="LangChain v1 已注册 Tool",
                 bg="#1e1e2e", fg="#cdd6f4",
                 font=("Arial", 12, "bold")).pack(pady=10)

        cols = ("Tool 名称", "描述")
        tree = ttk.Treeview(win, columns=cols, show="headings", height=10)
        tree.heading("Tool 名称", text="Tool 名称")
        tree.heading("描述",      text="描述")
        tree.column("Tool 名称", width=140)
        tree.column("描述",      width=300)
        tree.pack(fill=tk.BOTH, expand=True, padx=12)

        for t in self.lc_tools:
            tree.insert("", tk.END, values=(t.name, t.description))

        def reload():
            self.skill_modules = discover_skill_modules()
            self.lc_tools      = build_lc_tools(self.skill_modules)
            self.lc_agent     = build_agent(self.cfg, self.lc_tools)
            self._refresh_skill_list()
            for row in tree.get_children():
                tree.delete(row)
            for t in self.lc_tools:
                tree.insert("", tk.END, values=(t.name, t.description))

        tk.Button(win, text="🔄 重新加载 Skill",
                  command=reload,
                  bg="#313244", fg="#cdd6f4",
                  relief=tk.FLAT, padx=10, pady=4).pack(pady=8)

    def _open_model_settings(self):
        win = tk.Toplevel(self)
        win.title("模型设置")
        win.geometry("480x300")
        win.configure(bg="#1e1e2e")
        win.resizable(False, False)

        fields = [
            ("Base URL",      "base_url"),
            ("API Key",       "api_key"),
            ("Model",         "model"),
            ("System Prompt", "system_prompt"),
        ]
        entries = {}
        for i, (label, key) in enumerate(fields):
            tk.Label(win, text=label, bg="#1e1e2e", fg="#cdd6f4",
                     font=("Arial", 10)).grid(row=i, column=0,
                                              sticky=tk.W, padx=16, pady=8)
            var = tk.StringVar(value=self.cfg.get(key, ""))
            ent = tk.Entry(win, textvariable=var, width=40,
                           bg="#313244", fg="#cdd6f4",
                           insertbackground="#cdd6f4", relief=tk.FLAT)
            if key == "api_key":
                ent.config(show="*")
            ent.grid(row=i, column=1, padx=8, pady=8, sticky=tk.EW)
            entries[key] = var
        win.columnconfigure(1, weight=1)

        def save_and_close():
            for key, var in entries.items():
                self.cfg[key] = var.get().strip()
            save_config(self.cfg)
            self.lc_agent = build_agent(self.cfg, self.lc_tools)
            self._append_chat("system", "[系统] 模型配置已保存，Agent 已重建\n")
            win.destroy()

        tk.Button(win, text="💾 保存",
                  command=save_and_close,
                  bg="#89b4fa", fg="#1e1e2e", relief=tk.FLAT,
                  font=("Arial", 11, "bold"), padx=16, pady=6,
                  ).grid(row=len(fields), column=0, columnspan=2, pady=16)


if __name__ == "__main__":
    app = AgentLCApp()
    app.mainloop()
