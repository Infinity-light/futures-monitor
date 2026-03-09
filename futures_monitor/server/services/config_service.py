"""
---
role: Encapsulate configuration persistence and retrieval logic.
depends:
  - futures_monitor.config.AppConfig
  - futures_monitor.config.load_config
  - futures_monitor.config.save_config
  - futures_monitor.config.resolve_runtime_config_path
  - futures_monitor.server.schemas.ConfigDTO
  - futures_monitor.server.services.monitor_service.MonitorService
exports:
  - ConfigService
status: IMPLEMENTED
functions:
  - ConfigService.get_config() -> ConfigDTO
  - ConfigService.update_config(payload: ConfigDTO) -> ConfigDTO
  - ConfigService.to_dto(config: AppConfig) -> ConfigDTO
  - ConfigService.from_dto(dto: ConfigDTO) -> AppConfig
  - ConfigService.set_monitor_service(monitor_service: MonitorService | None) -> None
---
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from futures_monitor.config import (
    AppConfig,
    SYMBOL_CANDIDATE_DEFINITIONS,
    ensure_runtime_config,
    load_config,
    resolve_runtime_config_path,
    save_config,
)

if TYPE_CHECKING:
    from futures_monitor.server.schemas import ConfigDTO
    from futures_monitor.server.services.monitor_service import MonitorService


logger = logging.getLogger(__name__)

_EXCHANGE_NAMES = {
    "SHFE": "上期所",
    "DCE": "大商所",
    "CZCE": "郑商所",
    "CFFEX": "中金所",
    "INE": "上期能源",
    "GFEX": "广期所",
}

_SYMBOL_CANDIDATES = SYMBOL_CANDIDATE_DEFINITIONS


class ConfigService:
    """Configuration service for reading and writing app configuration."""

    def __init__(self, config_path: str | None = None) -> None:
        self._config_path = str(ensure_runtime_config(resolve_runtime_config_path())) if config_path is None else config_path
        self._monitor_service: MonitorService | None = None

    def set_monitor_service(self, monitor_service: MonitorService | None) -> None:
        """Attach the monitor service so config saves can refresh runtime state."""
        self._monitor_service = monitor_service

    def _build_symbol_candidates(self) -> list:
        from futures_monitor.server.schemas import SymbolCandidate

        return [
            SymbolCandidate(
                value=item["value"],
                code=item["code"],
                name=item["name"],
                exchange=item["exchange"],
                category=_EXCHANGE_NAMES.get(item["exchange"], item["exchange"]),
            )
            for item in _SYMBOL_CANDIDATES
        ]

    def _with_candidates(self, dto: "ConfigDTO") -> "ConfigDTO":
        dto.symbol_candidates = self._build_symbol_candidates()
        return dto

    def get_symbol_candidates(self) -> list:
        return self._build_symbol_candidates()

    @staticmethod
    def to_dto(config: AppConfig) -> "ConfigDTO":
        """Convert AppConfig to ConfigDTO."""
        from futures_monitor.server.schemas import ConfigDTO

        return ConfigDTO(
            symbols=list(config.symbols) if config.symbols else [],
            selection_mode=config.selection_mode,
            selection_exchanges=list(config.selection_exchanges) if config.selection_exchanges else [],
            selection_symbols=list(config.selection_symbols) if config.selection_symbols else [],
            take_profit_pct=config.take_profit_pct,
            stop_loss_pct=config.stop_loss_pct,
            position_pct=config.position_pct,
            enable_sms=config.enable_sms,
            alert_sound=config.alert_sound,
            data_dir=config.data_dir,
            timezone=config.timezone,
            use_real_market_data=config.use_real_market_data,
            strict_real_mode=config.strict_real_mode,
            ui_refresh_ms=config.ui_refresh_ms,
            tq_account=config.tq_account,
            tq_password=config.tq_password,
        )

    @staticmethod
    def from_dto(dto: "ConfigDTO") -> AppConfig:
        """Convert ConfigDTO to AppConfig."""
        return AppConfig(
            symbols=list(dto.symbols) if dto.symbols else [],
            selection_mode=dto.selection_mode,
            selection_exchanges=list(dto.selection_exchanges) if dto.selection_exchanges else [],
            selection_symbols=list(dto.selection_symbols) if dto.selection_symbols else [],
            take_profit_pct=dto.take_profit_pct,
            stop_loss_pct=dto.stop_loss_pct,
            position_pct=dto.position_pct,
            enable_sms=dto.enable_sms,
            alert_sound=dto.alert_sound,
            data_dir=dto.data_dir,
            timezone=dto.timezone,
            use_real_market_data=dto.use_real_market_data,
            strict_real_mode=dto.strict_real_mode,
            ui_refresh_ms=dto.ui_refresh_ms,
            tq_account=dto.tq_account,
            tq_password=dto.tq_password,
        )

    def get_config(self) -> "ConfigDTO":
        """Load configuration from file and return as DTO."""
        try:
            config = load_config(self._config_path)
            logger.info("Configuration loaded from %s", self._config_path)
            return self._with_candidates(self.to_dto(config))
        except Exception as exc:
            logger.error("Failed to load config: %s", exc)
            return self._with_candidates(self.to_dto(AppConfig()))

    def update_config(self, payload: "ConfigDTO") -> "ConfigDTO":
        """Save configuration to file and refresh runtime consumers."""
        try:
            config = self.from_dto(payload)
            save_config(config, self._config_path)

            if self._monitor_service is not None:
                self._monitor_service.reload_config(config)

            log_payload = payload.model_dump_masked()
            logger.info("Configuration saved to %s: %s", self._config_path, log_payload)
            return self._with_candidates(self.to_dto(config))
        except Exception as exc:
            logger.error("Failed to save config: %s", exc)
            raise


_config_service_instance: ConfigService | None = None


def get_config_service() -> ConfigService:
    """Get the global ConfigService singleton instance."""
    global _config_service_instance
    if _config_service_instance is None:
        _config_service_instance = ConfigService()
    return _config_service_instance
