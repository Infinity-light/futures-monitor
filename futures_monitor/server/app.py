"""
---
role: Compose FastAPI application and register API routes.
depends:
  - fastapi.FastAPI
  - fastapi.WebSocket
  - fastapi.WebSocketDisconnect
  - fastapi.middleware.cors.CORSMiddleware
  - futures_monitor.server.api.config_api.router
  - futures_monitor.server.api.monitor_api.router
  - futures_monitor.server.ws.hub.ConnectionHub
  - futures_monitor.server.ws.hub.get_hub
  - futures_monitor.server.services.monitor_service.get_monitor_service
exports:
  - create_app
  - app
status: VERIFIED
functions:
  - create_app() -> FastAPI
---
"""

import asyncio
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .api.config_api import router as config_router
from .api.monitor_api import router as monitor_router
from .schemas import HealthResponse
from .static_host import configure_static_host
from .services.monitor_service import get_monitor_service
from .ws.hub import get_hub

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title="Futures Monitor API",
        version="0.1.0",
        description="Backend API for futures breakout monitoring system",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://localhost:3000",
            "http://localhost:8080",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8080",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.get("/api/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        """Health check endpoint."""
        return HealthResponse()

    application.include_router(config_router, prefix="/api")
    application.include_router(monitor_router, prefix="/api")

    static_root = configure_static_host(application)
    if static_root is not None:
        logger.info("Serving frontend assets from %s", static_root)
    else:
        logger.info("Frontend build not found; serving placeholder root response")

    @application.websocket("/ws/events")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        """WebSocket endpoint for real-time events."""
        hub = get_hub()
        await websocket.accept()
        await hub.register(websocket)

        try:
            await websocket.send_json({
                "type": "connection",
                "data": {"status": "connected"},
            })

            while True:
                try:
                    data = await websocket.receive_text()
                    logger.debug("Received WebSocket message: %s", data)
                    await websocket.send_json({
                        "type": "pong",
                        "data": {"received": data},
                    })
                except WebSocketDisconnect:
                    break
                except Exception as exc:
                    logger.warning("WebSocket error: %s", exc)
                    break
        finally:
            await hub.unregister(websocket)

    @application.on_event("startup")
    async def startup_event() -> None:
        """Application startup handler."""
        logger.info("Futures Monitor API starting up...")
        monitor_service = get_monitor_service()
        hub = get_hub()
        monitor_service.set_hub(hub)
        monitor_service.set_event_loop(asyncio.get_running_loop())
        logger.info("Futures Monitor API started successfully")

    @application.on_event("shutdown")
    async def shutdown_event() -> None:
        """Application shutdown handler."""
        logger.info("Futures Monitor API shutting down...")
        monitor_service = get_monitor_service()
        if monitor_service._running:
            monitor_service.stop()
        logger.info("Futures Monitor API shutdown complete")

    return application


app = create_app()
