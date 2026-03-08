"""
---
role: Provide HTTP endpoints for reading and updating monitor configuration.
depends:
  - fastapi.APIRouter
  - fastapi.Depends
  - fastapi.HTTPException
  - futures_monitor.server.schemas.ConfigDTO
  - futures_monitor.server.services.config_service.ConfigService
exports:
  - router
  - get_config
  - update_config
status: IMPLEMENTED
functions:
  - get_config() -> ConfigDTO
  - update_config(payload: ConfigDTO) -> ConfigDTO
---
"""

import logging

from fastapi import APIRouter, Depends, HTTPException

from ..schemas import ConfigDTO
from ..services.config_service import ConfigService, get_config_service

router = APIRouter(tags=["config"])
logger = logging.getLogger(__name__)


def get_config_service_dependency() -> ConfigService:
    """Dependency to get the ConfigService singleton."""
    return get_config_service()


def _mask_password(dto: ConfigDTO) -> ConfigDTO:
    """Return a response-safe copy of the config with masked password."""
    data = dto.model_dump()
    if data.get("tq_password"):
        data["tq_password"] = "***"
    return ConfigDTO(**data)


@router.get("/config", response_model=ConfigDTO)
def get_config(
    service: ConfigService = Depends(get_config_service_dependency),
) -> ConfigDTO:
    """Return current configuration.

    Note: The tq_password field is masked (shown as ***) for security.
    """
    try:
        return _mask_password(service.get_config())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to load config: {exc}") from exc


@router.put("/config", response_model=ConfigDTO)
def update_config(
    payload: ConfigDTO,
    service: ConfigService = Depends(get_config_service_dependency),
) -> ConfigDTO:
    """Update configuration.

    Args:
        payload: New configuration values. Use tq_password="***" to keep existing password.

    Note:
        Password is not logged for security reasons.
    """
    try:
        current = service.get_config()
        next_payload = payload.model_copy(deep=True)
        if next_payload.tq_password == "***":
            next_payload.tq_password = current.tq_password

        result = service.update_config(next_payload)
        return _mask_password(result)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Failed to update config: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to save config: {exc}") from exc
