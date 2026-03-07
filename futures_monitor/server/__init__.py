"""
role: Server package bootstrap and public exports for HTTP and WS layers.
depends:
  - futures_monitor.server.app
exports:
  - create_app
  - app
status: PENDING
functions:
  - create_app() -> FastAPI
"""

from .app import app, create_app

__all__ = ["create_app", "app"]
