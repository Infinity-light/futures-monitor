import json
import tempfile
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
                    symbols=['SHFE.rb2405'],
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
                    symbols=['DCE.i2405'],
                    tq_account='new-account',
                    tq_password='new-password',
                    use_real_market_data=True,
                    strict_real_mode=False,
                    data_dir=str(Path(temp_dir) / 'data-new'),
                ),
                str(config_path),
            )

            with patch.object(service, '_monitor_loop', return_value=None):
                result = service.start([])
                service._thread.join(timeout=1)

        self.assertTrue(result['success'])
        self.assertEqual(service.config.tq_account, 'new-account')
        self.assertEqual(service.config.tq_password, 'new-password')
        self.assertTrue(service.config.use_real_market_data)
        self.assertFalse(service.config.strict_real_mode)
        self.assertEqual(service.symbols, ['DCE.i2405'])
        self.assertIsNot(service.provider, original_provider)
        self.assertEqual(service.provider._config.tq_account, 'new-account')


if __name__ == '__main__':
    unittest.main()
