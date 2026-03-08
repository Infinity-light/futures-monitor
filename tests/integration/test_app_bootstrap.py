import asyncio
import unittest
from unittest.mock import MagicMock, patch

from futures_monitor.server.__main__ import main


class TestAppBootstrap(unittest.TestCase):
    def test_server_entrypoint_invokes_uvicorn_run(self) -> None:
        with patch("sys.argv", ["server", "--host", "127.0.0.1", "--port", "8123"]):
            with patch("uvicorn.run") as mock_run:
                exit_code = main()

        self.assertEqual(exit_code, 0)
        mock_run.assert_called_once()
        _, kwargs = mock_run.call_args
        self.assertEqual(kwargs["host"], "127.0.0.1")
        self.assertEqual(kwargs["port"], 8123)
        self.assertEqual(kwargs["reload"], False)

    def test_create_app_startup_wires_monitor_service(self) -> None:
        from futures_monitor.server.app import create_app

        mock_service = MagicMock()
        mock_hub = object()

        with patch("futures_monitor.server.app.get_monitor_service", return_value=mock_service):
            with patch("futures_monitor.server.app.get_hub", return_value=mock_hub):
                with patch("futures_monitor.server.app.configure_static_host", return_value=None):
                    app = create_app()
                    startup_handler = next(
                        route for route in app.router.on_startup if route.__name__ == "startup_event"
                    )
                    asyncio.run(startup_handler())

        mock_service.set_hub.assert_called_once_with(mock_hub)
        mock_service.set_event_loop.assert_called_once()


if __name__ == "__main__":
    unittest.main()
