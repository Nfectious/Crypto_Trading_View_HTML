"""Phase 1N — Closed candle finalization. Appends immutable rows; handoff point for indicators."""
from .rolling_cache import RollingCache
from ..data.kline_model import NormalizedKline


def finalize_candle(cache: RollingCache, kline: NormalizedKline) -> dict:
    """
    For closed (is_closed=True) candles: append an immutable row to the rolling window.
    Returns the finalized dict for downstream indicator processing.
    Caller is responsible for passing only closed klines (kline.is_closed == True).
    """
    entry: dict = {
        "open_time_ms": kline.open_time_ms,
        "close_time_ms": kline.close_time_ms,
        "open": kline.open,
        "high": kline.high,
        "low": kline.low,
        "close": kline.close,
        "volume": kline.volume,
        "quote_volume": kline.quote_volume,
        "trade_count": kline.trade_count,
        "is_closed": True,
    }
    cache[kline.symbol][kline.timeframe].append(entry)
    return entry
