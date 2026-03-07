"""
---
role: 告警弹窗定义
depends:
  - tkinter
exports:
  - AlertDialog
status: IMPLEMENTED
functions:
  - AlertDialog.open(message: str) -> str
---
"""

from __future__ import annotations

import tkinter as tk


class AlertDialog:
    def __init__(self, title: str = "告警") -> None:
        self.title = title

    def open(self, message: str) -> str:
        result = {"value": "ignored"}

        root = tk.Tk()
        root.title(self.title)
        root.attributes("-topmost", True)
        root.resizable(False, False)

        frame = tk.Frame(root, padx=16, pady=12)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text=message, justify="left", wraplength=360).pack(pady=(0, 12))

        button_frame = tk.Frame(frame)
        button_frame.pack(fill="x")

        def choose_bought() -> None:
            result["value"] = "bought"
            root.destroy()

        def choose_ignored() -> None:
            result["value"] = "ignored"
            root.destroy()

        tk.Button(button_frame, text="已买入", width=10, command=choose_bought).pack(side="left", padx=4)
        tk.Button(button_frame, text="忽略", width=10, command=choose_ignored).pack(side="left", padx=4)

        root.protocol("WM_DELETE_WINDOW", choose_ignored)
        root.mainloop()
        return result["value"]
