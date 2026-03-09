"""
---
role: Encapsulate monitor domain operations for API consumption.
depends:
  - futures_monitor.server.schemas.MonitorStatus
  - futures_monitor.server.schemas.SymbolRow
  - futures_monitor.config.AppConfig
  - futures_monitor.config.load_config
  - futures_monitor.config.resolve_runtime_config_path
  - futures_monitor.market.MarketDataProvider
  - futures_monitor.strategy.breakout.BreakoutStrategy
  - futures_monitor.strategy.breakout.Kline
  - futures_monitor.strategy.state_machine.StrategyStateMachine
  - futures_monitor.strategy.state_machine.BREAKOUT_DETECTED
  - futures_monitor.strategy.state_machine.HOLDING
  - futures_monitor.strategy.state_machine.MONITORING
  - futures_monitor.data.storage.Storage
  - futures_monitor.alert.desktop.DesktopAlertSender
  - futures_monitor.alert.sms.SmsAlertSender
  - futures_monitor.utils.logger.get_logger
  - futures_monitor.utils.timeutil.is_after_1445
  - futures_monitor.utils.timeutil.is_after_1455
exports:
  - MonitorService
status: IMPLEMENTED
functions:
  - MonitorService.start(symbols: list[str], selection_mode: str | None = None, selection_exchanges: list[str] | None = None) -> dict
  - MonitorService.stop() -> dict
  - MonitorService.get_status() -> MonitorStatus
  - MonitorService.mark_bought(symbol: str) -> dict
  - MonitorService.set_hub(hub: ConnectionHub) -> None
  - MonitorService.reload_config(config: AppConfig | None = None) -> AppConfig
---
"""

from __future__ import annotations

import asyncio
import threading
import time
from datetime import datetime
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from futures_monitor.alert.desktop import DesktopAlertSender
from futures_monitor.alert.sms import SmsAlertSender
from futures_monitor.config import AppConfig, ensure_runtime_config, get_fixed_monitor_pool, load_config, resolve_runtime_config_path
from futures_monitor.data.storage import Storage
from futures_monitor.market import MarketDataProvider
from futures_monitor.strategy.breakout import BreakoutStrategy, Kline
from futures_monitor.strategy.state_machine import (
    BREAKOUT_DETECTED,
    HOLDING,
    MONITORING,
    StrategyStateMachine,
)
from futures_monitor.utils.logger import get_logger
from futures_monitor.utils.timeutil import is_after_1445, is_after_1455

if TYPE_CHECKING:
    from futures_monitor.server.schemas import MonitorStatus, SymbolRow
    from futures_monitor.server.ws.hub import ConnectionHub


_CONNECTION_STATUS_MAP = {
    "未连接": "disconnected",
    "已断开": "disconnected",
    "连接中": "connecting",
    "已连接": "connected",
    "连接失败": "error",
}


def _to_local_dt(timestamp: float | int | str, timezone: str) -> datetime:
    """Convert timestamp to local datetime."""
    tz = ZoneInfo(timezone)
    if isinstance(timestamp, str):
        try:
            dt = datetime.fromisoformat(timestamp)
            return dt if dt.tzinfo else dt.replace(tzinfo=tz)
        except Exception:
            return datetime.now(tz)

    if isinstance(timestamp, int):
        if timestamp > 10**12:
            return datetime.fromtimestamp(timestamp / 1_000_000_000, tz=tz)
        return datetime.fromtimestamp(timestamp, tz=tz)

    if isinstance(timestamp, float):
        return datetime.fromtimestamp(timestamp, tz=tz)

    return datetime.now(tz)


def _build_breakout_message(symbol: str, breakout_price: float, tp: float, sl: float) -> str:
    """Build breakout alert message."""
    return (
        "【策略：分钟开盘战法】突破警报\n"
        f"品种：{symbol}\n"
        f"突破价：{breakout_price:.2f}\n"
        f"止盈：{tp:.2f}\n"
        f"止损：{sl:.2f}"
    )


def _build_runtime_state() -> dict:
    """Build initial runtime state for a symbol."""
    return {
        "day_high": None,
        "day_low": None,
        "breakout_price": None,
        "take_profit_price": None,
        "stop_loss_price": None,
        "reminded_1445": False,
        "reminded_1455": False,
        "tp_sent": False,
        "sl_sent": False,
        "last_event": "等待行情",
        "probe_count": 0,
        "probe_progress": 0,
        "probe_icon_level": 0,
        "probe_state_text": "监控中",
        "last_probe_target": None,
        "last_probe_bucket": None,
    }


def _clamp_progress(value: float) -> int:
    return max(0, min(100, int(round(value))))


class MonitorService:
    """Monitor service for managing futures breakout monitoring."""

    def __init__(self, config_path: str | None = None) -> None:
        self.logger = get_logger("futures_monitor.monitor_service")
        self._config_path = str(ensure_runtime_config(resolve_runtime_config_path())) if config_path is None else config_path
        self.config = self._load_config(self._config_path)

        self.storage = Storage(db_path=f"{self.config.data_dir}/monitor.db")
        self.desktop = DesktopAlertSender(alert_sound=self.config.alert_sound)
        self.sms = SmsAlertSender(enabled=self.config.enable_sms)
        self.provider = MarketDataProvider(config=self.config, logger=self.logger)

        self.strategy_map: dict[str, BreakoutStrategy] = {}
        self.machine_map: dict[str, StrategyStateMachine] = {}
        self.runtime_map: dict[str, dict] = {}

        self.symbols: list[str] = self.config.selection_symbols or ["SHFE.rb"]
        self.selection_mode: str = self.config.selection_mode
        self.selection_exchanges: list[str] = list(self.config.selection_exchanges)
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

        self._hub: ConnectionHub | None = None
        self._running = False
        self._connection_status = "disconnected"
        self._loop: asyncio.AbstractEventLoop | None = None
        self._stop_join_timeout = 2.0
        self._start_wait_timeout = 1.2
        self._start_wait_interval = 0.05
        self._start_ready_min_rows = 1

    def _load_config(self, config_path: str) -> AppConfig:
        """Load configuration from file."""
        config = load_config(config_path)
        if config.use_real_market_data and not config.strict_real_mode:
            self.logger.warning("当前为非严格真实行情模式，真实行情失败时将回退 mock")
        return config

    def set_hub(self, hub: ConnectionHub) -> None:
        """Set the WebSocket hub for broadcasting events."""
        self._hub = hub

    def set_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Store the application event loop for cross-thread broadcasts."""
        self._loop = loop

    def reload_config(self, config: AppConfig | None = None) -> AppConfig:
        """Reload runtime configuration and rebuild dependent providers."""
        next_config = config or self._load_config(self._config_path)
        self.config = next_config
        self.storage = Storage(db_path=f"{self.config.data_dir}/monitor.db")
        self.desktop = DesktopAlertSender(alert_sound=self.config.alert_sound)
        self.sms = SmsAlertSender(enabled=self.config.enable_sms)
        self.provider = MarketDataProvider(config=self.config, logger=self.logger)
        if not self._running:
            self.selection_mode = self.config.selection_mode
            self.selection_exchanges = list(self.config.selection_exchanges)
            if self.selection_mode == "custom":
                self.symbols = self.config.selection_symbols or ["SHFE.rb"]
            else:
                self.symbols = get_fixed_monitor_pool(self.selection_mode, self.selection_exchanges)
        return self.config

    def _schedule_broadcast(self, event: dict) -> None:
        if self._hub is None or self._loop is None:
            return
        try:
            asyncio.run_coroutine_threadsafe(self._hub.broadcast(event), self._loop)
        except Exception as exc:
            self.logger.debug("Failed to broadcast event: %s", exc)

    def _emit_event(self, event_type: str, data: dict) -> None:
        event = {"type": event_type, "data": data}
        self._schedule_broadcast(event)

    def _emit_log(self, message: str, level: str = "INFO") -> None:
        """Emit a log event."""
        getattr(self.logger, level.lower(), self.logger.info)(message)
        self._emit_event(
            "log",
            {
                "timestamp": datetime.now().isoformat(),
                "level": level,
                "message": message,
            },
        )

    def _build_row_payload(self, symbol: str) -> dict:
        machine = self.machine_map.setdefault(symbol, StrategyStateMachine())
        runtime = self.runtime_map.setdefault(symbol, _build_runtime_state())
        latest = self.provider.get_latest_snapshot([symbol]).get(symbol)
        metadata = self.provider.get_symbol_metadata(symbol)
        return {
            "symbol": symbol,
            "display_symbol": metadata.get("display_symbol", symbol),
            "name": metadata.get("name", ""),
            "exchange": metadata.get("exchange", ""),
            "status": machine.get_state(),
            "last_price": None if latest is None else latest.close,
            "day_high": runtime.get("day_high"),
            "day_low": runtime.get("day_low"),
            "breakout_price": runtime.get("breakout_price"),
            "take_profit": runtime.get("take_profit_price"),
            "stop_loss": runtime.get("stop_loss_price"),
            "last_event": runtime.get("last_event", "-"),
            "has_bought": machine.get_state() == HOLDING,
            "probe_count": int(runtime.get("probe_count", 0) or 0),
            "probe_progress": int(runtime.get("probe_progress", 0) or 0),
            "probe_icon_level": int(runtime.get("probe_icon_level", 0) or 0),
            "probe_state_text": str(runtime.get("probe_state_text", "监控中") or "监控中"),
        }

    def _emit_row(self, symbol: str) -> None:
        """Emit a row update event."""
        self._emit_event("row", self._build_row_payload(symbol))

    def _emit_connection(self, status: str) -> None:
        """Emit connection status event."""
        normalized = _CONNECTION_STATUS_MAP.get(status, status)
        self._connection_status = normalized
        self._emit_event("connection", {"status": normalized})

    def _emit_running(self, running: bool) -> None:
        """Emit running status event."""
        self._running = running
        self._emit_event("running", {"running": running})

    def _prepare_symbol_context(self, symbols: list[str]) -> None:
        """Prepare strategy and state machine context for symbols."""
        for symbol in symbols:
            self.strategy_map.setdefault(symbol, BreakoutStrategy())
            self.machine_map.setdefault(symbol, StrategyStateMachine())
            self.runtime_map.setdefault(symbol, _build_runtime_state())
            self._emit_row(symbol)

    def _cleanup_finished_thread(self) -> None:
        """Drop stale thread reference after monitor loop exits."""
        if self._thread and not self._thread.is_alive():
            self._thread = None

    def _has_live_thread(self) -> bool:
        """Return whether the monitor worker thread is still alive."""
        return self._thread is not None and self._thread.is_alive()

    def _is_stopping(self) -> bool:
        """Return whether a stop has been requested but the worker has not exited yet."""
        return self._stop_event.is_set() and self._has_live_thread()

    def _resolve_start_symbols(self, requested_symbols: list[str]) -> list[str]:
        """Resolve the concrete symbols that will be monitored for this run."""
        if self.selection_mode == "custom":
            return requested_symbols or ["SHFE.rb"]
        fixed_pool = get_fixed_monitor_pool(self.selection_mode, self.selection_exchanges)
        return self.provider.resolve_symbols(
            fixed_pool,
            selection_mode=self.selection_mode,
            selection_exchanges=self.selection_exchanges,
        )

    def _has_ready_start_snapshot(self) -> bool:
        """Return whether the first start snapshot already contains usable market state."""
        ready_rows = 0
        for symbol in self.symbols:
            runtime = self.runtime_map.get(symbol)
            if not runtime:
                continue
            latest = self.provider.get_latest_snapshot([symbol]).get(symbol)
            has_price = latest is not None and latest.close is not None
            has_range = runtime.get("day_high") is not None and runtime.get("day_low") is not None
            has_event = str(runtime.get("last_event") or "").strip() not in {"", "等待行情"}
            if has_price and (has_range or has_event):
                ready_rows += 1
                if ready_rows >= self._start_ready_min_rows:
                    return True
        return False

    def _wait_for_start_snapshot(self) -> None:
        """Wait briefly for the first batch of usable row data before returning start status."""
        deadline = time.monotonic() + self._start_wait_timeout
        while time.monotonic() < deadline:
            if not self._has_live_thread() or self._stop_event.is_set():
                return
            if self._has_ready_start_snapshot():
                return
            time.sleep(self._start_wait_interval)

    def _clear_monitor_state(self) -> None:
        """Reset monitor state so stopped snapshots do not expose stale rows."""
        self.symbols = []
        self.strategy_map.clear()
        self.machine_map.clear()
        self.runtime_map.clear()

    def start(
        self,
        symbols: list[str],
        selection_mode: str | None = None,
        selection_exchanges: list[str] | None = None,
    ) -> dict:
        """Start monitoring the specified symbols."""
        self._cleanup_finished_thread()
        if self._has_live_thread():
            if self._stop_event.is_set():
                return {"success": False, "message": "监控正在停止中，请稍候再试。"}
            return {"success": False, "message": "监控已在运行中。"}

        self.reload_config()
        selected_symbols = list(symbols) if symbols else list(self.config.selection_symbols)
        self.selection_mode = selection_mode or self.config.selection_mode
        self.selection_exchanges = list(selection_exchanges or self.config.selection_exchanges)
        self.symbols = self._resolve_start_symbols(selected_symbols)
        self._prepare_symbol_context(self.symbols)

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._monitor_loop, name="monitor-thread", daemon=True)
        self._thread.start()

        self._emit_running(True)
        if self.selection_mode == "all":
            msg = "启动监控: 固定主力池（映射当前活跃合约）"
        elif self.selection_mode == "exchange":
            msg = f"启动监控: 交易所 {', '.join(self.selection_exchanges)} 固定主力池（映射当前活跃合约）"
        else:
            msg = f"启动监控: {', '.join(self.symbols)}"
        self._emit_log(msg)
        self._wait_for_start_snapshot()

        return {
            "success": True,
            "message": msg,
            "symbols": list(self.symbols),
            "selection_mode": self.selection_mode,
            "selection_exchanges": self.selection_exchanges,
        }

    def stop(self) -> dict:
        """Stop monitoring."""
        thread = self._thread
        if not self._running and not self._has_live_thread():
            self._emit_connection("已断开")
            return {"success": True, "message": "监控未运行"}

        self._stop_event.set()
        self._emit_log("收到停止指令，正在停止监控线程。")

        if thread and thread.is_alive() and threading.current_thread() is not thread:
            thread.join(timeout=self._stop_join_timeout)
            if thread.is_alive():
                self._emit_log("监控线程仍在退出中，将继续等待后台循环收尾。", level="WARNING")
                return {"success": True, "message": "监控正在停止中"}
            self._thread = None
        else:
            self._cleanup_finished_thread()

        self._emit_connection("已断开")
        if self._running:
            self._emit_running(False)
        self._clear_monitor_state()
        return {"success": True, "message": "监控已停止"}

    def mark_bought(self, symbol: str) -> dict:
        """Mark a symbol as bought."""
        machine = self.machine_map.setdefault(symbol, StrategyStateMachine())
        runtime = self.runtime_map.setdefault(symbol, _build_runtime_state())

        try:
            machine.mark_bought(datetime.now().isoformat())
        except ValueError as exc:
            runtime["last_event"] = "当前状态不可标记已买入"
            self._emit_log(f"{symbol} 标记已买入失败：当前状态={machine.get_state()}", level="WARNING")
            self._emit_row(symbol)
            return {"success": False, "message": str(exc)}

        runtime["last_event"] = "手动标记已买入"
        self.storage.save_symbol_state(symbol=symbol, state=HOLDING, bought_at=datetime.now().isoformat())
        self._emit_log(f"{symbol} 已标记为 HOLDING")
        self._emit_row(symbol)

        return {"success": True, "message": f"{symbol} 已标记为已买入"}

    def get_status(self) -> "MonitorStatus":
        """Get current monitor status."""
        from futures_monitor.server.schemas import MonitorStatus, SymbolRow

        rows: list[SymbolRow] = []
        for symbol in self.symbols:
            machine = self.machine_map.get(symbol)
            runtime = self.runtime_map.get(symbol)
            if machine and runtime:
                rows.append(SymbolRow(**self._build_row_payload(symbol)))

        stopping = self._is_stopping()
        return MonitorStatus(
            running=self._running or stopping,
            connection_status=self._connection_status,
            symbols=self.symbols,
            selection_mode=self.selection_mode,
            selection_exchanges=list(self.selection_exchanges),
            rows=rows,
            message="监控正在停止中" if stopping else ("" if self._running else "监控未运行"),
        )

    def _set_day_high_low(self, symbol: str, kline: Kline) -> None:
        """Update day high/low for a symbol."""
        runtime = self.runtime_map.setdefault(symbol, _build_runtime_state())
        runtime["day_high"] = kline.high if runtime["day_high"] is None else max(runtime["day_high"], kline.high)
        runtime["day_low"] = kline.low if runtime["day_low"] is None else min(runtime["day_low"], kline.low)

    def _update_probe_state(self, symbol: str, kline: Kline) -> None:
        runtime = self.runtime_map.setdefault(symbol, _build_runtime_state())
        strategy = self.strategy_map.setdefault(symbol, BreakoutStrategy())
        probe_target_count = max(1, int(self.config.probe_target_count))
        probe_distance_ratio = max(0.0, float(self.config.probe_distance_ratio))
        klines = strategy.klines

        if len(klines) < 4 or runtime.get("day_high") is None or runtime.get("day_low") is None:
            runtime["probe_progress"] = 0
            runtime["probe_icon_level"] = min(int(runtime.get("probe_count", 0) or 0), probe_target_count)
            runtime["probe_state_text"] = "监控中"
            runtime["last_probe_target"] = None
            runtime["last_probe_bucket"] = None
            return

        previous_three = klines[-4:-1]
        current = klines[-1]
        if not all(item.close > item.open for item in previous_three):
            runtime["probe_progress"] = 0
            runtime["probe_state_text"] = "监控中"
            runtime["last_probe_target"] = None
            runtime["last_probe_bucket"] = None
            return

        target_price = previous_three[-1].low
        day_high = float(runtime["day_high"])
        day_low = float(runtime["day_low"])
        price_range = max(day_high - day_low, abs(target_price) * 0.001, 1e-6)
        threshold = max(price_range * probe_distance_ratio, 1e-6)
        distance = max(0.0, current.low - target_price)
        progress = _clamp_progress((1 - min(distance / threshold, 1.0)) * 100)
        runtime["probe_progress"] = progress
        runtime["probe_icon_level"] = min(int(runtime.get("probe_count", 0) or 0), probe_target_count)

        if current.low < target_price:
            runtime["probe_progress"] = 100
            runtime["probe_state_text"] = "突破检测"
            runtime["last_probe_target"] = target_price
            runtime["last_probe_bucket"] = None
            return

        if distance <= threshold:
            bucket = f"{target_price:.6f}:{current.timestamp}"
            if runtime.get("last_probe_bucket") != bucket:
                runtime["probe_count"] = min(probe_target_count, int(runtime.get("probe_count", 0) or 0) + 1)
                runtime["probe_icon_level"] = min(int(runtime.get("probe_count", 0) or 0), probe_target_count)
                runtime["last_probe_bucket"] = bucket
            runtime["last_probe_target"] = target_price
            runtime["probe_state_text"] = f"第{min(int(runtime.get('probe_count', 0) or 0), probe_target_count)}次试探"
            return

        runtime["probe_state_text"] = "监控中"
        if progress == 0:
            runtime["last_probe_bucket"] = None
        runtime["last_probe_target"] = target_price

    def _handle_monitoring_state(self, symbol: str, kline: Kline) -> None:
        """Handle MONITORING state logic."""
        strategy = self.strategy_map.setdefault(symbol, BreakoutStrategy())
        machine = self.machine_map.setdefault(symbol, StrategyStateMachine())
        runtime = self.runtime_map.setdefault(symbol, _build_runtime_state())

        result = strategy.evaluate(
            new_kline=kline,
            day_high=float(runtime["day_high"]),
            day_low=float(runtime["day_low"]),
            take_profit_pct=self.config.take_profit_pct,
            stop_loss_pct=self.config.stop_loss_pct,
        )
        self._update_probe_state(symbol, kline)
        if not result.triggered:
            runtime["last_event"] = runtime.get("probe_state_text") or "监控中"
            return

        machine.transition(BREAKOUT_DETECTED)
        runtime["breakout_price"] = result.breakout_price
        runtime["take_profit_price"] = result.take_profit_price
        runtime["stop_loss_price"] = result.stop_loss_price
        runtime["probe_progress"] = 100
        runtime["probe_state_text"] = "突破检测"
        runtime["last_event"] = "突破已触发，等待买入"

        msg = _build_breakout_message(
            symbol=symbol,
            breakout_price=float(result.breakout_price),
            tp=float(result.take_profit_price),
            sl=float(result.stop_loss_price),
        )
        self.logger.warning(msg)
        self.storage.save_alert(symbol=symbol, message=msg, level="WARNING")
        self.storage.save_symbol_state(symbol=symbol, state=BREAKOUT_DETECTED)
        self._emit_log(msg.replace("\n", " | "), level="WARNING")
        self.sms.send(phone_number="", message=msg)

    def _handle_breakout_state(self, symbol: str, current_dt: datetime) -> None:
        """Handle BREAKOUT_DETECTED state logic."""
        runtime = self.runtime_map.setdefault(symbol, _build_runtime_state())

        if not runtime["reminded_1445"] and is_after_1445(current_dt):
            remind = f"{symbol} 14:45 未买入提醒"
            runtime["reminded_1445"] = True
            runtime["last_event"] = remind
            self.storage.save_alert(symbol=symbol, message=remind, level="WARNING")
            self._emit_log(remind, level="WARNING")

    def _handle_holding_state(self, symbol: str, kline: Kline, current_dt: datetime) -> None:
        """Handle HOLDING state logic."""
        runtime = self.runtime_map.setdefault(symbol, _build_runtime_state())
        tp = runtime.get("take_profit_price")
        sl = runtime.get("stop_loss_price")

        if tp is not None and (not runtime["tp_sent"]) and kline.close >= float(tp):
            msg = f"{symbol} 止盈提醒，当前价={kline.close:.2f}，止盈价={float(tp):.2f}"
            runtime["tp_sent"] = True
            runtime["last_event"] = msg
            self.storage.save_alert(symbol=symbol, message=msg, level="WARNING")
            self._emit_log(msg, level="WARNING")

        if sl is not None and (not runtime["sl_sent"]) and kline.close <= float(sl):
            msg = f"{symbol} 止损提醒，当前价={kline.close:.2f}，止损价={float(sl):.2f}"
            runtime["sl_sent"] = True
            runtime["last_event"] = msg
            self.storage.save_alert(symbol=symbol, message=msg, level="WARNING")
            self._emit_log(msg, level="WARNING")

        if not runtime["reminded_1455"] and is_after_1455(current_dt):
            msg = f"{symbol} 14:55 持仓提醒（强制平仓提醒，仅提醒）"
            runtime["reminded_1455"] = True
            runtime["last_event"] = msg
            self.storage.save_alert(symbol=symbol, message=msg, level="WARNING")
            self._emit_log(msg, level="WARNING")

    def _process_tick(self, symbol: str, kline: Kline) -> None:
        """Process a single tick for a symbol."""
        self.provider._latest_snapshot[symbol] = kline
        self._set_day_high_low(symbol, kline)

        machine = self.machine_map.setdefault(symbol, StrategyStateMachine())
        runtime = self.runtime_map.setdefault(symbol, _build_runtime_state())
        state = machine.get_state()
        current_dt = _to_local_dt(kline.timestamp, self.config.timezone)

        if state == MONITORING:
            self._handle_monitoring_state(symbol, kline)
            state = machine.get_state()

        if state == BREAKOUT_DETECTED:
            self._handle_breakout_state(symbol, current_dt)

        if state == HOLDING:
            self._handle_holding_state(symbol, kline, current_dt)

        if runtime.get("last_event") in (None, ""):
            runtime["last_event"] = "监控中"

        self._emit_row(symbol)

    def _monitor_loop(self) -> None:
        """Main monitoring loop running in a separate thread."""
        self._emit_connection("连接中")
        thread = threading.current_thread()
        try:
            stream = self.provider.stream_1m_klines(
                self.symbols,
                stop_flag=self._stop_event.is_set,
                selection_mode=self.selection_mode,
                selection_exchanges=self.selection_exchanges,
            )
            self._emit_connection("已连接")
            for symbol, kline in stream:
                if self._stop_event.is_set():
                    break
                if symbol not in self.symbols:
                    self.symbols.append(symbol)
                    self._prepare_symbol_context([symbol])
                self._process_tick(symbol, kline)
        except Exception as exc:
            self._emit_connection("连接失败")
            self._emit_log(f"行情线程异常退出: {exc}", level="ERROR")
            self.logger.exception("monitor loop failed")
        finally:
            if self._thread is thread:
                self._thread = None
            self._emit_connection("已断开")
            if self._running:
                self._emit_running(False)
            if self._stop_event.is_set():
                self._emit_log("监控已停止。")
                self._clear_monitor_state()


_monitor_service_instance: MonitorService | None = None


def get_monitor_service() -> MonitorService:
    """Get the global MonitorService singleton instance."""
    global _monitor_service_instance
    if _monitor_service_instance is None:
        _monitor_service_instance = MonitorService()
    return _monitor_service_instance
