import unittest

from futures_monitor.server.schemas import (
    ConfigDTO,
    HealthResponse,
    MonitorControlRequest,
    MonitorStatus,
)


class TestServerSchemas(unittest.TestCase):
    def test_health_response_instantiation(self) -> None:
        payload = HealthResponse()
        self.assertEqual(payload.message, "ok")

    def test_monitor_status_instantiation(self) -> None:
        payload = MonitorStatus(running=True, symbols=["SHFE.rb2405"])
        self.assertTrue(payload.running)
        self.assertEqual(payload.symbols, ["SHFE.rb2405"])

    def test_monitor_control_request_instantiation(self) -> None:
        payload = MonitorControlRequest(action="start")
        self.assertEqual(payload.action, "start")

    def test_config_dto_instantiation(self) -> None:
        payload = ConfigDTO(poll_interval=10, symbols=["SHFE.rb2405", "DCE.i2405"])
        self.assertEqual(payload.poll_interval, 10)
        self.assertEqual(payload.symbols, ["SHFE.rb2405", "DCE.i2405"])


if __name__ == "__main__":
    unittest.main()
