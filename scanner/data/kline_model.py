"""Phase 1J — Normalized kline schema. Exchange-agnostic OHLCV candle model."""
from dataclasses import dataclass


@dataclass(frozen=True)
class NormalizedKline:
    exchange: str
    symbol: str
    timeframe: str
    event_time_ms: int
    open_time_ms: int
    close_time_ms: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    quote_volume: float
    trade_count: int
    is_closed: bool
