import json
import tempfile
import unittest
from pathlib import Path

from futures_monitor.config import AppConfig, load_config, save_config


class TestConfig(unittest.TestCase):
    def test_load_default_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            cfg = load_config(str(Path(td) / "missing.json"))

        self.assertIsInstance(cfg, AppConfig)
        self.assertEqual(cfg.take_profit_pct, 0.5)
        self.assertEqual(cfg.stop_loss_pct, 0.5)
        self.assertEqual(cfg.position_pct, 0.1)
        self.assertFalse(cfg.enable_sms)
        self.assertTrue(cfg.alert_sound)
        self.assertEqual(cfg.data_dir, ".data")
        self.assertEqual(cfg.timezone, "Asia/Shanghai")
        self.assertTrue(cfg.strict_real_mode)
        self.assertEqual(cfg.ui_refresh_ms, 800)

    def test_save_and_reload(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "cfg.json"
            cfg = AppConfig(symbols=["SHFE.rb2405"], take_profit_pct=0.2, stop_loss_pct=0.3)
            save_config(cfg, str(p))
            loaded = load_config(str(p))

        self.assertEqual(loaded.symbols, ["SHFE.rb2405"])
        self.assertEqual(loaded.take_profit_pct, 0.2)
        self.assertEqual(loaded.stop_loss_pct, 0.3)

    def test_invalid_pct_raises(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "cfg.json"
            p.write_text(json.dumps({"take_profit_pct": 1.2}), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_config(str(p))


if __name__ == "__main__":
    unittest.main()
