"""
---
role: Provide HTTP endpoints for monitor status and control commands.
depends:
  - fastapi.APIRouter
  - fastapi.Depends
  - fastapi.HTTPException
  - futures_monitor.server.schemas.MonitorStatus
  - futures_monitor.server.schemas.MonitorControlRequest
  - futures_monitor.server.schemas.MarkBoughtRequest
  - futures_monitor.server.services.monitor_service.MonitorService
exports:
  - router
  - get_status
  - control_monitor
  - mark_bought
status: IMPLEMENTED
functions:
  - get_status() -> MonitorStatus
  - control_monitor(payload: MonitorControlRequest) -> MonitorStatus
  - mark_bought(payload: MarkBoughtRequest) -> dict
---
"""

from fastapi import APIRouter, Depends, HTTPException

from ..schemas import MarkBoughtRequest, MonitorControlRequest, MonitorStatus
from ..services.monitor_service import get_monitor_service, MonitorService

router = APIRouter(tags=["monitor"])


def get_monitor_service_dependency() -> MonitorService:
    """Dependency to get the MonitorService singleton."""
    return get_monitor_service()


@router.get("/monitor/status", response_model=MonitorStatus)
def get_status(
    service: MonitorService = Depends(get_monitor_service_dependency),
) -> MonitorStatus:
    """Return current monitor status including running state, connection status, and symbol rows."""
    try:
        return service.get_status()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {exc}") from exc


@router.post("/monitor/control", response_model=MonitorStatus)
def control_monitor(
    payload: MonitorControlRequest,
    service: MonitorService = Depends(get_monitor_service_dependency),
) -> MonitorStatus:
    """Control the monitor - start or stop monitoring.

    Args:
        payload: Control request with action ("start" or "stop") and optional symbols list.
                Use symbols=["ALL"] or symbols=["全部"] to monitor all domestic futures.
    """
    try:
        if payload.action == "start":
            result = service.start(payload.symbols)
            if not result.get("success"):
                raise HTTPException(status_code=400, detail=result.get("message", "Failed to start"))
        elif payload.action == "stop":
            result = service.stop()
            if not result.get("success"):
                raise HTTPException(status_code=400, detail=result.get("message", "Failed to stop"))
        else:
            raise HTTPException(status_code=400, detail=f"Invalid action: {payload.action}. Use 'start' or 'stop'.")

        return service.get_status()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Control command failed: {exc}") from exc


@router.post("/monitor/mark-bought")
def mark_bought(
    payload: MarkBoughtRequest,
    service: MonitorService = Depends(get_monitor_service_dependency),
) -> dict:
    """Mark a symbol as bought.

    Args:
        payload: Request with symbol to mark as bought.
    """
    try:
        result = service.mark_bought(payload.symbol)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message", "Failed to mark bought"))
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Mark bought failed: {exc}") from exc
