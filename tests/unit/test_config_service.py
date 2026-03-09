import json
import tempfile
import unittest
from pathlib import Path

from futures_monitor.server.schemas import ConfigDTO
from futures_monitor.server.services.config_service import ConfigService


class StubMonitorService:
    def __init__(self) -> None:
        self.reloaded = []

    def reload_config(self, config) -> None:
        self.reloaded.append(config)


class TestConfigService(unittest.TestCase):
    def test_update_config_persists_and_refreshes_monitor_service(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / 'runtime' / 'config.json'
            repository_template_path = Path(temp_dir) / 'repository-config.json'
            repository_template_path.write_text(
                json.dumps(
                    {
                        'symbols': ['SHFE.rb'],
                        'selection_mode': 'custom',
                        'selection_symbols': ['SHFE.rb'],
                        'tq_account': 'template-account',
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding='utf-8',
            )
            service = ConfigService(str(config_path))
            monitor_service = StubMonitorService()
            service.set_monitor_service(monitor_service)

            payload = ConfigDTO(
                symbols=['SHFE.rb', 'DCE.i'],
                selection_mode='custom',
                selection_symbols=['SHFE.rb', 'DCE.i'],
                take_profit_pct=0.25,
                stop_loss_pct=0.15,
                tq_account='next-account',
                tq_password='next-password',
                use_real_market_data=True,
                strict_real_mode=True,
            )

            result = service.update_config(payload)
            saved = json.loads(config_path.read_text(encoding='utf-8'))
            template_saved = json.loads(repository_template_path.read_text(encoding='utf-8'))

        self.assertEqual(result.symbols, ['SHFE.rb', 'DCE.i'])
        self.assertEqual(result.selection_mode, 'custom')
        self.assertEqual(result.selection_symbols, ['SHFE.rb', 'DCE.i'])
        self.assertGreater(len(result.symbol_candidates), 0)
        self.assertEqual(saved['tq_account'], 'next-account')
        self.assertEqual(saved['tq_password'], 'next-password')
        self.assertTrue(saved['use_real_market_data'])
        self.assertEqual(template_saved['tq_account'], 'template-account')
        self.assertEqual(len(monitor_service.reloaded), 1)
        self.assertEqual(monitor_service.reloaded[0].tq_account, 'next-account')

    def test_get_config_returns_symbol_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / 'config.json'
            service = ConfigService(str(config_path))

            result = service.get_config()

        self.assertGreater(len(result.symbol_candidates), 0)
        self.assertEqual(result.symbol_candidates[0].value, 'SHFE.rb')
        self.assertEqual(result.symbol_candidates[0].name, '螺纹钢')
        self.assertEqual(result.symbol_candidates[0].category.endswith('所') or result.symbol_candidates[0].category == '上期能源', True)


if __name__ == '__main__':
    unittest.main()
