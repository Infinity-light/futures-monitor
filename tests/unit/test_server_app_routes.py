import unittest

from fastapi.testclient import TestClient

from futures_monitor.server.app import create_app


class TestServerAppRoutes(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(create_app())

    def test_health_route_accessible(self) -> None:
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("message"), "ok")

    def test_monitor_status_route_is_stable(self) -> None:
        response = self.client.get("/api/monitor/status")
        self.assertIn(response.status_code, (200, 501))


if __name__ == "__main__":
    unittest.main()
