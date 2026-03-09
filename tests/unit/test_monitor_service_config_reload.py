import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from futures_monitor.config import AppConfig, save_config
from futures_monitor.server.services.monitor_service import MonitorService


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
        self.assertEqual(service.symbols, ['DCE.i', 'DCE.m'])
        self.assertIsNot(service.provider, original_provider)
        self.assertEqual(service.provider._config.tq_account, 'new-account')
        self.assertEqual(service.provider.get_symbol_metadata('DCE.i2409')['name'], '铁矿石')

    def test_stop_waits_for_thread_exit_before_restart(self) -> None:
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

                    release_stop.set()
                    stop_thread.join(timeout=1)
                    self.assertFalse(stop_thread.is_alive())

                    second = service.start(['SHFE.rb'], selection_mode='custom')
                    self.assertTrue(second['success'])
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
                    service.stop()

        mocked_resolve.assert_called_once_with([], selection_mode='all', selection_exchanges=[])
        self.assertTrue(result['success'])
        self.assertEqual(result['symbols'], ['SHFE.rb', 'DCE.i'])
        self.assertEqual(service.symbols, ['SHFE.rb', 'DCE.i'])
        self.assertIn('SHFE.rb', service.runtime_map)
        self.assertIn('DCE.i', service.runtime_map)

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
                        service._thread.join(timeout=1)

        mocked_resolve.assert_not_called()
        self.assertTrue(result['success'])
        self.assertEqual(result['symbols'], ['SHFE.rb', 'DCE.i'])
        self.assertEqual(service.symbols, ['SHFE.rb', 'DCE.i'])


if __name__ == '__main__':
    unittest.main()
