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

    def test_save_and_reload_custom_selection(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "cfg.json"
            cfg = AppConfig(
                symbols=["SHFE.rb", "DCE.i"],
                selection_mode="custom",
                selection_symbols=["SHFE.rb", "DCE.i"],
                take_profit_pct=0.2,
                stop_loss_pct=0.3,
            )
            save_config(cfg, str(p))
            loaded = load_config(str(p))
            saved = json.loads(p.read_text(encoding="utf-8"))

        self.assertEqual(loaded.symbols, ["SHFE.rb", "DCE.i"])
        self.assertEqual(loaded.selection_mode, "custom")
        self.assertEqual(loaded.selection_symbols, ["SHFE.rb", "DCE.i"])
        self.assertEqual(saved["selection_symbols"], ["SHFE.rb", "DCE.i"])
        self.assertEqual(loaded.take_profit_pct, 0.2)
        self.assertEqual(loaded.stop_loss_pct, 0.3)

    def test_legacy_all_text_is_migrated_without_pseudo_symbol(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "cfg.json"
            p.write_text(
                json.dumps(
                    {
                        "symbols": ["ALL 全部品种（自动读取当前有效合约）"],
                        "take_profit_pct": 0.5,
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            loaded = load_config(str(p))

        self.assertEqual(loaded.selection_mode, "all")
        self.assertEqual(loaded.selection_symbols, [])
        self.assertEqual(loaded.symbols, ["ALL"])

    def test_exchange_mode_roundtrip_uses_program_values(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "cfg.json"
            cfg = AppConfig(selection_mode="exchange", selection_exchanges=["SHFE", "DCE"])
            save_config(cfg, str(p))
            loaded = load_config(str(p))
            saved = json.loads(p.read_text(encoding="utf-8"))

        self.assertEqual(loaded.selection_mode, "exchange")
        self.assertEqual(loaded.selection_exchanges, ["SHFE", "DCE"])
        self.assertEqual(loaded.symbols, ["ALL"])
        self.assertEqual(saved["symbols"], ["ALL"])
        self.assertEqual(saved["selection_exchanges"], ["SHFE", "DCE"])

    def test_symbol_candidate_definitions_exposed_for_shared_metadata(self) -> None:
        from futures_monitor.config import SYMBOL_CANDIDATE_DEFINITIONS

        self.assertTrue(any(item["value"] == "SHFE.rb" and item["name"] == "螺纹钢" for item in SYMBOL_CANDIDATE_DEFINITIONS))

    def test_invalid_pct_raises(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "cfg.json"
            p.write_text(json.dumps({"take_profit_pct": 1.2}), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_config(str(p))


if __name__ == "__main__":
    unittest.main()
