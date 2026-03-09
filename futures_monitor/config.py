"""
---
role: 配置模块
depends: []
exports:
  - AppConfig
  - resolve_config_template_path
  - resolve_runtime_config_path
  - ensure_runtime_config
  - load_config
  - save_config
  - normalize_selection_mode
  - normalize_selection_exchanges
  - normalize_selection_symbols
  - derive_legacy_symbols
  - is_all_selection_token
  - ALL_SYMBOL_LABEL
  - ALL_SYMBOL_ALIASES
  - SUPPORTED_EXCHANGES
status: IMPLEMENTED
functions:
  - resolve_config_template_path() -> Path
  - resolve_runtime_config_path() -> Path
  - ensure_runtime_config(path: str | Path | None = None, template_path: str | Path | None = None) -> Path
  - load_config(path: str | None = None) -> AppConfig
  - save_config(config: AppConfig, path: str | None = None) -> str
  - normalize_selection_mode(value: object, symbols: list[str] | None = None, exchanges: list[str] | None = None) -> str
  - normalize_selection_exchanges(values: object) -> list[str]
  - normalize_selection_symbols(values: object) -> list[str]
  - derive_legacy_symbols(selection_mode: str, selection_symbols: list[str]) -> list[str]
  - is_all_selection_token(value: object) -> bool
---
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import shutil


ALL_SYMBOL_LABEL = "ALL 全部品种（自动读取当前有效合约）"
ALL_SYMBOL_ALIASES = {"ALL", "全部", ALL_SYMBOL_LABEL}
SUPPORTED_SELECTION_MODES = {"all", "exchange", "custom"}
SUPPORTED_EXCHANGES = {"SHFE", "DCE", "CZCE", "CFFEX", "INE", "GFEX"}
_PACKAGE_ROOT = Path(__file__).resolve().parent
_DEFAULT_TEMPLATE_CONFIG_PATH = _PACKAGE_ROOT / "config.json"
_DEFAULT_RUNTIME_DATA_DIR = _PACKAGE_ROOT.parent / ".data"
_RUNTIME_CONFIG_ENV = "FUTURES_MONITOR_RUNTIME_CONFIG"
_RUNTIME_DATA_DIR_ENV = "FUTURES_MONITOR_DATA_DIR"
_TEMPLATE_CONFIG_ENV = "FUTURES_MONITOR_CONFIG_TEMPLATE"
SYMBOL_CANDIDATE_DEFINITIONS = [
    {"value": "SHFE.rb", "code": "SHFE.rb", "name": "螺纹钢", "exchange": "SHFE"},
    {"value": "SHFE.hc", "code": "SHFE.hc", "name": "热轧卷板", "exchange": "SHFE"},
    {"value": "SHFE.fu", "code": "SHFE.fu", "name": "燃料油", "exchange": "SHFE"},
    {"value": "SHFE.bu", "code": "SHFE.bu", "name": "沥青", "exchange": "SHFE"},
    {"value": "SHFE.au", "code": "SHFE.au", "name": "黄金", "exchange": "SHFE"},
    {"value": "SHFE.ag", "code": "SHFE.ag", "name": "白银", "exchange": "SHFE"},
    {"value": "SHFE.cu", "code": "SHFE.cu", "name": "沪铜", "exchange": "SHFE"},
    {"value": "SHFE.al", "code": "SHFE.al", "name": "沪铝", "exchange": "SHFE"},
    {"value": "SHFE.zn", "code": "SHFE.zn", "name": "沪锌", "exchange": "SHFE"},
    {"value": "DCE.i", "code": "DCE.i", "name": "铁矿石", "exchange": "DCE"},
    {"value": "DCE.m", "code": "DCE.m", "name": "豆粕", "exchange": "DCE"},
    {"value": "DCE.y", "code": "DCE.y", "name": "豆油", "exchange": "DCE"},
    {"value": "DCE.a", "code": "DCE.a", "name": "豆一", "exchange": "DCE"},
    {"value": "DCE.c", "code": "DCE.c", "name": "玉米", "exchange": "DCE"},
    {"value": "DCE.cs", "code": "DCE.cs", "name": "玉米淀粉", "exchange": "DCE"},
    {"value": "DCE.eg", "code": "DCE.eg", "name": "乙二醇", "exchange": "DCE"},
    {"value": "DCE.pp", "code": "DCE.pp", "name": "聚丙烯", "exchange": "DCE"},
    {"value": "DCE.v", "code": "DCE.v", "name": "PVC", "exchange": "DCE"},
    {"value": "CZCE.TA", "code": "CZCE.TA", "name": "PTA", "exchange": "CZCE"},
    {"value": "CZCE.MA", "code": "CZCE.MA", "name": "甲醇", "exchange": "CZCE"},
    {"value": "CZCE.SR", "code": "CZCE.SR", "name": "白糖", "exchange": "CZCE"},
    {"value": "CZCE.CF", "code": "CZCE.CF", "name": "棉花", "exchange": "CZCE"},
    {"value": "CZCE.RM", "code": "CZCE.RM", "name": "菜粕", "exchange": "CZCE"},
    {"value": "CZCE.SA", "code": "CZCE.SA", "name": "纯碱", "exchange": "CZCE"},
    {"value": "CZCE.FG", "code": "CZCE.FG", "name": "玻璃", "exchange": "CZCE"},
    {"value": "CZCE.UR", "code": "CZCE.UR", "name": "尿素", "exchange": "CZCE"},
    {"value": "CZCE.WH", "code": "CZCE.WH", "name": "强麦", "exchange": "CZCE"},
    {"value": "CZCE.WR", "code": "CZCE.WR", "name": "线材", "exchange": "CZCE"},
    {"value": "CZCE.ZC", "code": "CZCE.ZC", "name": "郑煤", "exchange": "CZCE"},
    {"value": "CFFEX.IF", "code": "CFFEX.IF", "name": "沪深300股指", "exchange": "CFFEX"},
    {"value": "CFFEX.IC", "code": "CFFEX.IC", "name": "中证500股指", "exchange": "CFFEX"},
    {"value": "CFFEX.IH", "code": "CFFEX.IH", "name": "上证50股指", "exchange": "CFFEX"},
    {"value": "CFFEX.IM", "code": "CFFEX.IM", "name": "中证1000股指", "exchange": "CFFEX"},
    {"value": "CFFEX.T", "code": "CFFEX.T", "name": "10年期国债", "exchange": "CFFEX"},
    {"value": "INE.sc", "code": "INE.sc", "name": "原油", "exchange": "INE"},
    {"value": "INE.nr", "code": "INE.nr", "name": "20号胶", "exchange": "INE"},
    {"value": "INE.lu", "code": "INE.lu", "name": "低硫燃料油", "exchange": "INE"},
    {"value": "GFEX.si", "code": "GFEX.si", "name": "工业硅", "exchange": "GFEX"},
    {"value": "GFEX.lc", "code": "GFEX.lc", "name": "碳酸锂", "exchange": "GFEX"},
]


@dataclass(slots=True)
class AppConfig:
    symbols: list[str] = field(default_factory=list)
    selection_mode: str = "all"
    selection_exchanges: list[str] = field(default_factory=list)
    selection_symbols: list[str] = field(default_factory=list)
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


def resolve_config_template_path() -> Path:
    configured = os.getenv(_TEMPLATE_CONFIG_ENV)
    return Path(configured).expanduser() if configured else _DEFAULT_TEMPLATE_CONFIG_PATH


def resolve_runtime_config_path() -> Path:
    configured_path = os.getenv(_RUNTIME_CONFIG_ENV)
    if configured_path:
        return Path(configured_path).expanduser()

    configured_data_dir = os.getenv(_RUNTIME_DATA_DIR_ENV)
    data_dir = Path(configured_data_dir).expanduser() if configured_data_dir else _DEFAULT_RUNTIME_DATA_DIR
    return data_dir / "config.json"


def ensure_runtime_config(path: str | Path | None = None, template_path: str | Path | None = None) -> Path:
    runtime_path = Path(path).expanduser() if path is not None else resolve_runtime_config_path()
    runtime_path.parent.mkdir(parents=True, exist_ok=True)
    if runtime_path.exists():
        return runtime_path

    source_path = Path(template_path).expanduser() if template_path is not None else resolve_config_template_path()
    if source_path.exists():
        shutil.copyfile(source_path, runtime_path)
    else:
        runtime_path.write_text(json.dumps(_config_to_payload(AppConfig()), ensure_ascii=False, indent=2), encoding="utf-8")
    return runtime_path


def _dedupe_strings(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        token = str(value).strip()
        if not token or token in seen:
            continue
        seen.add(token)
        result.append(token)
    return result


def is_all_selection_token(value: object) -> bool:
    token = str(value or "").strip()
    if not token:
        return False
    token_upper = token.upper()
    return token_upper == "ALL" or token == "全部" or token_upper.startswith("ALL ") or "全部品种" in token


def normalize_selection_mode(
    value: object,
    symbols: list[str] | None = None,
    exchanges: list[str] | None = None,
) -> str:
    token = str(value or "").strip().lower()
    if token in SUPPORTED_SELECTION_MODES:
        return token

    normalized_symbols = normalize_selection_symbols(symbols or [])
    normalized_exchanges = normalize_selection_exchanges(exchanges or [])
    if any(is_all_selection_token(symbol) for symbol in normalized_symbols):
        return "all"
    if normalized_exchanges:
        return "exchange"
    if normalized_symbols:
        return "custom"
    return "all"


def normalize_selection_exchanges(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    normalized = [str(value).strip().upper() for value in values if str(value).strip()]
    return [value for value in _dedupe_strings(normalized) if value in SUPPORTED_EXCHANGES]


def normalize_selection_symbols(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    normalized = [str(value).strip() for value in values if str(value).strip()]
    return _dedupe_strings(normalized)


def derive_legacy_symbols(selection_mode: str, selection_symbols: list[str]) -> list[str]:
    if selection_mode in {"all", "exchange"}:
        return ["ALL"]
    return list(selection_symbols)


def _resolve_selection_fields(raw: dict) -> tuple[str, list[str], list[str], list[str]]:
    raw_symbols = normalize_selection_symbols(raw.get("symbols", []))
    raw_selection_symbols = raw.get("selection_symbols", raw.get("selection_contracts", []))
    selection_symbols = normalize_selection_symbols(raw_selection_symbols)
    selection_exchanges = normalize_selection_exchanges(raw.get("selection_exchanges", []))
    selection_mode = normalize_selection_mode(
        raw.get("selection_mode"),
        selection_symbols or raw_symbols,
        selection_exchanges,
    )

    if selection_mode == "custom" and not selection_symbols:
        selection_symbols = [symbol for symbol in raw_symbols if not is_all_selection_token(symbol)]
    if selection_mode != "custom":
        selection_symbols = []
    if selection_mode != "exchange":
        selection_exchanges = []

    legacy_symbols = derive_legacy_symbols(selection_mode, selection_symbols)
    return selection_mode, selection_exchanges, selection_symbols, legacy_symbols


def _validate_pct(name: str, value: float) -> None:
    if not 0 <= value <= 1:
        raise ValueError(f"{name} must be in range [0, 1], got {value}")


def _validate_config(config: AppConfig) -> None:
    if not isinstance(config.symbols, list) or any(not isinstance(item, str) for item in config.symbols):
        raise ValueError("symbols must be list[str]")
    if config.selection_mode not in SUPPORTED_SELECTION_MODES:
        raise ValueError(f"selection_mode must be one of {SUPPORTED_SELECTION_MODES}")
    if not isinstance(config.selection_exchanges, list) or any(not isinstance(item, str) for item in config.selection_exchanges):
        raise ValueError("selection_exchanges must be list[str]")
    if not isinstance(config.selection_symbols, list) or any(not isinstance(item, str) for item in config.selection_symbols):
        raise ValueError("selection_symbols must be list[str]")

    _validate_pct("take_profit_pct", config.take_profit_pct)
    _validate_pct("stop_loss_pct", config.stop_loss_pct)
    _validate_pct("position_pct", config.position_pct)

    if not isinstance(config.data_dir, str) or not config.data_dir.strip():
        raise ValueError("data_dir must be non-empty string")
    if not isinstance(config.timezone, str) or not config.timezone.strip():
        raise ValueError("timezone must be non-empty string")
    if not isinstance(config.ui_refresh_ms, int) or config.ui_refresh_ms <= 0:
        raise ValueError("ui_refresh_ms must be positive int")


def _config_to_payload(config: AppConfig) -> dict:
    return {
        "symbols": list(config.symbols),
        "selection_mode": config.selection_mode,
        "selection_exchanges": list(config.selection_exchanges),
        "selection_symbols": list(config.selection_symbols),
        "take_profit_pct": config.take_profit_pct,
        "stop_loss_pct": config.stop_loss_pct,
        "position_pct": config.position_pct,
        "enable_sms": config.enable_sms,
        "alert_sound": config.alert_sound,
        "data_dir": config.data_dir,
        "timezone": config.timezone,
        "use_real_market_data": config.use_real_market_data,
        "strict_real_mode": config.strict_real_mode,
        "ui_refresh_ms": config.ui_refresh_ms,
        "tq_account": config.tq_account,
        "tq_password": config.tq_password,
    }


def load_config(path: str | None = None) -> AppConfig:
    config_path = ensure_runtime_config() if path is None else Path(path)
    if not config_path.exists():
        return AppConfig()

    with config_path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    selection_mode, selection_exchanges, selection_symbols, legacy_symbols = _resolve_selection_fields(raw)
    config = AppConfig(
        symbols=legacy_symbols,
        selection_mode=selection_mode,
        selection_exchanges=selection_exchanges,
        selection_symbols=selection_symbols,
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


def save_config(config: AppConfig, path: str | None = None) -> str:
    config.selection_exchanges = normalize_selection_exchanges(config.selection_exchanges)
    config.selection_symbols = normalize_selection_symbols(config.selection_symbols)
    config.selection_mode = normalize_selection_mode(
        config.selection_mode,
        config.selection_symbols or config.symbols,
        config.selection_exchanges,
    )
    config.symbols = derive_legacy_symbols(config.selection_mode, config.selection_symbols)
    _validate_config(config)

    payload = _config_to_payload(config)

    config_path = Path(path) if path is not None else resolve_runtime_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with config_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return str(config_path)
