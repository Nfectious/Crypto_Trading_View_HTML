"""Phase 1E — Timeframe parser. Validates against Binance kline intervals."""
import logging

log = logging.getLogger(__name__)

VALID_BINANCE_INTERVALS: frozenset[str] = frozenset([
    "1s",
    "1m", "3m", "5m", "15m", "30m",
    "1h", "2h", "4h", "6h", "8h", "12h",
    "1d", "3d",
    "1w",
    "1M",
])


def validate_timeframe(tf: str) -> bool:
    return tf in VALID_BINANCE_INTERVALS


def parse_scan_timeframes(raw_list: list[str]) -> list[str]:
    result: list[str] = []
    for raw in raw_list:
        tf = raw.strip()
        if not validate_timeframe(tf):
            log.warning("Invalid Binance timeframe, skipping: %r", tf)
            continue
        result.append(tf)
    return result
