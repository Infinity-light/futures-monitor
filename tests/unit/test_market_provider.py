import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from futures_monitor.config import AppConfig
from futures_monitor.market import MarketDataProvider
from futures_monitor.utils.logger import get_logger


class TestMarketDataProvider(unittest.TestCase):
    def test_mock_mode_streams_data(self) -> None:
        cfg = AppConfig(use_real_market_data=False)
        provider = MarketDataProvider(config=cfg, logger=get_logger("test.market.mock"))

        rows = list(provider.stream_1m_klines(["SHFE.rb"], max_updates=4, selection_mode='custom'))

        self.assertGreaterEqual(len(rows), 4)
        symbols = [s for s, _ in rows]
        self.assertTrue(all(s == "SHFE.rb" for s in symbols))

    def test_strict_real_mode_raises_when_auth_missing(self) -> None:
        cfg = AppConfig(use_real_market_data=True, strict_real_mode=True, tq_account="", tq_password="")
        provider = MarketDataProvider(config=cfg, logger=get_logger("test.market.strict"))

        with self.assertRaisesRegex(ValueError, "可用于 TqSdk/快期认证的快期账户"):
            list(provider.stream_1m_klines(["SHFE.rb"], max_updates=1, selection_mode='custom'))

    def test_non_strict_real_mode_fallbacks_to_mock_when_auth_missing(self) -> None:
        cfg = AppConfig(use_real_market_data=True, strict_real_mode=False, tq_account="", tq_password="")
        logger = get_logger("test.market.fallback")
        provider = MarketDataProvider(config=cfg, logger=logger)

        with patch.object(logger, "warning") as mocked_warning:
            rows = list(provider.stream_1m_klines(["SHFE.rb"], max_updates=2, selection_mode='custom'))

        self.assertEqual(len(rows), 2)
        self.assertGreaterEqual(mocked_warning.call_count, 1)
        self.assertIn("fallback to mock", mocked_warning.call_args_list[0].args[0])
        self.assertIn("可用于 TqSdk/快期认证的快期账户", str(mocked_warning.call_args_list[0].args[1]))

    def test_get_latest_snapshot_returns_latest(self) -> None:
        cfg = AppConfig(use_real_market_data=False)
        provider = MarketDataProvider(config=cfg, logger=get_logger("test.market.snapshot"))

        rows = list(provider.stream_1m_klines(["SHFE.rb", "DCE.m"], max_updates=3, selection_mode='custom'))
        self.assertGreaterEqual(len(rows), 3)

        snap = provider.get_latest_snapshot(["SHFE.rb", "DCE.m"])
        self.assertIn("SHFE.rb", snap)

    def test_custom_selection_filters_all_label_like_values(self) -> None:
        cfg = AppConfig(use_real_market_data=False)
        provider = MarketDataProvider(config=cfg, logger=get_logger("test.market.filter"))

        rows = list(
            provider.stream_1m_klines(
                ["ALL 全部品种（自动读取当前有效合约）", "SHFE.rb"],
                max_updates=2,
                selection_mode='custom',
            )
        )

        self.assertEqual({symbol for symbol, _ in rows}, {"SHFE.rb"})

    def test_resolve_real_symbols_maps_program_values_to_active_contracts(self) -> None:
        cfg = AppConfig(use_real_market_data=True, tq_account='demo', tq_password='demo')
        provider = MarketDataProvider(config=cfg, logger=get_logger("test.market.resolve"))

        class FakeApi:
            def get_quote(self, symbol: str):
                mapping = {
                    'SHFE.rb': SimpleNamespace(underlying_symbol='SHFE.rb2405'),
                    'DCE.i': SimpleNamespace(underlying_symbol='DCE.i2409'),
                }
                return mapping.get(symbol, SimpleNamespace(underlying_symbol=''))

        resolved = provider._resolve_real_symbols(['SHFE.rb', 'DCE.i'], api=FakeApi(), selection_mode='custom')

        self.assertEqual(resolved, ['SHFE.rb2405', 'DCE.i2409'])

    def test_get_symbol_metadata_prefers_product_name_for_active_contract(self) -> None:
        cfg = AppConfig(use_real_market_data=False)
        provider = MarketDataProvider(config=cfg, logger=get_logger("test.market.metadata"))

        metadata = provider.get_symbol_metadata('SHFE.rb2405')

        self.assertEqual(metadata['display_symbol'], 'SHFE.rb')
        self.assertEqual(metadata['name'], '螺纹钢')
        self.assertEqual(metadata['exchange'], 'SHFE')

    def test_resolve_symbols_prepares_exchange_mode_symbols_in_mock_mode(self) -> None:
        cfg = AppConfig(use_real_market_data=False)
        provider = MarketDataProvider(config=cfg, logger=get_logger("test.market.resolve.mock"))

        resolved = provider.resolve_symbols([], selection_mode='exchange', selection_exchanges=['DCE'])

        self.assertEqual(resolved, ['DCE.i', 'DCE.m'])


if __name__ == "__main__":
    unittest.main()
