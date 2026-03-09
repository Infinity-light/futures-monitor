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
  - MarketDataProvider.stream_1m_klines(symbols: list[str], max_updates: int | None = None, stop_flag: callable | None = None, selection_mode: str = "custom", selection_exchanges: list[str] | None = None)
  - MarketDataProvider.get_latest_snapshot(symbols: list[str]) -> dict[str, Kline]
---
"""

from __future__ import annotations

from typing import Callable, Iterator


_TQ_AUTH_GUIDANCE = (
    "请填写可用于 TqSdk/快期认证的快期账户（手机号、邮箱或用户名）及对应密码，"
    "不是期货实盘账号，也不是普通模拟交易编号。"
)

from futures_monitor.config import ALL_SYMBOL_ALIASES, ALL_SYMBOL_LABEL, SYMBOL_CANDIDATE_DEFINITIONS, is_all_selection_token
from futures_monitor.strategy.breakout import Kline


class MarketDataProvider:
    def __init__(self, config, logger) -> None:
        self._config = config
        self._logger = logger
        self._latest_snapshot: dict[str, Kline] = {}
        self._symbol_metadata = {
            str(item["value"]).upper(): {
                "name": str(item["name"]),
                "exchange": str(item["exchange"]),
                "display_symbol": str(item["code"]),
            }
            for item in SYMBOL_CANDIDATE_DEFINITIONS
        }

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
            token_upper = token.upper()
            if token == ALL_SYMBOL_LABEL:
                return True
            if token_upper in ALL_SYMBOL_ALIASES or token in ALL_SYMBOL_ALIASES:
                return True
            if is_all_selection_token(token):
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

    def _dedupe_instrument_ids(self, symbols: list[str]) -> list[str]:
        deduped: list[str] = []
        seen: set[str] = set()
        for symbol in symbols:
            token = str(symbol).strip()
            if not token:
                continue
            key = token.split(".", 1)[1] if "." in token else token
            key = key.upper()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(token)
        return deduped

    def get_symbol_metadata(self, symbol: str) -> dict[str, str]:
        token = str(symbol).strip()
        if not token:
            return {"display_symbol": "", "name": "", "exchange": ""}
        exchange = token.split(".", 1)[0] if "." in token else ""
        instrument = token.split(".", 1)[1] if "." in token else token
        product = instrument.rstrip("0123456789") or instrument
        direct = self._symbol_metadata.get(token.upper())
        product_key = f"{exchange}.{product}".upper() if exchange else product.upper()
        candidate = direct or self._symbol_metadata.get(product_key)
        if candidate:
            return {
                "display_symbol": candidate.get("display_symbol", token),
                "name": candidate.get("name", product.upper()),
                "exchange": candidate.get("exchange", exchange),
            }
        return {"display_symbol": token, "name": product.upper(), "exchange": exchange}

    def _build_custom_symbol_mapping(self, symbols: list[str]) -> dict[str, str]:
        mapping: dict[str, str] = {}
        for symbol in self._normalize_symbols(symbols):
            if is_all_selection_token(symbol):
                continue
            instrument = symbol.split(".", 1)[1] if "." in symbol else symbol
            product = instrument.rstrip("0123456789") or instrument
            exchange = symbol.split(".", 1)[0] if "." in symbol else ""
            mapping[symbol.upper()] = symbol
            mapping[product.upper()] = symbol
            if exchange:
                mapping[f"{exchange}.{product}".upper()] = symbol
        return mapping

    def _resolve_quote_symbol(self, api, requested_symbol: str) -> str:
        token = str(requested_symbol).strip()
        if not token:
            return token
        quote = api.get_quote(token)
        underlying_symbol = str(getattr(quote, "underlying_symbol", "") or "").strip()
        if underlying_symbol:
            return underlying_symbol
        if "." in token and not any(char.isdigit() for char in token.rsplit(".", 1)[1]):
            quote = api.get_quote(f"KQ.m@{token}")
            underlying_symbol = str(getattr(quote, "underlying_symbol", "") or "").strip()
            if underlying_symbol:
                return underlying_symbol
        return token

    def _resolve_mock_symbols(
        self,
        symbols: list[str],
        selection_mode: str = "custom",
        selection_exchanges: list[str] | None = None,
    ) -> list[str]:
        normalized = self._normalize_symbols(symbols)
        if selection_mode == "all" or self._is_all_symbols_request(normalized):
            return ["SHFE.rb", "DCE.i", "CZCE.TA"]
        if selection_mode == "exchange":
            exchange_map = {
                "SHFE": ["SHFE.rb", "SHFE.au"],
                "DCE": ["DCE.i", "DCE.m"],
                "CZCE": ["CZCE.TA", "CZCE.MA"],
                "CFFEX": ["CFFEX.IF", "CFFEX.T"],
                "INE": ["INE.sc", "INE.nr"],
                "GFEX": ["GFEX.si", "GFEX.lc"],
            }
            resolved: list[str] = []
            for exchange in selection_exchanges or []:
                resolved.extend(exchange_map.get(exchange, []))
            return self._dedupe_symbols(resolved)
        filtered = [symbol for symbol in normalized if not is_all_selection_token(symbol)]
        resolved = self._dedupe_instrument_ids(filtered)
        return resolved or ["SHFE.rb2410"]

    def _resolve_all_real_symbols(self, api, exchange_id: str | None = None) -> list[str]:
        resolved: list[str] = []

        query_kwargs = {"exchange_id": exchange_id} if exchange_id else {}
        cont_symbols = list(api.query_cont_quotes(**query_kwargs))
        for cont_symbol in cont_symbols:
            quote = api.get_quote(cont_symbol)
            underlying_symbol = getattr(quote, "underlying_symbol", "")
            if underlying_symbol:
                resolved.append(str(underlying_symbol))

        resolved = self._dedupe_symbols(self._normalize_symbols(resolved))
        if resolved:
            return resolved

        futures = list(api.query_quotes(ins_class="FUTURE", expired=False, **query_kwargs))
        return self._dedupe_symbols(self._normalize_symbols(futures))

    def _resolve_real_symbols(
        self,
        symbols: list[str],
        api,
        selection_mode: str = "custom",
        selection_exchanges: list[str] | None = None,
    ) -> list[str]:
        normalized = self._normalize_symbols(symbols)
        exchanges = [exchange for exchange in (selection_exchanges or []) if exchange]
        if selection_mode == "exchange":
            resolved: list[str] = []
            for exchange in exchanges:
                resolved.extend(self._resolve_all_real_symbols(api, exchange_id=exchange))
            resolved = self._dedupe_symbols(resolved)
            if not resolved:
                raise RuntimeError(f"交易所 {', '.join(exchanges)} 未查询到任何有效期货合约")
            self._logger.info("交易所 %s 请求已解析为 %d 个有效合约", ", ".join(exchanges), len(resolved))
            return resolved
        if selection_mode == "all" or self._is_all_symbols_request(normalized):
            resolved = self._resolve_all_real_symbols(api)
            if not resolved:
                raise RuntimeError("ALL/全部 请求未查询到任何有效期货合约")
            self._logger.info("ALL/全部 请求已解析为 %d 个有效合约", len(resolved))
            return resolved
        filtered = [symbol for symbol in normalized if not is_all_selection_token(symbol)]
        mapping = self._build_custom_symbol_mapping(filtered)
        resolved: list[str] = []
        for symbol in filtered:
            resolved_symbol = self._resolve_quote_symbol(api, symbol)
            resolved.append(resolved_symbol)
            mapped_from = mapping.get(symbol.upper(), symbol)
            if resolved_symbol != mapped_from:
                self._logger.info("自定义品种 %s 已解析为当前有效合约 %s", mapped_from, resolved_symbol)
        return self._dedupe_symbols(self._normalize_symbols(resolved))

    def _stream_mock(
        self,
        symbols: list[str],
        max_updates: int | None = None,
        stop_flag: Callable[[], bool] | None = None,
        selection_mode: str = "custom",
        selection_exchanges: list[str] | None = None,
    ) -> Iterator[tuple[str, Kline]]:
        emitted = 0
        safe_symbols = self._resolve_mock_symbols(
            symbols,
            selection_mode=selection_mode,
            selection_exchanges=selection_exchanges,
        )

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
        selection_mode: str = "custom",
        selection_exchanges: list[str] | None = None,
    ) -> Iterator[tuple[str, Kline]]:
        if not self._config.tq_account or not self._config.tq_password:
            raise ValueError(
                "真实行情模式需要填写可用于 TqSdk/快期认证的快期账户（手机号、邮箱或用户名）及对应密码，"
                "不是期货实盘账号，也不是普通模拟交易编号。"
            )

        from tqsdk import TqApi, TqAuth

        api = TqApi(auth=TqAuth(self._config.tq_account, self._config.tq_password))
        safe_symbols = self._resolve_real_symbols(
            symbols,
            api,
            selection_mode=selection_mode,
            selection_exchanges=selection_exchanges,
        )
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
        selection_mode: str = "custom",
        selection_exchanges: list[str] | None = None,
    ):
        use_real = bool(getattr(self._config, "use_real_market_data", False))
        strict_real_mode = bool(getattr(self._config, "strict_real_mode", True))

        if not use_real:
            yield from self._stream_mock(
                symbols,
                max_updates=max_updates,
                stop_flag=stop_flag,
                selection_mode=selection_mode,
                selection_exchanges=selection_exchanges,
            )
            return

        try:
            yield from self._stream_real(
                symbols,
                max_updates=max_updates,
                stop_flag=stop_flag,
                selection_mode=selection_mode,
                selection_exchanges=selection_exchanges,
            )
        except Exception as exc:
            if strict_real_mode:
                raise ValueError(f"{exc} 如确认账号密码无误，请检查该账户是否开通快期/TqSdk认证权限。") from exc
            self._logger.warning("Real market data unavailable, fallback to mock stream: %s", exc)
            yield from self._stream_mock(
                symbols,
                max_updates=max_updates,
                stop_flag=stop_flag,
                selection_mode=selection_mode,
                selection_exchanges=selection_exchanges,
            )

    def get_latest_snapshot(self, symbols: list[str]) -> dict[str, Kline]:
        safe_symbols = symbols or list(self._latest_snapshot.keys())
        return {symbol: self._latest_snapshot[symbol] for symbol in safe_symbols if symbol in self._latest_snapshot}
