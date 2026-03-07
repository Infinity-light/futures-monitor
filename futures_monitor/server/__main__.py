"""
Entry point for running the Futures Monitor API server.

Usage:
    python -m futures_monitor.server
    python -m futures_monitor.server --host 0.0.0.0 --port 8000
    python -m futures_monitor.server --reload  # Enable auto-reload for development
"""

from __future__ import annotations

import argparse
import logging
import sys


def setup_logging() -> None:
    """Configure logging for the server."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )


def main() -> int:
    """Main entry point for the server."""
    parser = argparse.ArgumentParser(
        description="Futures Monitor API Server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind the server to",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the server to",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )
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
        logger.error(
            "uvicorn is required to run the server. "
            "Install it with: pip install uvicorn[standard]"
        )
        return 1

    logger.info(f"Starting Futures Monitor API server on {args.host}:{args.port}")

    uvicorn.run(
        "futures_monitor.server.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1,
        log_level="info",
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
