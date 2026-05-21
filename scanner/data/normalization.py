"""Phase 1K — Binance WebSocket payload normalization."""
from .kline_model import NormalizedKline

# Binance quote assets that are exactly 4 characters; used for symbol reconstruction.
# For other lengths (e.g. USDC), the split falls back to a configurable separator.
_KNOWN_QUOTES = frozenset(["USDT", "BUSD", "USDC", "TUSD", "FDUSD", "BTC", "ETH", "BNB"])


def _reconstruct_symbol(raw: str) -> str:
    """
    Reconstruct 'BTC/USDT' from 'BTCUSDT'.
    Tries known quote assets longest-first to avoid ambiguity.
    Returns raw string unchanged if no match is found.
    """
    upper = raw.upper()
    for quote in sorted(_KNOWN_QUOTES, key=len, reverse=True):
        if upper.endswith(quote) and len(upper) > len(quote):
            base = upper[: len(upper) - len(quote)]
            return f"{base}/{quote}"
    return upper


def normalize_binance_kline(
    payload: dict,
    exchange: str = "binance",
) -> NormalizedKline:
    """
    Convert a raw Binance combined-stream kline payload to NormalizedKline.

    Expected payload shape (combined stream wrapper):
        {"stream": "btcusdt@kline_5m", "data": {"e": "kline", "E": ..., "s": ..., "k": {...}}}

    Also handles unwrapped single-stream payloads where the top level is the event dict.
    """
    data = payload.get("data", payload)
    k = data["k"]

    raw_symbol = data.get("s") or k.get("s") or ""
    symbol = _reconstruct_symbol(raw_symbol)

    return NormalizedKline(
        exchange=exchange,
        symbol=symbol,
        timeframe=k["i"],
        event_time_ms=int(data.get("E", 0)),
        open_time_ms=int(k["t"]),
        close_time_ms=int(k["T"]),
        open=float(k["o"]),
        high=float(k["h"]),
        low=float(k["l"]),
        close=float(k["c"]),
        volume=float(k["v"]),
        quote_volume=float(k["q"]),
        trade_count=int(k["n"]),
        is_closed=bool(k["x"]),
    )
