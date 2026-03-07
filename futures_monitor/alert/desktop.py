"""
---
role: 桌面告警
depends:
  - tkinter
exports:
  - DesktopAlertSender
status: IMPLEMENTED
functions:
  - DesktopAlertSender.send(title: str, message: str) -> str
---
"""

from __future__ import annotations

import sys
import threading

from futures_monitor.utils.logger import get_logger


class DesktopAlertSender:
    def __init__(self, alert_sound: bool = True) -> None:
        self.alert_sound = alert_sound
        self._logger = get_logger(self.__class__.__name__)

    def _play_sound(self) -> None:
        if not self.alert_sound:
            return

        if sys.platform.startswith("win"):
            try:
                import winsound

                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            except Exception as exc:
                self._logger.warning("Failed to play alert sound: %s", exc)

    def send(self, title: str, message: str) -> str:
        """
        Returns:
            "bought" | "ignored" | "fallback"
        """
        self._play_sound()

        try:
            import tkinter as tk
        except Exception as exc:
            self._logger.warning("tkinter unavailable, fallback to log alert: %s", exc)
            self._logger.warning("ALERT [%s] %s", title, message)
            return "fallback"

        result = {"choice": "ignored"}

        def _show_dialog() -> None:
            root = tk.Tk()
            root.title(title)
            root.attributes("-topmost", True)
            root.resizable(False, False)

            frame = tk.Frame(root, padx=16, pady=12)
            frame.pack(fill="both", expand=True)

            label = tk.Label(frame, text=message, justify="left", wraplength=360)
            label.pack(pady=(0, 12))

            btn_frame = tk.Frame(frame)
            btn_frame.pack(fill="x")

            def choose_bought() -> None:
                result["choice"] = "bought"
                root.destroy()

            def choose_ignored() -> None:
                result["choice"] = "ignored"
                root.destroy()

            tk.Button(btn_frame, text="已买入", width=10, command=choose_bought).pack(side="left", padx=4)
            tk.Button(btn_frame, text="忽略", width=10, command=choose_ignored).pack(side="left", padx=4)

            root.protocol("WM_DELETE_WINDOW", choose_ignored)
            root.mainloop()

        try:
            if threading.current_thread() is threading.main_thread():
                _show_dialog()
            else:
                self._logger.warning("Desktop dialog called from non-main thread, fallback to log")
                self._logger.warning("ALERT [%s] %s", title, message)
                return "fallback"
        except Exception as exc:
            self._logger.warning("Desktop alert failed, fallback to log alert: %s", exc)
            self._logger.warning("ALERT [%s] %s", title, message)
            return "fallback"

        return result["choice"]
