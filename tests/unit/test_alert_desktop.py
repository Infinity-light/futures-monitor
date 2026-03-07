import unittest

from futures_monitor.alert.desktop import DesktopAlertSender


class TestDesktopAlert(unittest.TestCase):
    def test_sender_constructable(self) -> None:
        sender = DesktopAlertSender(alert_sound=False)
        self.assertTrue(hasattr(sender, "send"))
        self.assertTrue(callable(sender.send))


if __name__ == "__main__":
    unittest.main()
