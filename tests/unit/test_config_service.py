import json
import tempfile
import unittest
from pathlib import Path

from futures_monitor.server.services.config_service import ConfigService
from futures_monitor.server.schemas import ConfigDTO


class StubMonitorService:
    def __init__(self) -> None:
        self.reloaded = []

    def reload_config(self, config) -> None:
        self.reloaded.append(config)


class TestConfigService(unittest.TestCase):
    def test_update_config_persists_and_refreshes_monitor_service(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / 'config.json'
            service = ConfigService(str(config_path))
            monitor_service = StubMonitorService()
            service.set_monitor_service(monitor_service)

            payload = ConfigDTO(
                symbols=['SHFE.rb2505', 'DCE.i2505'],
                take_profit_pct=0.25,
                stop_loss_pct=0.15,
                tq_account='next-account',
                tq_password='next-password',
                use_real_market_data=True,
                strict_real_mode=True,
            )

            result = service.update_config(payload)
            saved = json.loads(config_path.read_text(encoding='utf-8'))

        self.assertEqual(result.symbols, ['SHFE.rb2505', 'DCE.i2505'])
        self.assertEqual(saved['tq_account'], 'next-account')
        self.assertEqual(saved['tq_password'], 'next-password')
        self.assertTrue(saved['use_real_market_data'])
        self.assertEqual(len(monitor_service.reloaded), 1)
        self.assertEqual(monitor_service.reloaded[0].tq_account, 'next-account')


if __name__ == '__main__':
    unittest.main()
