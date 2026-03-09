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

from ..schemas import ErrorResponse, MarkBoughtRequest, MonitorControlRequest, MonitorStatus
from ..services.monitor_service import MonitorService, get_monitor_service

router = APIRouter(tags=["monitor"])


_AUTH_HINT = (
    "请确认填写的是可用于 TqSdk/快期认证的快期账户（手机号、邮箱或用户名）和对应密码，"
    "不是期货实盘账号，也不是普通模拟交易编号。"
)


def _raise_client_error(detail: str, status_code: int = 400, hint: str | None = None) -> None:
    raise HTTPException(status_code=status_code, detail={"detail": detail, "hint": hint})


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


@router.post(
    "/monitor/control",
    response_model=MonitorStatus,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def control_monitor(
    payload: MonitorControlRequest,
    service: MonitorService = Depends(get_monitor_service_dependency),
) -> MonitorStatus:
    """Control the monitor - start or stop monitoring."""
    try:
        if payload.action == "start":
            result = service.start(
                payload.symbols,
                selection_mode=payload.selection_mode,
                selection_exchanges=payload.selection_exchanges,
            )
            if not result.get("success"):
                detail = str(result.get("message", "启动监控失败"))
                hint = _AUTH_HINT if "快期" in detail or "TqSdk" in detail or "认证" in detail else None
                _raise_client_error(detail=detail, hint=hint)
        elif payload.action == "stop":
            result = service.stop()
            if not result.get("success"):
                _raise_client_error(detail=str(result.get("message", "停止监控失败")))
        else:
            _raise_client_error(detail=f"无效操作：{payload.action}。仅支持 start 或 stop。")

        return service.get_status()
    except HTTPException:
        raise
    except Exception as exc:
        detail = str(exc)
        hint = _AUTH_HINT if "快期" in detail or "TqSdk" in detail or "认证" in detail else None
        _raise_client_error(detail=f"启动或停止监控失败：{detail}", status_code=500, hint=hint)


@router.post("/monitor/mark-bought")
def mark_bought(
    payload: MarkBoughtRequest,
    service: MonitorService = Depends(get_monitor_service_dependency),
) -> dict:
    """Mark a symbol as bought."""
    try:
        result = service.mark_bought(payload.symbol)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message", "Failed to mark bought"))
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Mark bought failed: {exc}") from exc
