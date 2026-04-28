"""
Mini Agent - 最简化 Agent 学习程序
=================================
功能：
  1. 图形交互界面（Tkinter）
  2. 自定义大模型（base_url / api_key / model 可配置）
  3. Skill 插件系统（将 Python 文件放入 skills/ 目录自动加载）

依赖：
  pip install openai
  Python 内置：tkinter, importlib, json, os
"""

# 压制 Python 3.14 + Pydantic v1 兼容性警告（不影响功能）
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
from openai import OpenAI

# ─────────────────────────────────────────────
# 配置文件路径
# ─────────────────────────────────────────────
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")
SKILLS_DIR  = os.path.join(os.path.dirname(__file__), "skills")


# ─────────────────────────────────────────────
# 配置管理
# ─────────────────────────────────────────────
DEFAULT_CONFIG = {
    "base_url": "https://api.longcat.chat/openai",
    "api_key":  "ak_24o1uw5WR5tI2kq8U84f85ao07T1t",
    "model":    "LongCat-Flash-Lite",
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


# ─────────────────────────────────────────────
# Skill 插件系统
# ─────────────────────────────────────────────
def discover_skills() -> dict[str, dict]:
    """扫描 skills/ 目录，返回 {skill_name: {"module": mod, "meta": meta}} 字典"""
    skills = {}
    os.makedirs(SKILLS_DIR, exist_ok=True)
    for fname in os.listdir(SKILLS_DIR):
        if fname.endswith(".py") and not fname.startswith("_"):
            skill_name = fname[:-3]
            path = os.path.join(SKILLS_DIR, fname)
            spec = importlib.util.spec_from_file_location(skill_name, path)
            mod  = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(mod)
                meta = {
                    "name":        getattr(mod, "SKILL_NAME",        skill_name),
                    "description": getattr(mod, "SKILL_DESCRIPTION", "无描述"),
                }
                skills[skill_name] = {"module": mod, "meta": meta}
            except Exception as e:
                print(f"[Skill] 加载 {fname} 失败: {e}")
    return skills

def run_skill(skill_key: str, skills: dict, user_input: str) -> str:
    """执行指定 skill 的 run(input) 函数，返回字符串结果"""
    if skill_key not in skills:
        return f"[错误] 未找到 skill: {skill_key}"
    mod = skills[skill_key]["module"]
    if not hasattr(mod, "run"):
        return f"[错误] skill '{skill_key}' 中没有 run(input) 函数"
    try:
        return str(mod.run(user_input))
    except Exception as e:
        return f"[Skill 执行错误] {e}"


# ─────────────────────────────────────────────
# LLM 调用
# ─────────────────────────────────────────────
def call_llm(cfg: dict, messages: list) -> str:
    """调用 OpenAI 兼容接口，返回助手回复文本"""
    client = OpenAI(base_url=cfg["base_url"], api_key=cfg["api_key"])
    resp = client.chat.completions.create(
        model=cfg["model"],
        messages=messages,
    )
    return resp.choices[0].message.content


# ─────────────────────────────────────────────
# 主界面
# ─────────────────────────────────────────────
class AgentApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Mini Agent 🤖")
        self.geometry("900x680")
        self.configure(bg="#1e1e2e")
        self.resizable(True, True)

        self.cfg    = load_config()
        self.skills = discover_skills()
        self.history: list[dict] = []  # 对话历史

        self._build_ui()

    # ── 构建 UI ───────────────────────────────
    def _build_ui(self):
        # 顶部工具栏
        toolbar = tk.Frame(self, bg="#313244", pady=6)
        toolbar.pack(fill=tk.X)

        tk.Label(toolbar, text="🤖 Mini Agent", bg="#313244",
                 fg="#cdd6f4", font=("Arial", 14, "bold")).pack(side=tk.LEFT, padx=12)

        tk.Button(toolbar, text="⚙ 模型设置", command=self._open_model_settings,
                  bg="#45475a", fg="#cdd6f4", relief=tk.FLAT,
                  padx=8, pady=4).pack(side=tk.RIGHT, padx=6)

        tk.Button(toolbar, text="🔌 Skill 管理", command=self._open_skill_manager,
                  bg="#45475a", fg="#cdd6f4", relief=tk.FLAT,
                  padx=8, pady=4).pack(side=tk.RIGHT, padx=6)

        tk.Button(toolbar, text="🗑 清空对话", command=self._clear_history,
                  bg="#45475a", fg="#cdd6f4", relief=tk.FLAT,
                  padx=8, pady=4).pack(side=tk.RIGHT, padx=6)

        # 主区：左边对话，右边 skill 列表
        main = tk.Frame(self, bg="#1e1e2e")
        main.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # 对话区
        chat_frame = tk.Frame(main, bg="#1e1e2e")
        chat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.chat_display = scrolledtext.ScrolledText(
            chat_frame, wrap=tk.WORD, state=tk.DISABLED,
            bg="#181825", fg="#cdd6f4", insertbackground="#cdd6f4",
            font=("Consolas", 11), relief=tk.FLAT, padx=10, pady=10,
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        # 配置消息颜色标签
        self.chat_display.tag_config("user",      foreground="#89b4fa")
        self.chat_display.tag_config("assistant", foreground="#a6e3a1")
        self.chat_display.tag_config("skill",     foreground="#f9e2af")
        self.chat_display.tag_config("system",    foreground="#6c7086")

        # 右边 skill 列表
        skill_frame = tk.Frame(main, bg="#181825", width=180)
        skill_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(8, 0))
        skill_frame.pack_propagate(False)

        tk.Label(skill_frame, text="🔌 已加载 Skill",
                 bg="#181825", fg="#cdd6f4",
                 font=("Arial", 10, "bold")).pack(pady=8)

        self.skill_listbox = tk.Listbox(
            skill_frame, bg="#181825", fg="#f9e2af",
            selectbackground="#313244", relief=tk.FLAT,
            font=("Consolas", 10), activestyle="none",
        )
        self.skill_listbox.pack(fill=tk.BOTH, expand=True, padx=4)
        self._refresh_skill_list()

        tk.Button(skill_frame, text="▶ 执行选中 Skill",
                  command=self._run_selected_skill,
                  bg="#313244", fg="#f9e2af", relief=tk.FLAT, pady=4,
                  ).pack(fill=tk.X, padx=4, pady=6)

        # 底部输入区
        input_frame = tk.Frame(self, bg="#313244", pady=8)
        input_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=8, pady=(0, 8))

        self.input_var = tk.StringVar()
        self.input_entry = tk.Entry(
            input_frame, textvariable=self.input_var,
            bg="#45475a", fg="#cdd6f4", insertbackground="#cdd6f4",
            font=("Consolas", 12), relief=tk.FLAT,
        )
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), ipady=6)
        self.input_entry.bind("<Return>", lambda e: self._send_message())
        self.input_entry.focus()

        self.send_btn = tk.Button(
            input_frame, text="发送 ↵", command=self._send_message,
            bg="#89b4fa", fg="#1e1e2e", relief=tk.FLAT,
            font=("Arial", 11, "bold"), padx=14, pady=6,
        )
        self.send_btn.pack(side=tk.RIGHT)

        self._append_chat("system", "=== Mini Agent 已就绪 ===\n"
                          "在下方输入问题直接与 LLM 对话，或在右侧选择 Skill 执行。\n")

    # ── 对话逻辑 ─────────────────────────────
    def _send_message(self):
        text = self.input_var.get().strip()
        if not text:
            return
        self.input_var.set("")
        self.send_btn.config(state=tk.DISABLED)
        self._append_chat("user", f"你：{text}\n")
        self.history.append({"role": "user", "content": text})
        threading.Thread(target=self._llm_thread, args=(text,), daemon=True).start()

    def _llm_thread(self, _text):
        try:
            messages = [{"role": "system", "content": self.cfg["system_prompt"]}] + self.history
            reply = call_llm(self.cfg, messages)
            self.history.append({"role": "assistant", "content": reply})
            self.after(0, self._append_chat, "assistant", f"AI：{reply}\n")
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
        self.history.clear()
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete("1.0", tk.END)
        self.chat_display.config(state=tk.DISABLED)
        self._append_chat("system", "=== 对话已清空 ===\n")

    # ── Skill 管理 ────────────────────────────
    def _refresh_skill_list(self):
        self.skill_listbox.delete(0, tk.END)
        if not self.skills:
            self.skill_listbox.insert(tk.END, "（暂无 Skill）")
        for key, info in self.skills.items():
            self.skill_listbox.insert(tk.END, info["meta"]["name"])

    def _run_selected_skill(self):
        sel = self.skill_listbox.curselection()
        if not sel:
            messagebox.showinfo("提示", "请先在右侧列表中选择一个 Skill")
            return
        idx      = sel[0]
        key_list = list(self.skills.keys())
        if idx >= len(key_list):
            return
        skill_key  = key_list[idx]
        user_input = self.input_var.get().strip() or "(无输入)"
        self._append_chat("user", f"你（via Skill）：{user_input}\n")
        self.input_var.set("")

        def _thread():
            result = run_skill(skill_key, self.skills, user_input)
            self.after(0, self._append_chat, "skill",
                       f"[Skill: {self.skills[skill_key]['meta']['name']}]\n{result}\n")

        threading.Thread(target=_thread, daemon=True).start()

    def _open_skill_manager(self):
        win = tk.Toplevel(self)
        win.title("Skill 管理")
        win.geometry("500x420")
        win.configure(bg="#1e1e2e")

        tk.Label(win, text="已加载 Skill 列表",
                 bg="#1e1e2e", fg="#cdd6f4",
                 font=("Arial", 12, "bold")).pack(pady=10)

        frame = tk.Frame(win, bg="#181825")
        frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)

        cols = ("名称", "描述", "模块")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=10)
        for c in cols:
            tree.heading(c, text=c)
        tree.column("名称", width=100)
        tree.column("描述", width=240)
        tree.column("模块", width=100)
        tree.pack(fill=tk.BOTH, expand=True)

        for key, info in self.skills.items():
            tree.insert("", tk.END,
                        values=(info["meta"]["name"], info["meta"]["description"], key))

        def reload():
            self.skills = discover_skills()
            self._refresh_skill_list()
            for row in tree.get_children():
                tree.delete(row)
            for key, info in self.skills.items():
                tree.insert("", tk.END,
                            values=(info["meta"]["name"], info["meta"]["description"], key))

        btn_row = tk.Frame(win, bg="#1e1e2e")
        btn_row.pack(fill=tk.X, padx=12, pady=8)
        tk.Button(btn_row, text="🔄 重新扫描 Skill",
                  command=reload,
                  bg="#313244", fg="#cdd6f4", relief=tk.FLAT, padx=10, pady=4,
                  ).pack(side=tk.LEFT)

        hint = f"Skill 目录：{SKILLS_DIR}"
        tk.Label(win, text=hint, bg="#1e1e2e", fg="#6c7086",
                 font=("Consolas", 9)).pack(pady=6)

    # ── 模型设置 ──────────────────────────────
    def _open_model_settings(self):
        win = tk.Toplevel(self)
        win.title("模型设置")
        win.geometry("480x340")
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
            self._append_chat("system", "[系统] 模型配置已保存\n")
            win.destroy()

        tk.Button(win, text="💾 保存", command=save_and_close,
                  bg="#89b4fa", fg="#1e1e2e", relief=tk.FLAT,
                  font=("Arial", 11, "bold"), padx=16, pady=6,
                  ).grid(row=len(fields), column=0, columnspan=2, pady=16)


# ─────────────────────────────────────────────
# 入口
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = AgentApp()
    app.mainloop()
