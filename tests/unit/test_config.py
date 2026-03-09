import json
import os
import tempfile
import unittest
from pathlib import Path

from futures_monitor.config import (
    AppConfig,
    ensure_runtime_config,
    load_config,
    resolve_runtime_config_path,
    save_config,
)


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

    def test_runtime_config_initializes_from_template_once(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_path = Path(temp_dir) / "runtime" / "config.json"
            template_path = Path(temp_dir) / "template.json"
            template_path.write_text(
                json.dumps(
                    {
                        "symbols": ["SHFE.rb"],
                        "selection_mode": "custom",
                        "selection_symbols": ["SHFE.rb"],
                        "take_profit_pct": 0.37,
                        "stop_loss_pct": 0.21,
                        "tq_account": "template-account",
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            created_path = ensure_runtime_config(runtime_path, template_path)
            created_payload = json.loads(created_path.read_text(encoding="utf-8"))

            template_path.write_text(
                json.dumps(
                    {
                        "symbols": ["DCE.i"],
                        "selection_mode": "custom",
                        "selection_symbols": ["DCE.i"],
                        "take_profit_pct": 0.99,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            second_path = ensure_runtime_config(runtime_path, template_path)
            second_payload = json.loads(second_path.read_text(encoding="utf-8"))

        self.assertEqual(created_path, runtime_path)
        self.assertEqual(created_payload["tq_account"], "template-account")
        self.assertEqual(created_payload["take_profit_pct"], 0.37)
        self.assertEqual(second_payload["tq_account"], "template-account")
        self.assertEqual(second_payload["take_profit_pct"], 0.37)

    def test_load_config_without_explicit_path_uses_runtime_env_and_not_template_after_init(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_path = Path(temp_dir) / "persistent" / "config.json"
            template_path = Path(temp_dir) / "repo-config.json"
            template_path.write_text(
                json.dumps(
                    {
                        "symbols": ["SHFE.rb"],
                        "selection_mode": "custom",
                        "selection_symbols": ["SHFE.rb"],
                        "tq_account": "repo-template",
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            old_runtime_env = os.environ.get("FUTURES_MONITOR_RUNTIME_CONFIG")
            old_template_env = os.environ.get("FUTURES_MONITOR_CONFIG_TEMPLATE")
            os.environ["FUTURES_MONITOR_RUNTIME_CONFIG"] = str(runtime_path)
            os.environ["FUTURES_MONITOR_CONFIG_TEMPLATE"] = str(template_path)
            try:
                first = load_config()
                save_config(
                    AppConfig(
                        symbols=["DCE.i"],
                        selection_mode="custom",
                        selection_symbols=["DCE.i"],
                        tq_account="runtime-value",
                    )
                )
                template_path.write_text(
                    json.dumps(
                        {
                            "symbols": ["CZCE.MA"],
                            "selection_mode": "custom",
                            "selection_symbols": ["CZCE.MA"],
                            "tq_account": "changed-template",
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )
                second = load_config()
                runtime_payload = json.loads(runtime_path.read_text(encoding="utf-8"))
            finally:
                if old_runtime_env is None:
                    os.environ.pop("FUTURES_MONITOR_RUNTIME_CONFIG", None)
                else:
                    os.environ["FUTURES_MONITOR_RUNTIME_CONFIG"] = old_runtime_env
                if old_template_env is None:
                    os.environ.pop("FUTURES_MONITOR_CONFIG_TEMPLATE", None)
                else:
                    os.environ["FUTURES_MONITOR_CONFIG_TEMPLATE"] = old_template_env

        self.assertEqual(first.tq_account, "repo-template")
        self.assertEqual(second.tq_account, "runtime-value")
        self.assertEqual(runtime_payload["tq_account"], "runtime-value")
        self.assertEqual(runtime_payload["selection_symbols"], ["DCE.i"])

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

    def test_symbol_candidate_definitions_include_recent_common_cn_names(self) -> None:
        from futures_monitor.config import SYMBOL_CANDIDATE_DEFINITIONS

        expected_names = {
            'CZCE.UR': '尿素',
            'DCE.v': 'PVC',
            'CZCE.WH': '强麦',
            'CZCE.WR': '线材',
            'CZCE.ZC': '郑煤',
        }
        actual = {item['value']: item['name'] for item in SYMBOL_CANDIDATE_DEFINITIONS}
        self.assertEqual({key: actual.get(key) for key in expected_names}, expected_names)

    def test_symbol_candidate_definitions_cover_latest_cn_name_backfill_batch(self) -> None:
        from futures_monitor.config import SYMBOL_CANDIDATE_DEFINITIONS

        expected_names = {
            'SHFE.sp': '纸浆',
            'SHFE.ru': '橡胶',
            'SHFE.sn': '沪锡',
            'SHFE.bc': '国际铜',
            'SHFE.ad': '铸造铝合金',
            'SHFE.op': '胶版印刷纸',
            'DCE.l': '聚乙烯',
            'DCE.p': '棕榈油',
            'DCE.jd': '鸡蛋',
            'DCE.j': '焦炭',
            'DCE.jm': '焦煤',
            'DCE.lh': '生猪',
            'DCE.bz': '纯苯',
            'DCE.pg': '液化石油气',
            'CZCE.AP': '苹果',
            'CZCE.PF': '短纤',
            'CZCE.PX': '对二甲苯',
            'CZCE.OI': '菜油',
            'CZCE.PR': '瓶片',
            'CZCE.SH': '烧碱',
            'CZCE.CY': '棉纱',
            'CFFEX.TS': '2年期国债',
            'CFFEX.TF': '5年期国债',
            'CFFEX.TL': '30年期国债',
            'GFEX.ps': '多晶硅',
            'GFEX.pt': '铂',
            'GFEX.pd': '钯',
        }
        actual = {item['value']: item['name'] for item in SYMBOL_CANDIDATE_DEFINITIONS}
        self.assertEqual({key: actual.get(key) for key in expected_names}, expected_names)

    def test_invalid_pct_raises(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "cfg.json"
            p.write_text(json.dumps({"take_profit_pct": 1.2}), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_config(str(p))

    def test_resolve_runtime_config_path_uses_runtime_env(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_path = Path(temp_dir) / "x" / "config.json"
            old_runtime_env = os.environ.get("FUTURES_MONITOR_RUNTIME_CONFIG")
            os.environ["FUTURES_MONITOR_RUNTIME_CONFIG"] = str(runtime_path)
            try:
                resolved = resolve_runtime_config_path()
            finally:
                if old_runtime_env is None:
                    os.environ.pop("FUTURES_MONITOR_RUNTIME_CONFIG", None)
                else:
                    os.environ["FUTURES_MONITOR_RUNTIME_CONFIG"] = old_runtime_env

        self.assertEqual(resolved, runtime_path)


if __name__ == "__main__":
    unittest.main()
