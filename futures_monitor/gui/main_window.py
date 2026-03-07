"""
---
role: 主窗口定义
depends:
  - tkinter
exports:
  - MainWindow
status: IMPLEMENTED
functions:
  - MainWindow.run() -> None
  - MainWindow.update_symbol_row(...) -> None
  - MainWindow.append_log(message: str) -> None
  - MainWindow.set_connection_status(status: str) -> None
---
"""

from __future__ import annotations

from datetime import datetime
import tkinter as tk
from tkinter import ttk
from typing import Callable


class MainWindow:
    def __init__(
        self,
        title: str = "Futures Monitor",
        geometry: str = "1280x760",
        take_profit_pct: float = 0.5,
        stop_loss_pct: float = 0.5,
        on_start: Callable[[list[str]], None] | None = None,
        on_stop: Callable[[], None] | None = None,
        on_mark_bought: Callable[[str], None] | None = None,
    ) -> None:
        self.on_start = on_start
        self.on_stop = on_stop
        self.on_mark_bought = on_mark_bought

        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry(geometry)

        self._symbol_to_item: dict[str, str] = {}

        self._running_value = tk.StringVar(value="已停止")
        self._connection_value = tk.StringVar(value="未连接")
        self._clock_value = tk.StringVar(value="--:--:--")

        self._build_layout(take_profit_pct=take_profit_pct, stop_loss_pct=stop_loss_pct)
        self._tick_clock()

    def _build_layout(self, take_profit_pct: float, stop_loss_pct: float) -> None:
        self.root.rowconfigure(2, weight=1)
        self.root.rowconfigure(3, weight=1)
        self.root.columnconfigure(1, weight=1)

        status_bar = ttk.Frame(self.root, padding=(10, 8))
        status_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        status_bar.columnconfigure(0, weight=1)

        ttk.Label(status_bar, text="运行状态:").grid(row=0, column=0, sticky="w")
        self.running_label = ttk.Label(status_bar, textvariable=self._running_value)
        self.running_label.grid(row=0, column=1, padx=(4, 16), sticky="w")

        ttk.Label(status_bar, text="连接状态:").grid(row=0, column=2, sticky="w")
        self.connection_label = ttk.Label(status_bar, textvariable=self._connection_value)
        self.connection_label.grid(row=0, column=3, padx=(4, 16), sticky="w")

        ttk.Label(status_bar, text="当前时间:").grid(row=0, column=4, sticky="w")
        ttk.Label(status_bar, textvariable=self._clock_value).grid(row=0, column=5, padx=(4, 0), sticky="w")

        left_panel = ttk.LabelFrame(self.root, text="配置", padding=10)
        left_panel.grid(row=1, column=0, rowspan=2, sticky="nsew", padx=(10, 6), pady=(0, 8))
        left_panel.rowconfigure(1, weight=1)
        left_panel.columnconfigure(0, weight=1)

        ttk.Label(left_panel, text="监控品种（每行：代码 可后接说明；ALL=全部品种）").grid(row=0, column=0, sticky="w")
        self.symbols_text = tk.Text(left_panel, height=12, width=24)
        self.symbols_text.grid(row=1, column=0, sticky="nsew", pady=(6, 10))

        ratio_frame = ttk.Frame(left_panel)
        ratio_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        ttk.Label(ratio_frame, text=f"止盈比例: {take_profit_pct:.2f}").grid(row=0, column=0, sticky="w")
        ttk.Label(ratio_frame, text=f"止损比例: {stop_loss_pct:.2f}").grid(row=1, column=0, sticky="w")

        btn_frame = ttk.Frame(left_panel)
        btn_frame.grid(row=3, column=0, sticky="ew")
        self.start_button = ttk.Button(btn_frame, text="启动监控", command=self._handle_start)
        self.start_button.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.stop_button = ttk.Button(btn_frame, text="停止监控", command=self._handle_stop)
        self.stop_button.grid(row=0, column=1, sticky="ew")
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)

        center_panel = ttk.LabelFrame(self.root, text="监控总览", padding=8)
        center_panel.grid(row=1, column=1, sticky="nsew", padx=(6, 10), pady=(0, 8))
        center_panel.rowconfigure(0, weight=1)
        center_panel.columnconfigure(0, weight=1)

        columns = (
            "symbol",
            "state",
            "latest",
            "day_hl",
            "breakout",
            "tp_sl",
            "last_event",
        )
        self.tree = ttk.Treeview(center_panel, columns=columns, show="headings", height=12)
        self.tree.grid(row=0, column=0, sticky="nsew")

        self.tree.heading("symbol", text="品种")
        self.tree.heading("state", text="状态")
        self.tree.heading("latest", text="最新价")
        self.tree.heading("day_hl", text="当日高/低")
        self.tree.heading("breakout", text="突破价")
        self.tree.heading("tp_sl", text="止盈/止损")
        self.tree.heading("last_event", text="最后事件")

        self.tree.column("symbol", width=130, anchor="w")
        self.tree.column("state", width=160, anchor="center")
        self.tree.column("latest", width=100, anchor="e")
        self.tree.column("day_hl", width=170, anchor="center")
        self.tree.column("breakout", width=100, anchor="e")
        self.tree.column("tp_sl", width=200, anchor="center")
        self.tree.column("last_event", width=300, anchor="w")

        tree_scroll = ttk.Scrollbar(center_panel, orient="vertical", command=self.tree.yview)
        tree_scroll.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=tree_scroll.set)

        actions = ttk.Frame(center_panel)
        actions.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        self.mark_bought_button = ttk.Button(actions, text="标记已买入", command=self._handle_mark_bought)
        self.mark_bought_button.grid(row=0, column=0, sticky="w")

        log_panel = ttk.LabelFrame(self.root, text="日志", padding=8)
        log_panel.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=10, pady=(0, 10))
        log_panel.rowconfigure(0, weight=1)
        log_panel.columnconfigure(0, weight=1)

        self.log_text = tk.Text(log_panel, height=9, state="disabled")
        self.log_text.grid(row=0, column=0, sticky="nsew")
        log_scroll = ttk.Scrollbar(log_panel, orient="vertical", command=self.log_text.yview)
        log_scroll.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=log_scroll.set)

    def _tick_clock(self) -> None:
        self._clock_value.set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.root.after(1000, self._tick_clock)

    def _parse_symbols(self) -> list[str]:
        content = self.symbols_text.get("1.0", tk.END)
        symbols: list[str] = []
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            symbols.append(stripped.split(maxsplit=1)[0])
        return symbols

    def set_symbols(self, symbols: list[str]) -> None:
        self.symbols_text.delete("1.0", tk.END)
        if symbols:
            self.symbols_text.insert("1.0", "\n".join(symbols))

    def _handle_start(self) -> None:
        if self.on_start:
            self.on_start(self._parse_symbols())

    def _handle_stop(self) -> None:
        if self.on_stop:
            self.on_stop()

    def _handle_mark_bought(self) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], "values")
        if not values:
            return
        symbol = str(values[0])
        if self.on_mark_bought:
            self.on_mark_bought(symbol)

    def set_running_status(self, running: bool) -> None:
        self._running_value.set("监控中" if running else "已停止")

    def set_connection_status(self, status: str) -> None:
        self._connection_value.set(status)

    def update_symbol_row(
        self,
        symbol: str,
        state: str,
        latest_price: float | None,
        day_high: float | None,
        day_low: float | None,
        breakout_price: float | None,
        take_profit_price: float | None,
        stop_loss_price: float | None,
        last_event: str,
    ) -> None:
        latest = "-" if latest_price is None else f"{latest_price:.2f}"
        day_hl = "-" if day_high is None or day_low is None else f"{day_high:.2f} / {day_low:.2f}"
        breakout = "-" if breakout_price is None else f"{breakout_price:.2f}"
        tp_sl = "-" if take_profit_price is None or stop_loss_price is None else f"{take_profit_price:.2f} / {stop_loss_price:.2f}"

        values = (symbol, state, latest, day_hl, breakout, tp_sl, last_event)

        item_id = self._symbol_to_item.get(symbol)
        if item_id:
            self.tree.item(item_id, values=values)
            return

        item_id = self.tree.insert("", tk.END, values=values)
        self._symbol_to_item[symbol] = item_id

    def append_log(self, message: str) -> None:
        now = datetime.now().strftime("%H:%M:%S")
        line = f"[{now}] {message}\n"
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, line)
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")

    def run(self) -> None:
        self.root.mainloop()
