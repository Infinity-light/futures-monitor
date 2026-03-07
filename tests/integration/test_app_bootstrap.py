import unittest
from unittest.mock import patch

from futures_monitor.main import main


class TestAppBootstrap(unittest.TestCase):
    def test_main_runs_with_mocked_alert(self) -> None:
        with patch("futures_monitor.main.DesktopAlertSender.send", return_value="ignored"):
            main()


if __name__ == "__main__":
    unittest.main()
