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

    def test_resolve_all_real_symbols_prefers_cont_quotes_direct_symbols(self) -> None:
        cfg = AppConfig(use_real_market_data=True, tq_account='demo', tq_password='demo')
        provider = MarketDataProvider(config=cfg, logger=get_logger("test.market.resolve.cont"))

        class FakeApi:
            def __init__(self) -> None:
                self.query_quotes_called = False

            def query_cont_quotes(self, **kwargs):
                self.query_cont_quotes_kwargs = kwargs
                return ['SHFE.rb2605', 'SHFE.bu2604']

            def query_quotes(self, **kwargs):
                self.query_quotes_called = True
                return ['SHFE.rb2601', 'SHFE.rb2605', 'SHFE.bu2604']

        api = FakeApi()

        resolved = provider._resolve_all_real_symbols(api)

        self.assertEqual(resolved, ['SHFE.rb2605', 'SHFE.bu2604'])
        self.assertEqual(api.query_cont_quotes_kwargs, {})
        self.assertFalse(api.query_quotes_called)

    def test_resolve_all_real_symbols_falls_back_only_when_cont_quotes_empty(self) -> None:
        cfg = AppConfig(use_real_market_data=True, tq_account='demo', tq_password='demo')
        provider = MarketDataProvider(config=cfg, logger=get_logger("test.market.resolve.fallback"))

        class FakeApi:
            def __init__(self) -> None:
                self.query_quotes_called = False

            def query_cont_quotes(self, **kwargs):
                self.query_cont_quotes_kwargs = kwargs
                return []

            def query_quotes(self, **kwargs):
                self.query_quotes_called = True
                self.query_quotes_kwargs = kwargs
                return ['SHFE.rb2601', 'SHFE.rb2605', 'SHFE.bu2604']

        api = FakeApi()

        resolved = provider._resolve_all_real_symbols(api, exchange_id='SHFE')

        self.assertTrue(api.query_quotes_called)
        self.assertEqual(api.query_cont_quotes_kwargs, {'exchange_id': 'SHFE'})
        self.assertEqual(
            api.query_quotes_kwargs,
            {'ins_class': 'FUTURE', 'expired': False, 'exchange_id': 'SHFE'},
        )
        self.assertEqual(resolved, ['SHFE.rb2601', 'SHFE.rb2605', 'SHFE.bu2604'])

    def test_resolve_real_symbols_exchange_mode_uses_active_contracts_only(self) -> None:
        cfg = AppConfig(use_real_market_data=True, tq_account='demo', tq_password='demo')
        provider = MarketDataProvider(config=cfg, logger=get_logger("test.market.resolve.exchange"))

        class FakeApi:
            def __init__(self) -> None:
                self.query_quotes_called = False

            def query_cont_quotes(self, **kwargs):
                exchange_id = kwargs.get('exchange_id')
                if exchange_id == 'SHFE':
                    return ['SHFE.rb2605', 'SHFE.bu2604']
                return []

            def query_quotes(self, **kwargs):
                self.query_quotes_called = True
                return ['SHFE.rb2601', 'SHFE.rb2605', 'SHFE.bu2601', 'SHFE.bu2604']

        api = FakeApi()

        resolved = provider._resolve_real_symbols([], api=api, selection_mode='exchange', selection_exchanges=['SHFE'])

        self.assertEqual(resolved, ['SHFE.rb2605', 'SHFE.bu2604'])
        self.assertFalse(api.query_quotes_called)

    def test_stream_real_yields_initial_rows_before_first_wait_update(self) -> None:
        cfg = AppConfig(use_real_market_data=True, tq_account='demo', tq_password='demo')
        provider = MarketDataProvider(config=cfg, logger=get_logger("test.market.real.init"))

        class FakeSeries:
            def __init__(self, rows):
                self._rows = rows
                self.iloc = self

            def __getitem__(self, index):
                return self._rows[index]

        fake_serials = {
            'SHFE.rb2405': FakeSeries(
                [
                    {'open': 100, 'high': 101, 'low': 99, 'close': 100.5, 'datetime': 1},
                    {'open': 101, 'high': 102, 'low': 100, 'close': 101.5, 'datetime': 2},
                    {'open': 102, 'high': 103, 'low': 101, 'close': 102.5, 'datetime': 3},
                    {'open': 103, 'high': 108, 'low': 97, 'close': 106.5, 'datetime': 4},
                ]
            ),
            'DCE.i2409': FakeSeries(
                [
                    {'open': 200, 'high': 201, 'low': 199, 'close': 200.5, 'datetime': 11},
                    {'open': 201, 'high': 202, 'low': 200, 'close': 201.5, 'datetime': 12},
                    {'open': 202, 'high': 203, 'low': 201, 'close': 202.5, 'datetime': 13},
                    {'open': 203, 'high': 208, 'low': 197, 'close': 206.5, 'datetime': 14},
                ]
            ),
        }

        class FakeApi:
            instances = []

            def __init__(self, auth=None) -> None:
                self.auth = auth
                self.wait_update_calls = 0
                self.closed = False
                self.serial_requests = []
                FakeApi.instances.append(self)

            def get_kline_serial(self, symbol: str, duration_seconds: int, data_length: int = 4):
                self.serial_requests.append((symbol, duration_seconds, data_length))
                return fake_serials[symbol]

            def wait_update(self):
                self.wait_update_calls += 1
                raise AssertionError('wait_update should not be called before first initial yield batch')

            def close(self):
                self.closed = True

        fake_tqsdk = SimpleNamespace(TqApi=FakeApi, TqAuth=lambda account, password: (account, password))

        with patch.dict('sys.modules', {'tqsdk': fake_tqsdk}), patch.object(
            provider, '_resolve_real_symbols', return_value=['SHFE.rb2405', 'DCE.i2409']
        ):
            rows = list(provider._stream_real(['SHFE.rb', 'DCE.i'], max_updates=2, selection_mode='custom'))

        self.assertEqual(len(rows), 2)
        self.assertEqual([symbol for symbol, _ in rows], ['SHFE.rb2405', 'DCE.i2409'])
        first_symbol, first_kline = rows[0]
        second_symbol, second_kline = rows[1]
        self.assertEqual(first_symbol, 'SHFE.rb2405')
        self.assertEqual(first_kline.close, 106.5)
        self.assertEqual(second_symbol, 'DCE.i2409')
        self.assertEqual(second_kline.close, 206.5)
        snapshot = provider.get_latest_snapshot(['SHFE.rb2405', 'DCE.i2409'])
        self.assertEqual(snapshot['SHFE.rb2405'], first_kline)
        self.assertEqual(snapshot['DCE.i2409'], second_kline)
        self.assertEqual(
            FakeApi.instances[0].serial_requests,
            [('SHFE.rb2405', 60, 4), ('DCE.i2409', 60, 4)],
        )
        self.assertEqual(FakeApi.instances[0].wait_update_calls, 0)
        self.assertTrue(FakeApi.instances[0].closed)


if __name__ == "__main__":
    unittest.main()
