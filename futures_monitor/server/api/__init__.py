"""
role: API router package exports.
depends:
  - futures_monitor.server.api.config_api
  - futures_monitor.server.api.monitor_api
exports:
  - config_router
  - monitor_router
status: PENDING
functions:
  - none
"""

from .config_api import router as config_router
from .monitor_api import router as monitor_router

__all__ = ["config_router", "monitor_router"]
