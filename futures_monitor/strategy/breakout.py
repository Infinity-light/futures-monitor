"""
---
role: 突破策略
depends:
  - futures_monitor.strategy.state_machine
exports:
  - Kline
  - BreakoutResult
  - BreakoutStrategy
status: IMPLEMENTED
functions:
  - BreakoutStrategy.evaluate(new_kline: Kline, day_high: float, day_low: float, take_profit_pct: float, stop_loss_pct: float) -> BreakoutResult
---
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Kline:
    open: float
    high: float
    low: float
    close: float
    timestamp: float | int | str


@dataclass(slots=True)
class BreakoutResult:
    triggered: bool
    breakout_price: float | None
    take_profit_price: float | None
    stop_loss_price: float | None
    reason: str


class BreakoutStrategy:
    def __init__(self, max_cache_size: int = 200) -> None:
        self._max_cache_size = max(10, max_cache_size)
        self._klines: list[Kline] = []

    @property
    def klines(self) -> list[Kline]:
        return list(self._klines)

    def _append_kline(self, kline: Kline) -> None:
        self._klines.append(kline)
        if len(self._klines) > self._max_cache_size:
            self._klines = self._klines[-self._max_cache_size :]

    def evaluate(
        self,
        new_kline: Kline,
        day_high: float,
        day_low: float,
        take_profit_pct: float,
        stop_loss_pct: float,
    ) -> BreakoutResult:
        if not 0 <= take_profit_pct <= 1:
            raise ValueError("take_profit_pct must be in range [0, 1]")
        if not 0 <= stop_loss_pct <= 1:
            raise ValueError("stop_loss_pct must be in range [0, 1]")
        if day_high < day_low:
            raise ValueError("day_high must be >= day_low")

        self._append_kline(new_kline)

        if len(self._klines) < 4:
            return BreakoutResult(False, None, None, None, "not enough kline data")

        previous_three = self._klines[-4:-1]
        current = self._klines[-1]

        if not all(k.close > k.open for k in previous_three):
            return BreakoutResult(False, None, None, None, "previous three klines are not all bullish")

        if not (
            previous_three[0].low <= previous_three[1].low <= previous_three[2].low
        ):
            return BreakoutResult(False, None, None, None, "lows are decreasing within bullish sequence")

        prev_low = previous_three[-1].low
        if not (current.low < prev_low):
            return BreakoutResult(False, None, None, None, "current low does not break previous low")

        price_range = day_high - day_low
        breakout_price = current.close
        take_profit_price = day_low + price_range * take_profit_pct
        stop_loss_price = prev_low + price_range * stop_loss_pct

        return BreakoutResult(
            triggered=True,
            breakout_price=breakout_price,
            take_profit_price=take_profit_price,
            stop_loss_price=stop_loss_price,
            reason="breakout triggered by low break after bullish non-decreasing-low sequence",
        )
