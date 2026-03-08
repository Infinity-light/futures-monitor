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


@router.get("/config", response_model=ConfigDTO)
def get_config(
    service: ConfigService = Depends(get_config_service_dependency),
) -> ConfigDTO:
    """Return current configuration exactly as stored."""
    try:
        return service.get_config()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to load config: {exc}") from exc


@router.put("/config", response_model=ConfigDTO)
def update_config(
    payload: ConfigDTO,
    service: ConfigService = Depends(get_config_service_dependency),
) -> ConfigDTO:
    """Update configuration using the exact values submitted by the client."""
    try:
        return service.update_config(payload)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Failed to update config: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to save config: {exc}") from exc
