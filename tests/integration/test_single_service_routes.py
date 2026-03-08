import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from futures_monitor.server.app import create_app


class TestSingleServiceRoutes(unittest.TestCase):
    def test_api_health_is_available(self) -> None:
        with patch.dict(os.environ, {}, clear=False):
            client = TestClient(create_app())
            response = client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("message"), "ok")

    def test_root_path_returns_placeholder_when_dist_missing(self) -> None:
        missing_dir = str(Path(tempfile.gettempdir()) / "futures-monitor-missing-dist")
        with patch.dict(os.environ, {"FUTURES_MONITOR_STATIC_DIR": missing_dir}, clear=False):
            client = TestClient(create_app())
            response = client.get("/")
            history_response = client.get("/dashboard")

        self.assertEqual(response.status_code, 200)
        self.assertIn("frontend is not built yet", response.text)
        self.assertEqual(history_response.status_code, 200)
        self.assertIn("frontend is not built yet", history_response.text)

    def test_root_path_returns_built_page_when_dist_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            static_root = Path(temp_dir)
            (static_root / "assets").mkdir()
            (static_root / "index.html").write_text("<html><body>built frontend</body></html>", encoding="utf-8")
            (static_root / "assets" / "app.js").write_text("console.log('built')", encoding="utf-8")

            with patch.dict(os.environ, {"FUTURES_MONITOR_STATIC_DIR": temp_dir}, clear=False):
                client = TestClient(create_app())
                root_response = client.get("/")
                history_response = client.get("/positions/open")
                asset_response = client.get("/assets/app.js")

        self.assertEqual(root_response.status_code, 200)
        self.assertIn("built frontend", root_response.text)
        self.assertEqual(history_response.status_code, 200)
        self.assertIn("built frontend", history_response.text)
        self.assertEqual(asset_response.status_code, 200)
        self.assertIn("console.log('built')", asset_response.text)

    def test_websocket_events_allows_connection(self) -> None:
        missing_dir = str(Path(tempfile.gettempdir()) / "futures-monitor-missing-dist")
        with patch.dict(os.environ, {"FUTURES_MONITOR_STATIC_DIR": missing_dir}, clear=False):
            client = TestClient(create_app())
            with client.websocket_connect("/ws/events") as websocket:
                connected_message = websocket.receive_json()
                websocket.send_text("ping")
                pong_message = websocket.receive_json()

        self.assertEqual(connected_message.get("type"), "connection")
        self.assertEqual(connected_message.get("data", {}).get("status"), "connected")
        self.assertEqual(pong_message.get("type"), "pong")
        self.assertEqual(pong_message.get("data", {}).get("received"), "ping")


if __name__ == "__main__":
    unittest.main()
