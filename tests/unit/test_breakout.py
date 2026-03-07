import unittest

from futures_monitor.strategy.breakout import BreakoutStrategy, Kline


class TestBreakout(unittest.TestCase):
    def test_breakout_triggered(self) -> None:
        strategy = BreakoutStrategy()
        day_high, day_low = 110.0, 95.0

        klines = [
            Kline(100, 103, 99, 102, "t1"),
            Kline(102, 104, 100, 103, "t2"),
            Kline(103, 105, 101, 104, "t3"),
            Kline(104, 106, 100.5, 103.8, "t4"),
        ]

        result = None
        for k in klines:
            result = strategy.evaluate(k, day_high, day_low, 0.5, 0.5)

        self.assertIsNotNone(result)
        self.assertTrue(result.triggered)
        self.assertEqual(result.breakout_price, 103.8)
        self.assertAlmostEqual(result.take_profit_price, 102.5)
        self.assertAlmostEqual(result.stop_loss_price, 108.5)

    def test_not_enough_data(self) -> None:
        strategy = BreakoutStrategy()
        result = strategy.evaluate(Kline(100, 101, 99, 100.5, "t1"), 110, 90, 0.5, 0.5)
        self.assertFalse(result.triggered)


if __name__ == "__main__":
    unittest.main()
