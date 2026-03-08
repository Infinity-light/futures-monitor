"""
---
role: Define API data contracts for monitor and config modules.
depends:
  - pydantic.BaseModel
exports:
  - HealthResponse
  - MonitorStatus
  - MonitorControlRequest
  - MarkBoughtRequest
  - SymbolRow
  - ConfigDTO
status: IMPLEMENTED
functions:
  - HealthResponse.model_dump() -> dict
  - MonitorStatus.model_dump() -> dict
  - MonitorControlRequest.model_dump() -> dict
  - MarkBoughtRequest.model_dump() -> dict
  - SymbolRow.model_dump() -> dict
  - ConfigDTO.model_dump() -> dict
---
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    message: str = "ok"


class SymbolRow(BaseModel):
    """Single symbol monitoring row status."""

    symbol: str
    status: str = "MONITORING"
    last_price: float | None = None
    day_high: float | None = None
    day_low: float | None = None
    breakout_price: float | None = None
    take_profit: float | None = None
    stop_loss: float | None = None
    last_event: str = "-"
    has_bought: bool = False


class MonitorStatus(BaseModel):
    """Monitor service status."""

    running: bool = False
    connection_status: str = "disconnected"
    symbols: list[str] = Field(default_factory=list)
    rows: list[SymbolRow] = Field(default_factory=list)
    message: str = ""


class MonitorControlRequest(BaseModel):
    """Control monitor start/stop."""

    action: str
    symbols: list[str] = Field(default_factory=list)


class MarkBoughtRequest(BaseModel):
    """Mark a symbol as bought."""

    symbol: str


class ConfigDTO(BaseModel):
    """Configuration data transfer object."""

    symbols: list[str] = Field(default_factory=list)
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

    def model_dump_masked(self) -> dict:
        """Return dict with password masked."""

        data = self.model_dump()
        if data.get("tq_password"):
            data["tq_password"] = "***"
        return data
