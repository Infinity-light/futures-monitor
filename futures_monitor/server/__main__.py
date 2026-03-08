"""
---
role: Provide the single-service runtime entrypoint for the FastAPI API, WebSocket, and static host.
depends:
  - argparse.ArgumentParser
  - logging.basicConfig
  - os.getenv
  - sys.exit
  - uvicorn.run
exports:
  - setup_logging
  - main
status: VERIFIED
functions:
  - setup_logging() -> None
  - main() -> int
---
"""

from __future__ import annotations

import argparse
import logging
import os
import sys


DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8000
APP_IMPORT = "futures_monitor.server.app:app"


def setup_logging() -> None:
    """Configure logging for the single-service runtime entrypoint."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def main() -> int:
    """Parse CLI arguments and launch the FastAPI application via uvicorn."""
    parser = argparse.ArgumentParser(
        description="Futures Monitor single-service server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--host", default=os.getenv("APP_HOST", DEFAULT_HOST), help="Host to bind the server to")
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("APP_PORT", str(DEFAULT_PORT))),
        help="Port to bind the server to",
    )
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes (ignored if --reload is set)",
    )

    args = parser.parse_args()

    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        import uvicorn
    except ImportError:
        logger.error("uvicorn is required to run the server. Install it with: pip install uvicorn[standard]")
        return 1

    logger.info("Starting Futures Monitor single-service server on %s:%s", args.host, args.port)
    uvicorn.run(
        APP_IMPORT,
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1,
        log_level="info",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
