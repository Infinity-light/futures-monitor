import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from futures_monitor.config import AppConfig, get_fixed_monitor_pool, save_config
from futures_monitor.server.services.monitor_service import MonitorService
from futures_monitor.strategy.breakout import Kline


class TestMonitorServiceConfigReload(unittest.TestCase):
    def test_reload_config_rebuilds_provider_and_uses_new_config_on_start(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / 'config.json'
            save_config(
                AppConfig(
                    symbols=['SHFE.rb'],
                    selection_mode='custom',
                    selection_symbols=['SHFE.rb'],
                    tq_account='old-account',
                    tq_password='old-password',
                    use_real_market_data=False,
                    strict_real_mode=True,
                    data_dir=str(Path(temp_dir) / 'data-old'),
                ),
                str(config_path),
            )
            service = MonitorService(str(config_path))
            original_provider = service.provider

            save_config(
                AppConfig(
                    symbols=['ALL'],
                    selection_mode='exchange',
                    selection_exchanges=['DCE'],
                    tq_account='new-account',
                    tq_password='new-password',
                    use_real_market_data=True,
                    strict_real_mode=False,
                    data_dir=str(Path(temp_dir) / 'data-new'),
                ),
                str(config_path),
            )

            with patch.object(service, '_monitor_loop', return_value=None):
                result = service.start([], selection_mode='exchange', selection_exchanges=['DCE'])
                service._thread.join(timeout=1)

        self.assertTrue(result['success'])
        self.assertEqual(service.config.tq_account, 'new-account')
        self.assertEqual(service.config.tq_password, 'new-password')
        self.assertTrue(service.config.use_real_market_data)
        self.assertFalse(service.config.strict_real_mode)
        self.assertEqual(service.selection_mode, 'exchange')
        self.assertEqual(service.selection_exchanges, ['DCE'])
        self.assertEqual(service.symbols, get_fixed_monitor_pool('exchange', ['DCE']))
        self.assertIsNot(service.provider, original_provider)
        self.assertEqual(service.provider._config.tq_account, 'new-account')
        self.assertEqual(service.provider.get_symbol_metadata('DCE.i2409')['name'], '铁矿石')

    def test_stop_does_not_report_fully_stopped_before_thread_exit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / 'config.json'
            save_config(
                AppConfig(
                    selection_mode='custom',
                    selection_symbols=['SHFE.rb'],
                    use_real_market_data=False,
                    data_dir=str(Path(temp_dir) / 'data'),
                ),
                str(config_path),
            )
            service = MonitorService(str(config_path))
            release_stop = threading.Event()

            def blocking_stream(symbols, max_updates=None, stop_flag=None, selection_mode='custom', selection_exchanges=None):
                self.assertEqual(symbols, ['SHFE.rb'])
                while stop_flag and not stop_flag():
                    time.sleep(0.01)
                while stop_flag and stop_flag() and not release_stop.is_set():
                    time.sleep(0.01)
                if False:
                    yield None

            with patch.object(service, 'reload_config', return_value=service.config):
                with patch.object(service.provider, 'stream_1m_klines', side_effect=blocking_stream):
                    first = service.start(['SHFE.rb'], selection_mode='custom')
                    self.assertTrue(first['success'])
                    self.assertIsNotNone(service._thread)
                    self.assertTrue(service._thread.is_alive())

                    stop_thread = threading.Thread(target=service.stop)
                    stop_thread.start()
                    time.sleep(0.05)
                    self.assertTrue(stop_thread.is_alive())
                    self.assertTrue(service._thread.is_alive())
                    self.assertTrue(service.get_status().running)
                    self.assertEqual(service.get_status().message, '监控正在停止中')

                    release_stop.set()
                    stop_thread.join(timeout=1)
                    self.assertFalse(stop_thread.is_alive())
                    self.assertFalse(service.get_status().running)
                    self.assertEqual(service.get_status().message, '监控未运行')

    def test_start_returns_stopping_message_until_previous_thread_exits(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / 'config.json'
            save_config(
                AppConfig(
                    selection_mode='custom',
                    selection_symbols=['SHFE.rb'],
                    use_real_market_data=False,
                    data_dir=str(Path(temp_dir) / 'data'),
                ),
                str(config_path),
            )
            service = MonitorService(str(config_path))
            release_stop = threading.Event()

            def blocking_stream(symbols, max_updates=None, stop_flag=None, selection_mode='custom', selection_exchanges=None):
                while stop_flag and not stop_flag():
                    time.sleep(0.01)
                while stop_flag and stop_flag() and not release_stop.is_set():
                    time.sleep(0.01)
                if False:
                    yield None

            with patch.object(service, 'reload_config', return_value=service.config):
                with patch.object(service.provider, 'stream_1m_klines', side_effect=blocking_stream):
                    first = service.start(['SHFE.rb'], selection_mode='custom')
                    self.assertTrue(first['success'])

                    stop_thread = threading.Thread(target=service.stop)
                    stop_thread.start()
                    time.sleep(0.05)

                    retry_while_stopping = service.start(['SHFE.rb'], selection_mode='custom')
                    self.assertFalse(retry_while_stopping['success'])
                    self.assertEqual(retry_while_stopping['message'], '监控正在停止中，请稍候再试。')

                    release_stop.set()
                    stop_thread.join(timeout=1)
                    self.assertFalse(stop_thread.is_alive())

                    retry_after_exit = service.start(['SHFE.rb'], selection_mode='custom')
                    self.assertTrue(retry_after_exit['success'])
                    service.stop()

    def test_start_prepares_symbols_for_all_mode_before_stream_ticks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / 'config.json'
            save_config(
                AppConfig(
                    selection_mode='all',
                    use_real_market_data=False,
                    data_dir=str(Path(temp_dir) / 'data'),
                ),
                str(config_path),
            )
            service = MonitorService(str(config_path))

            with patch.object(service, 'reload_config', return_value=service.config):
                with patch.object(service.provider, 'resolve_symbols', return_value=['SHFE.rb', 'DCE.i']) as mocked_resolve:
                    result = service.start([], selection_mode='all')
                    active_symbols = list(service.symbols)
                    runtime_symbols = list(service.runtime_map)
                    service.stop()

        mocked_resolve.assert_called_once_with(get_fixed_monitor_pool('all'), selection_mode='all', selection_exchanges=[])
        self.assertTrue(result['success'])
        self.assertEqual(result['symbols'], ['SHFE.rb', 'DCE.i'])
        self.assertEqual(active_symbols, ['SHFE.rb', 'DCE.i'])
        self.assertIn('SHFE.rb', runtime_symbols)
        self.assertIn('DCE.i', runtime_symbols)

    def test_probe_logic_updates_count_progress_and_state_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / 'config.json'
            save_config(
                AppConfig(
                    selection_mode='custom',
                    selection_symbols=['SHFE.rb'],
                    use_real_market_data=False,
                    probe_target_count=3,
                    probe_distance_ratio=0.2,
                    data_dir=str(Path(temp_dir) / 'data'),
                ),
                str(config_path),
            )
            service = MonitorService(str(config_path))
            service._prepare_symbol_context(['SHFE.rb'])

            service._process_tick('SHFE.rb', Kline(open=100, high=110, low=100, close=108, timestamp='2026-03-09T09:00:00'))
            service._process_tick('SHFE.rb', Kline(open=108, high=112, low=102, close=110, timestamp='2026-03-09T09:01:00'))
            service._process_tick('SHFE.rb', Kline(open=110, high=114, low=104, close=112, timestamp='2026-03-09T09:02:00'))
            service._process_tick('SHFE.rb', Kline(open=112, high=116, low=104.5, close=113, timestamp='2026-03-09T09:03:00'))
            first_probe = service.get_status().rows[0]

            service._process_tick('SHFE.rb', Kline(open=113, high=117, low=104.6, close=112, timestamp='2026-03-09T09:04:00'))
            second_probe = service.get_status().rows[0]

            service._process_tick('SHFE.rb', Kline(open=112, high=113, low=110, close=111, timestamp='2026-03-09T09:05:00'))
            cooled_off = service.get_status().rows[0]

        self.assertEqual(first_probe.probe_count, 1)
        self.assertGreater(first_probe.probe_progress, 0)
        self.assertEqual(first_probe.probe_state_text, '第1次试探')
        self.assertEqual(second_probe.probe_count, 2)
        self.assertEqual(second_probe.probe_state_text, '第2次试探')
        self.assertEqual(cooled_off.probe_state_text, '监控中')

    def test_custom_mode_keeps_requested_symbols_without_provider_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / 'config.json'
            save_config(
                AppConfig(
                    selection_mode='custom',
                    selection_symbols=['SHFE.rb', 'DCE.i'],
                    use_real_market_data=False,
                    data_dir=str(Path(temp_dir) / 'data'),
                ),
                str(config_path),
            )
            service = MonitorService(str(config_path))

            with patch.object(service, 'reload_config', return_value=service.config):
                with patch.object(service.provider, 'resolve_symbols') as mocked_resolve:
                    with patch.object(service, '_monitor_loop', return_value=None):
                        result = service.start(['SHFE.rb', 'DCE.i'], selection_mode='custom')
                        active_symbols = list(service.symbols)
                        service._thread.join(timeout=1)

        mocked_resolve.assert_not_called()
        self.assertTrue(result['success'])
        self.assertEqual(result['symbols'], ['SHFE.rb', 'DCE.i'])
        self.assertEqual(active_symbols, ['SHFE.rb', 'DCE.i'])

    def test_start_waits_for_first_usable_snapshot_before_returning(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / 'config.json'
            save_config(
                AppConfig(
                    selection_mode='custom',
                    selection_symbols=['SHFE.rb'],
                    use_real_market_data=False,
                    data_dir=str(Path(temp_dir) / 'data'),
                ),
                str(config_path),
            )
            service = MonitorService(str(config_path))
            service._start_wait_timeout = 0.4
            service._start_wait_interval = 0.01
            release_stream = threading.Event()
            first_ready = threading.Event()

            def delayed_stream(symbols, max_updates=None, stop_flag=None, selection_mode='custom', selection_exchanges=None):
                time.sleep(0.06)
                kline = Kline(open=100, high=105, low=99, close=103, timestamp='2026-03-09T09:01:00')
                first_ready.set()
                yield 'SHFE.rb', kline
                while not (stop_flag and stop_flag()):
                    if release_stream.wait(0.01):
                        break

            with patch.object(service, 'reload_config', return_value=service.config):
                with patch.object(service.provider, 'stream_1m_klines', side_effect=delayed_stream):
                    started_at = time.monotonic()
                    result = service.start(['SHFE.rb'], selection_mode='custom')
                    elapsed = time.monotonic() - started_at
                    status = service.get_status()
                    release_stream.set()
                    service.stop()

        self.assertTrue(result['success'])
        self.assertTrue(first_ready.is_set())
        self.assertGreaterEqual(elapsed, 0.05)
        self.assertLess(elapsed, service._start_wait_timeout + 0.2)
        self.assertEqual(len(status.rows), 1)
        self.assertEqual(status.rows[0].last_price, 103)
        self.assertEqual(status.rows[0].day_high, 105)
        self.assertEqual(status.rows[0].day_low, 99)
        self.assertEqual(status.rows[0].last_event, '监控中')

    def test_start_returns_after_timeout_when_first_snapshot_is_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / 'config.json'
            save_config(
                AppConfig(
                    selection_mode='custom',
                    selection_symbols=['SHFE.rb'],
                    use_real_market_data=False,
                    data_dir=str(Path(temp_dir) / 'data'),
                ),
                str(config_path),
            )
            service = MonitorService(str(config_path))
            service._start_wait_timeout = 0.08
            service._start_wait_interval = 0.01
            release_stream = threading.Event()

            def blocking_stream(symbols, max_updates=None, stop_flag=None, selection_mode='custom', selection_exchanges=None):
                while not (stop_flag and stop_flag()) and not release_stream.wait(0.01):
                    pass
                if False:
                    yield None

            with patch.object(service, 'reload_config', return_value=service.config):
                with patch.object(service.provider, 'stream_1m_klines', side_effect=blocking_stream):
                    started_at = time.monotonic()
                    result = service.start(['SHFE.rb'], selection_mode='custom')
                    elapsed = time.monotonic() - started_at
                    release_stream.set()
                    service.stop()

        self.assertTrue(result['success'])
        self.assertGreaterEqual(elapsed, service._start_wait_timeout)
        self.assertLess(elapsed, service._start_wait_timeout + 0.15)

    def test_stop_clears_rows_and_symbols_after_thread_exit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / 'config.json'
            save_config(
                AppConfig(
                    selection_mode='custom',
                    selection_symbols=['SHFE.rb'],
                    use_real_market_data=False,
                    data_dir=str(Path(temp_dir) / 'data'),
                ),
                str(config_path),
            )
            service = MonitorService(str(config_path))
            release_stream = threading.Event()

            def single_tick_stream(symbols, max_updates=None, stop_flag=None, selection_mode='custom', selection_exchanges=None):
                yield 'SHFE.rb', Kline(open=100, high=104, low=98, close=101, timestamp='2026-03-09T09:00:00')
                while not (stop_flag and stop_flag()) and not release_stream.wait(0.01):
                    pass

            with patch.object(service, 'reload_config', return_value=service.config):
                with patch.object(service.provider, 'stream_1m_klines', side_effect=single_tick_stream):
                    service.start(['SHFE.rb'], selection_mode='custom')
                    before_stop = service.get_status()
                    result = service.stop()
                    after_stop = service.get_status()
                    release_stream.set()

        self.assertEqual(len(before_stop.rows), 1)
        self.assertEqual(before_stop.rows[0].last_price, 101)
        self.assertTrue(result['success'])
        self.assertFalse(after_stop.running)
        self.assertEqual(after_stop.message, '监控未运行')
        self.assertEqual(after_stop.symbols, [])
        self.assertEqual(after_stop.rows, [])


if __name__ == '__main__':
    unittest.main()
