import unittest

from futures_monitor.server.schemas import (
    ConfigDTO,
    ErrorResponse,
    HealthResponse,
    MonitorControlRequest,
    MonitorStatus,
    SymbolCandidate,
    SymbolRow,
)


class TestServerSchemas(unittest.TestCase):
    def test_health_response_instantiation(self) -> None:
        payload = HealthResponse()
        self.assertEqual(payload.message, "ok")
        self.assertEqual(payload.status, "ok")

    def test_monitor_status_instantiation(self) -> None:
        payload = MonitorStatus(
            running=True,
            symbols=["SHFE.rb"],
            selection_mode="custom",
            selection_exchanges=["SHFE"],
            connection_status="connected",
        )
        self.assertTrue(payload.running)
        self.assertEqual(payload.symbols, ["SHFE.rb"])
        self.assertEqual(payload.selection_mode, "custom")
        self.assertEqual(payload.selection_exchanges, ["SHFE"])
        self.assertEqual(payload.connection_status, "connected")

    def test_monitor_control_request_instantiation(self) -> None:
        payload = MonitorControlRequest(action="start", symbols=["SHFE.rb"], selection_mode="custom")
        self.assertEqual(payload.action, "start")
        self.assertEqual(payload.symbols, ["SHFE.rb"])
        self.assertEqual(payload.selection_mode, "custom")

    def test_symbol_row_uses_frontend_field_names(self) -> None:
        payload = SymbolRow(
            symbol="SHFE.rb2405",
            display_symbol="SHFE.rb",
            name="螺纹钢",
            exchange="SHFE",
            status="BREAKOUT_DETECTED",
            last_price=3512.5,
            take_profit=3550.0,
            stop_loss=3490.0,
            has_bought=False,
        )
        self.assertEqual(payload.display_symbol, "SHFE.rb")
        self.assertEqual(payload.name, "螺纹钢")
        self.assertEqual(payload.exchange, "SHFE")
        self.assertEqual(payload.status, "BREAKOUT_DETECTED")
        self.assertEqual(payload.last_price, 3512.5)
        self.assertEqual(payload.take_profit, 3550.0)
        self.assertEqual(payload.stop_loss, 3490.0)

    def test_config_dto_instantiation(self) -> None:
        payload = ConfigDTO(
            symbols=["ALL"],
            selection_mode="exchange",
            selection_exchanges=["SHFE"],
            selection_symbols=["SHFE.rb"],
            tq_account="demo-account",
            tq_password="demo-pass",
            use_real_market_data=True,
            strict_real_mode=False,
            symbol_candidates=[
                SymbolCandidate(value="SHFE.rb", code="SHFE.rb", name="螺纹钢", exchange="SHFE", category="上期所")
            ],
        )
        self.assertEqual(payload.symbols, ["ALL"])
        self.assertEqual(payload.selection_mode, "exchange")
        self.assertEqual(payload.selection_exchanges, ["SHFE"])
        self.assertEqual(payload.selection_symbols, ["SHFE.rb"])
        self.assertEqual(payload.tq_account, "demo-account")
        self.assertEqual(payload.tq_password, "demo-pass")
        self.assertTrue(payload.use_real_market_data)
        self.assertFalse(payload.strict_real_mode)
        self.assertEqual(payload.symbol_candidates[0].name, "螺纹钢")

    def test_error_response_supports_detail_and_hint(self) -> None:
        payload = ErrorResponse(detail="认证失败", hint="请填写快期账户")
        self.assertEqual(payload.detail, "认证失败")
        self.assertEqual(payload.hint, "请填写快期账户")


if __name__ == "__main__":
    unittest.main()
