"""Phase 1M — Partial candle update logic. Mutates the last deque entry in-place."""
from .rolling_cache import RollingCache
from ..data.kline_model import NormalizedKline


def update_partial_candle(cache: RollingCache, kline: NormalizedKline) -> None:
    """
    For in-progress (is_closed=False) candles: replace the last entry rather than
    appending, so the deque window stays consistent and indicator lookback is stable.
    """
    window = cache[kline.symbol][kline.timeframe]
    entry = {
        "open_time_ms": kline.open_time_ms,
        "open": kline.open,
        "high": kline.high,
        "low": kline.low,
        "close": kline.close,
        "volume": kline.volume,
        "is_closed": False,
    }
    if window:
        window[-1] = entry
    else:
        window.append(entry)
