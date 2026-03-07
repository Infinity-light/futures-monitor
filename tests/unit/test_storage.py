import tempfile
import unittest
from pathlib import Path

from futures_monitor.data.storage import Storage


class TestStorage(unittest.TestCase):
    def test_save_alert_and_state(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "test.db"
            storage = Storage(str(db))

            alert_id = storage.save_alert(symbol="MOCK", message="hello", level="INFO")
            self.assertGreater(alert_id, 0)

            storage.save_symbol_state(symbol="MOCK", state="MONITORING", bought_at=None, extra="{}")
            data = storage.load_symbol_state("MOCK")

        self.assertIsNotNone(data)
        assert data is not None
        self.assertEqual(data["symbol"], "MOCK")
        self.assertEqual(data["state"], "MONITORING")


if __name__ == "__main__":
    unittest.main()
