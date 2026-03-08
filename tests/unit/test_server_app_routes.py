import unittest
from unittest.mock import patch

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
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("running", payload)
        self.assertIn("connection_status", payload)
        self.assertIn("rows", payload)

    def test_mark_bought_uses_request_body_contract(self) -> None:
        response = self.client.post("/api/monitor/mark-bought", json={"symbol": "SHFE.rb2405"})
        self.assertIn(response.status_code, (200, 400))

    def test_websocket_uses_wrapped_contract_messages(self) -> None:
        with self.client.websocket_connect("/ws/events") as websocket:
            connected_message = websocket.receive_json()
            websocket.send_text("ping")
            pong_message = websocket.receive_json()

        self.assertEqual(connected_message["type"], "connection")
        self.assertEqual(connected_message["data"]["status"], "connected")
        self.assertEqual(pong_message["type"], "pong")
        self.assertEqual(pong_message["data"]["received"], "ping")


if __name__ == "__main__":
    unittest.main()
