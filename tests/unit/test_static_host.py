import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from futures_monitor.server.static_host import (
    PLACEHOLDER_HTML,
    STATIC_ROOT_ENV,
    configure_static_host,
    resolve_static_root,
)


class TestStaticHost(unittest.TestCase):
    def test_resolve_static_root_prefers_env_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {STATIC_ROOT_ENV: temp_dir}, clear=False):
                resolved = resolve_static_root()

        self.assertEqual(resolved, Path(temp_dir).resolve())

    def test_configure_static_host_serves_index_and_spa_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            static_root = Path(temp_dir)
            assets_dir = static_root / "assets"
            assets_dir.mkdir()
            index_file = static_root / "index.html"
            index_file.write_text("<html><body>single-service shell</body></html>", encoding="utf-8")
            asset_file = assets_dir / "app.js"
            asset_file.write_text("console.log('ready')", encoding="utf-8")
            robots_file = static_root / "robots.txt"
            robots_file.write_text("User-agent: *\nDisallow:", encoding="utf-8")

            app = FastAPI()
            with patch.dict(os.environ, {STATIC_ROOT_ENV: temp_dir}, clear=False):
                configured_root = configure_static_host(app)

            client = TestClient(app)
            root_response = client.get("/")
            spa_response = client.get("/dashboard")
            asset_response = client.get("/assets/app.js")
            file_response = client.get("/robots.txt")
            missing_asset_response = client.get("/assets/missing.js")

        self.assertEqual(configured_root, static_root.resolve())
        self.assertEqual(root_response.status_code, 200)
        self.assertIn("single-service shell", root_response.text)
        self.assertEqual(spa_response.status_code, 200)
        self.assertIn("single-service shell", spa_response.text)
        self.assertEqual(asset_response.status_code, 200)
        self.assertIn("console.log('ready')", asset_response.text)
        self.assertEqual(file_response.status_code, 200)
        self.assertIn("User-agent", file_response.text)
        self.assertEqual(missing_asset_response.status_code, 404)

    def test_configure_static_host_returns_placeholder_when_dist_missing(self) -> None:
        app = FastAPI()
        missing_dir = str(Path(tempfile.gettempdir()) / "futures-monitor-missing-dist")
        with patch.dict(os.environ, {STATIC_ROOT_ENV: missing_dir}, clear=False):
            configured_root = configure_static_host(app)

        client = TestClient(app)
        root_response = client.get("/")
        spa_response = client.get("/dashboard")
        assets_response = client.get("/assets/app.js")

        self.assertIsNone(configured_root)
        self.assertEqual(root_response.status_code, 200)
        self.assertEqual(spa_response.status_code, 200)
        self.assertIn("frontend is not built yet", root_response.text)
        self.assertEqual(root_response.text.strip(), PLACEHOLDER_HTML.strip())
        self.assertEqual(spa_response.text.strip(), PLACEHOLDER_HTML.strip())
        self.assertEqual(assets_response.status_code, 404)
        self.assertEqual(assets_response.json()["detail"], "Frontend assets are not available")


if __name__ == "__main__":
    unittest.main()
