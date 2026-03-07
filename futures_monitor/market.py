"""
---
role: 行情数据提供器
depends:
  - futures_monitor.config
  - futures_monitor.strategy.breakout
exports:
  - MarketDataProvider
status: IMPLEMENTED
functions:
  - MarketDataProvider.__init__(config: object, logger: object) -> None
  - MarketDataProvider.stream_1m_klines(symbols: list[str], max_updates: int | None = None, stop_flag: callable | None = None)
  - MarketDataProvider.get_latest_snapshot(symbols: list[str]) -> dict[str, Kline]
---
"""

from __future__ import annotations

from typing import Callable, Iterator


_ALL_SYMBOL_ALIASES = {"ALL", "全部"}

from futures_monitor.strategy.breakout import Kline


class MarketDataProvider:
    def __init__(self, config, logger) -> None:
        self._config = config
        self._logger = logger
        self._latest_snapshot: dict[str, Kline] = {}

    def _build_mock_klines_for_symbol(self, symbol: str, offset: float = 0.0) -> list[Kline]:
        _ = symbol
        return [
            Kline(open=100 + offset, high=103 + offset, low=99 + offset, close=102 + offset, timestamp="2026-03-07T09:00:00"),
            Kline(open=102 + offset, high=104 + offset, low=100 + offset, close=103 + offset, timestamp="2026-03-07T09:01:00"),
            Kline(open=103 + offset, high=105 + offset, low=101 + offset, close=104 + offset, timestamp="2026-03-07T09:02:00"),
            Kline(open=104 + offset, high=106 + offset, low=100.5 + offset, close=103.8 + offset, timestamp="2026-03-07T09:03:00"),
            Kline(open=103.8 + offset, high=109 + offset, low=103 + offset, close=108.8 + offset, timestamp="2026-03-07T14:56:00"),
        ]

    def _publish(self, symbol: str, kline: Kline) -> tuple[str, Kline]:
        self._latest_snapshot[symbol] = kline
        return symbol, kline

    def _is_all_symbols_request(self, symbols: list[str]) -> bool:
        for symbol in symbols:
            token = str(symbol).strip()
            if token.upper() in _ALL_SYMBOL_ALIASES or token in _ALL_SYMBOL_ALIASES:
                return True
        return False

    def _normalize_symbols(self, symbols: list[str]) -> list[str]:
        normalized: list[str] = []
        for symbol in symbols:
            token = str(symbol).strip()
            if token:
                normalized.append(token)
        return normalized

    def _dedupe_symbols(self, symbols: list[str]) -> list[str]:
        deduped: list[str] = []
        seen: set[str] = set()
        for symbol in symbols:
            if symbol in seen:
                continue
            seen.add(symbol)
            deduped.append(symbol)
        return deduped

    def _resolve_all_real_symbols(self, api) -> list[str]:
        resolved: list[str] = []

        cont_symbols = list(api.query_cont_quotes())
        for cont_symbol in cont_symbols:
            quote = api.get_quote(cont_symbol)
            underlying_symbol = getattr(quote, "underlying_symbol", "")
            if underlying_symbol:
                resolved.append(str(underlying_symbol))

        resolved = self._dedupe_symbols(self._normalize_symbols(resolved))
        if resolved:
            return resolved

        futures = list(api.query_quotes(ins_class="FUTURE", expired=False))
        return self._dedupe_symbols(self._normalize_symbols(futures))

    def _resolve_real_symbols(self, symbols: list[str], api) -> list[str]:
        normalized = self._normalize_symbols(symbols)
        if self._is_all_symbols_request(normalized):
            resolved = self._resolve_all_real_symbols(api)
            if not resolved:
                raise RuntimeError("ALL/全部 请求未查询到任何有效期货合约")
            self._logger.info("ALL/全部 请求已解析为 %d 个有效合约", len(resolved))
            return resolved
        return normalized

    def _stream_mock(
        self,
        symbols: list[str],
        max_updates: int | None = None,
        stop_flag: Callable[[], bool] | None = None,
    ) -> Iterator[tuple[str, Kline]]:
        emitted = 0
        safe_symbols = symbols or ["SHFE.rb2410"]

        for idx, symbol in enumerate(safe_symbols):
            if stop_flag and stop_flag():
                return
            klines = self._build_mock_klines_for_symbol(symbol, offset=float(idx) * 10.0)
            for kline in klines:
                if stop_flag and stop_flag():
                    return
                yield self._publish(symbol, kline)
                emitted += 1
                if max_updates is not None and emitted >= max_updates:
                    return

    def _stream_real(
        self,
        symbols: list[str],
        max_updates: int | None = None,
        stop_flag: Callable[[], bool] | None = None,
    ) -> Iterator[tuple[str, Kline]]:
        if not self._config.tq_account or not self._config.tq_password:
            raise ValueError("tq_account/tq_password is required when use_real_market_data=True")

        from tqsdk import TqApi, TqAuth

        api = TqApi(auth=TqAuth(self._config.tq_account, self._config.tq_password))
        safe_symbols = self._resolve_real_symbols(symbols, api)
        if not safe_symbols:
            raise RuntimeError("未提供可订阅的有效合约")
        serials = {symbol: api.get_kline_serial(symbol, 60, data_length=4) for symbol in safe_symbols}

        emitted = 0
        try:
            while True:
                if stop_flag and stop_flag():
                    return
                api.wait_update()
                for symbol, series in serials.items():
                    if stop_flag and stop_flag():
                        return
                    last = series.iloc[-1]
                    kline = Kline(
                        open=float(last["open"]),
                        high=float(last["high"]),
                        low=float(last["low"]),
                        close=float(last["close"]),
                        timestamp=int(last["datetime"]),
                    )
                    yield self._publish(symbol, kline)
                    emitted += 1
                    if max_updates is not None and emitted >= max_updates:
                        return
        finally:
            api.close()

    def stream_1m_klines(
        self,
        symbols: list[str],
        max_updates: int | None = None,
        stop_flag: Callable[[], bool] | None = None,
    ):
        use_real = bool(getattr(self._config, "use_real_market_data", False))
        strict_real_mode = bool(getattr(self._config, "strict_real_mode", True))

        if not use_real:
            yield from self._stream_mock(symbols, max_updates=max_updates, stop_flag=stop_flag)
            return

        try:
            yield from self._stream_real(symbols, max_updates=max_updates, stop_flag=stop_flag)
        except Exception as exc:
            if strict_real_mode:
                raise
            self._logger.warning("Real market data unavailable, fallback to mock stream: %s", exc)
            yield from self._stream_mock(symbols, max_updates=max_updates, stop_flag=stop_flag)

    def get_latest_snapshot(self, symbols: list[str]) -> dict[str, Kline]:
        safe_symbols = symbols or list(self._latest_snapshot.keys())
        return {symbol: self._latest_snapshot[symbol] for symbol in safe_symbols if symbol in self._latest_snapshot}
