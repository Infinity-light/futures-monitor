"""
---
role: 配置模块
depends: []
exports:
  - AppConfig
  - load_config
  - save_config
status: IMPLEMENTED
functions:
  - load_config(path: str = "futures_monitor/config.json") -> AppConfig
  - save_config(config: AppConfig, path: str = "futures_monitor/config.json") -> str
---
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path


@dataclass(slots=True)
class AppConfig:
    symbols: list[str] = field(default_factory=list)
    take_profit_pct: float = 0.5
    stop_loss_pct: float = 0.5
    position_pct: float = 0.1
    enable_sms: bool = False
    alert_sound: bool = True
    data_dir: str = ".data"
    timezone: str = "Asia/Shanghai"
    use_real_market_data: bool = False
    strict_real_mode: bool = True
    ui_refresh_ms: int = 800
    tq_account: str = ""
    tq_password: str = ""


def _validate_pct(name: str, value: float) -> None:
    if not 0 <= value <= 1:
        raise ValueError(f"{name} must be in range [0, 1], got {value}")


def _validate_config(config: AppConfig) -> None:
    if not isinstance(config.symbols, list) or any(not isinstance(item, str) for item in config.symbols):
        raise ValueError("symbols must be list[str]")

    _validate_pct("take_profit_pct", config.take_profit_pct)
    _validate_pct("stop_loss_pct", config.stop_loss_pct)
    _validate_pct("position_pct", config.position_pct)

    if not isinstance(config.data_dir, str) or not config.data_dir.strip():
        raise ValueError("data_dir must be non-empty string")
    if not isinstance(config.timezone, str) or not config.timezone.strip():
        raise ValueError("timezone must be non-empty string")
    if not isinstance(config.ui_refresh_ms, int) or config.ui_refresh_ms <= 0:
        raise ValueError("ui_refresh_ms must be positive int")


def load_config(path: str = "futures_monitor/config.json") -> AppConfig:
    config_path = Path(path)
    if not config_path.exists():
        return AppConfig()

    with config_path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    config = AppConfig(
        symbols=raw.get("symbols", []),
        take_profit_pct=raw.get("take_profit_pct", 0.5),
        stop_loss_pct=raw.get("stop_loss_pct", 0.5),
        position_pct=raw.get("position_pct", 0.1),
        enable_sms=raw.get("enable_sms", False),
        alert_sound=raw.get("alert_sound", True),
        data_dir=raw.get("data_dir", ".data"),
        timezone=raw.get("timezone", "Asia/Shanghai"),
        use_real_market_data=raw.get("use_real_market_data", False),
        strict_real_mode=raw.get("strict_real_mode", True),
        ui_refresh_ms=raw.get("ui_refresh_ms", 800),
        tq_account=raw.get("tq_account", ""),
        tq_password=raw.get("tq_password", ""),
    )
    _validate_config(config)
    return config


def save_config(config: AppConfig, path: str = "futures_monitor/config.json") -> str:
    _validate_config(config)

    config_path = Path(path)
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with config_path.open("w", encoding="utf-8") as f:
        json.dump(asdict(config), f, ensure_ascii=False, indent=2)

    return str(config_path)
