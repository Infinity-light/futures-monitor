"""
---
role: Resolve Vue build assets and register SPA fallback routes for FastAPI single-service delivery.
depends:
  - os.getenv
  - pathlib.Path
  - fastapi.FastAPI
  - fastapi.responses.FileResponse
  - fastapi.responses.HTMLResponse
  - fastapi.staticfiles.StaticFiles
exports:
  - STATIC_ROOT_ENV
  - PLACEHOLDER_HTML
  - resolve_static_root
  - configure_static_host
status: VERIFIED
functions:
  - resolve_static_root() -> Path | None
  - configure_static_host(app: FastAPI) -> Path | None
---
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

STATIC_ROOT_ENV = "FUTURES_MONITOR_STATIC_DIR"
PLACEHOLDER_HTML = """<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Futures Monitor</title>
  </head>
  <body>
    <main>
      <h1>Futures Monitor frontend is not built yet.</h1>
      <p>Run the Vue build to serve the production interface from this FastAPI service.</p>
    </main>
  </body>
</html>
"""
_DEFAULT_STATIC_CANDIDATES = (
    Path(__file__).resolve().parents[1] / "web_dist",
    Path(__file__).resolve().parents[1] / "web" / "dist",
)


def resolve_static_root() -> Path | None:
    """Resolve the preferred static asset directory for single-service delivery."""
    configured = os.getenv(STATIC_ROOT_ENV)
    if configured:
        candidate = Path(configured).expanduser().resolve()
        return candidate if candidate.is_dir() else None

    for candidate in _DEFAULT_STATIC_CANDIDATES:
        if candidate.is_dir():
            return candidate
    return None


def configure_static_host(app: FastAPI) -> Path | None:
    """Register static file delivery and SPA fallback routes for the single-service app."""
    static_root = resolve_static_root()
    index_file = static_root / "index.html" if static_root is not None else None

    assets_dir = static_root / "assets" if static_root is not None else None
    if assets_dir is not None and assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="frontend-assets")

    @app.get("/", include_in_schema=False, response_model=None)
    async def serve_root() -> Response:
        if index_file is not None and index_file.is_file():
            return FileResponse(index_file)
        return HTMLResponse(PLACEHOLDER_HTML, status_code=200)

    @app.get("/{requested_path:path}", include_in_schema=False, response_model=None)
    async def serve_spa_entry(requested_path: str) -> Response:
        normalized_path = requested_path.strip("/")
        if not normalized_path:
            return await serve_root()

        if normalized_path == "assets" or normalized_path.startswith("assets/"):
            if static_root is None:
                raise HTTPException(status_code=404, detail="Frontend assets are not available")
            asset_target = static_root / normalized_path
            if asset_target.is_file():
                return FileResponse(asset_target)
            raise HTTPException(status_code=404, detail="Frontend asset not found")

        if index_file is not None and index_file.is_file():
            candidate = static_root / normalized_path
            if candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(index_file)

        return HTMLResponse(PLACEHOLDER_HTML, status_code=200)

    return static_root
