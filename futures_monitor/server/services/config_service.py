"""
---
role: Encapsulate configuration persistence and retrieval logic.
depends:
  - futures_monitor.config.AppConfig
  - futures_monitor.config.load_config
  - futures_monitor.config.save_config
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

from futures_monitor.config import AppConfig, load_config, save_config

if TYPE_CHECKING:
    from futures_monitor.server.schemas import ConfigDTO
    from futures_monitor.server.services.monitor_service import MonitorService


logger = logging.getLogger(__name__)


class ConfigService:
    """Configuration service for reading and writing app configuration."""

    def __init__(self, config_path: str = "futures_monitor/config.json") -> None:
        self._config_path = config_path
        self._monitor_service: MonitorService | None = None

    def set_monitor_service(self, monitor_service: MonitorService | None) -> None:
        """Attach the monitor service so config saves can refresh runtime state."""
        self._monitor_service = monitor_service

    @staticmethod
    def to_dto(config: AppConfig) -> "ConfigDTO":
        """Convert AppConfig to ConfigDTO."""
        from futures_monitor.server.schemas import ConfigDTO

        return ConfigDTO(
            symbols=list(config.symbols) if config.symbols else [],
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
        """Load configuration from file and return as DTO.

        Returns:
            ConfigDTO with current configuration. Password is included but
            should be masked by the API layer before sending to client.
        """
        try:
            config = load_config(self._config_path)
            logger.info(f"Configuration loaded from {self._config_path}")
            return self.to_dto(config)
        except Exception as exc:
            logger.error(f"Failed to load config: {exc}")
            # Return default config on error
            return self.to_dto(AppConfig())

    def update_config(self, payload: "ConfigDTO") -> "ConfigDTO":
        """Save configuration to file and refresh runtime consumers.

        Args:
            payload: New configuration values.

        Returns:
            ConfigDTO with saved configuration.

        Note:
            Password is not logged for security reasons.
        """
        try:
            config = self.from_dto(payload)
            save_config(config, self._config_path)

            if self._monitor_service is not None:
                self._monitor_service.reload_config(config)

            log_payload = payload.model_dump_masked()
            logger.info(f"Configuration saved to {self._config_path}: {log_payload}")

            return self.to_dto(config)
        except Exception as exc:
            logger.error(f"Failed to save config: {exc}")
            raise


# Global singleton instance
_config_service_instance: ConfigService | None = None


def get_config_service() -> ConfigService:
    """Get the global ConfigService singleton instance."""
    global _config_service_instance
    if _config_service_instance is None:
        _config_service_instance = ConfigService()
    return _config_service_instance
