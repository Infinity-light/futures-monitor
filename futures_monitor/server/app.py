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
status: IMPLEMENTED
functions:
  - create_app() -> FastAPI
---
"""

import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .api.config_api import router as config_router
from .api.monitor_api import router as monitor_router
from .schemas import HealthResponse
from .ws.hub import get_hub
from .services.monitor_service import get_monitor_service

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title="Futures Monitor API",
        version="0.1.0",
        description="Backend API for futures breakout monitoring system",
    )

    # Add CORS middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",  # Vite dev server
            "http://localhost:3000",  # Common dev server
            "http://localhost:8080",  # Another common dev server
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

    # Include API routers
    application.include_router(config_router, prefix="/api")
    application.include_router(monitor_router, prefix="/api")

    @application.websocket("/ws/events")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        """WebSocket endpoint for real-time events.

        Clients can connect to this endpoint to receive:
        - Log messages
        - Symbol row updates
        - Connection status changes
        - Running status changes
        """
        hub = get_hub()
        await websocket.accept()
        await hub.register(websocket)

        try:
            # Send initial connection confirmation
            await websocket.send_json({
                "type": "connected",
                "message": "WebSocket connected successfully",
            })

            # Keep connection alive and handle client messages
            while True:
                try:
                    # Wait for messages from client (with timeout)
                    data = await websocket.receive_text()
                    logger.debug(f"Received WebSocket message: {data}")

                    # Echo back for ping/pong
                    await websocket.send_json({
                        "type": "pong",
                        "received": data,
                    })
                except WebSocketDisconnect:
                    break
                except Exception as exc:
                    logger.warning(f"WebSocket error: {exc}")
                    break
        finally:
            await hub.unregister(websocket)

    @application.on_event("startup")
    async def startup_event() -> None:
        """Application startup handler."""
        logger.info("Futures Monitor API starting up...")

        # Initialize services
        monitor_service = get_monitor_service()
        hub = get_hub()
        monitor_service.set_hub(hub)

        logger.info("Futures Monitor API started successfully")

    @application.on_event("shutdown")
    async def shutdown_event() -> None:
        """Application shutdown handler."""
        logger.info("Futures Monitor API shutting down...")

        # Stop monitoring if running
        monitor_service = get_monitor_service()
        if monitor_service._running:
            monitor_service.stop()

        logger.info("Futures Monitor API shutdown complete")

    return application


# Global app instance for uvicorn
app = create_app()
