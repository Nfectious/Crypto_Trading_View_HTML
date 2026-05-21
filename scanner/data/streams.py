"""Phase 1F — Binance stream name generator. Produces kline stream identifiers."""


def symbol_to_binance(symbol: str) -> str:
    """'BTC/USDT' → 'btcusdt'"""
    return symbol.replace("/", "").lower()


def make_kline_stream(symbol: str, timeframe: str) -> str:
    """'BTC/USDT', '5m' → 'btcusdt@kline_5m'"""
    return f"{symbol_to_binance(symbol)}@kline_{timeframe}"


def make_kline_streams(symbols: list[str], timeframes: list[str]) -> list[str]:
    return [make_kline_stream(sym, tf) for sym in symbols for tf in timeframes]
