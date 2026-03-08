import unittest

from futures_monitor.server.schemas import (
    ConfigDTO,
    HealthResponse,
    MonitorControlRequest,
    MonitorStatus,
    SymbolRow,
)


class TestServerSchemas(unittest.TestCase):
    def test_health_response_instantiation(self) -> None:
        payload = HealthResponse()
        self.assertEqual(payload.message, "ok")
        self.assertEqual(payload.status, "ok")

    def test_monitor_status_instantiation(self) -> None:
        payload = MonitorStatus(running=True, symbols=["SHFE.rb2405"], connection_status="connected")
        self.assertTrue(payload.running)
        self.assertEqual(payload.symbols, ["SHFE.rb2405"])
        self.assertEqual(payload.connection_status, "connected")

    def test_monitor_control_request_instantiation(self) -> None:
        payload = MonitorControlRequest(action="start")
        self.assertEqual(payload.action, "start")

    def test_symbol_row_uses_frontend_field_names(self) -> None:
        payload = SymbolRow(
            symbol="SHFE.rb2405",
            status="BREAKOUT_DETECTED",
            last_price=3512.5,
            take_profit=3550.0,
            stop_loss=3490.0,
            has_bought=False,
        )
        self.assertEqual(payload.status, "BREAKOUT_DETECTED")
        self.assertEqual(payload.last_price, 3512.5)
        self.assertEqual(payload.take_profit, 3550.0)
        self.assertEqual(payload.stop_loss, 3490.0)

    def test_config_dto_instantiation(self) -> None:
        payload = ConfigDTO(poll_interval=10, symbols=["SHFE.rb2405", "DCE.i2405"])
        self.assertEqual(payload.poll_interval, 10)
        self.assertEqual(payload.symbols, ["SHFE.rb2405", "DCE.i2405"])


if __name__ == "__main__":
    unittest.main()
