"""
role: WebSocket package exports for connection hub contract.
depends:
  - futures_monitor.server.ws.hub.ConnectionHub
exports:
  - ConnectionHub
status: VERIFIED
functions:
  - none
"""

from .hub import ConnectionHub

__all__ = ["ConnectionHub"]
