import asyncio
import tempfile
import unittest
from pathlib import Path
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
        mock_config_service = MagicMock()
        mock_hub = object()

        with patch("futures_monitor.server.app.get_monitor_service", return_value=mock_service):
            with patch("futures_monitor.server.app.get_config_service", return_value=mock_config_service):
                with patch("futures_monitor.server.app.get_hub", return_value=mock_hub):
                    with patch("futures_monitor.server.app.configure_static_host", return_value=None):
                        app = create_app()
                        startup_handler = next(
                            route for route in app.router.on_startup if route.__name__ == "startup_event"
                        )
                        asyncio.run(startup_handler())

        mock_config_service.set_monitor_service.assert_called_once_with(mock_service)
        mock_service.set_hub.assert_called_once_with(mock_hub)
        mock_service.set_event_loop.assert_called_once()

    def test_default_singletons_can_boot_with_runtime_config_env(self) -> None:
        from futures_monitor.server.app import create_app

        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_path = Path(temp_dir) / 'persistent' / 'config.json'
            template_path = Path(temp_dir) / 'repository-config.json'
            template_path.write_text(
                '{"symbols": ["SHFE.rb"], "selection_mode": "custom", "selection_symbols": ["SHFE.rb"]}',
                encoding='utf-8',
            )

            with patch.dict(
                'os.environ',
                {
                    'FUTURES_MONITOR_RUNTIME_CONFIG': str(runtime_path),
                    'FUTURES_MONITOR_CONFIG_TEMPLATE': str(template_path),
                },
                clear=False,
            ):
                from futures_monitor.server.services import config_service as config_module
                from futures_monitor.server.services import monitor_service as monitor_module

                original_monitor = monitor_module._monitor_service_instance
                original_config = config_module._config_service_instance
                monitor_module._monitor_service_instance = None
                config_module._config_service_instance = None
                try:
                    with patch('futures_monitor.server.app.configure_static_host', return_value=None):
                        app = create_app()
                        startup_handler = next(
                            route for route in app.router.on_startup if route.__name__ == 'startup_event'
                        )
                        asyncio.run(startup_handler())
                        resolved_monitor = monitor_module.get_monitor_service()
                        resolved_config = config_module.get_config_service()
                        runtime_exists = runtime_path.exists()
                finally:
                    monitor_module._monitor_service_instance = original_monitor
                    config_module._config_service_instance = original_config

            self.assertEqual(Path(resolved_monitor._config_path), runtime_path)
            self.assertEqual(Path(resolved_config._config_path), runtime_path)
            self.assertTrue(runtime_exists)


if __name__ == "__main__":
    unittest.main()
