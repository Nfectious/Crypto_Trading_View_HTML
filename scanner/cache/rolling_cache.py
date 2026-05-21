"""Phase 1L — Rolling cache structure. Keyed by symbol → timeframe → deque of rows."""
from collections import defaultdict, deque
from typing import Any

# Type alias: cache[symbol][timeframe] = deque of row dicts (newest last)
RollingCache = dict[str, dict[str, deque]]


def make_rolling_cache(max_depth: int = 10) -> RollingCache:
    return defaultdict(lambda: defaultdict(lambda: deque(maxlen=max_depth)))


def cache_push(cache: RollingCache, symbol: str, timeframe: str, row: Any) -> None:
    cache[symbol][timeframe].append(row)


def cache_get_latest(cache: RollingCache, symbol: str, timeframe: str) -> Any | None:
    window = cache.get(symbol, {}).get(timeframe)
    return window[-1] if window else None


def cache_get_window(
    cache: RollingCache,
    symbol: str,
    timeframe: str,
) -> deque:
    return cache[symbol][timeframe]
