"""Phase 1D — Symbol parser. Normalizes and validates trading pair symbols."""
import logging
import re

log = logging.getLogger(__name__)

_SYMBOL_RE = re.compile(r"^[A-Z0-9]{2,10}/[A-Z0-9]{2,10}$")


def normalize_symbol(raw: str) -> str:
    return raw.strip().upper()


def validate_symbol(symbol: str) -> bool:
    return bool(_SYMBOL_RE.match(symbol))


def parse_active_pairs(raw_list: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for raw in raw_list:
        sym = normalize_symbol(raw)
        if not validate_symbol(sym):
            log.warning("Invalid symbol format, skipping: %r", sym)
            continue
        if sym in seen:
            log.warning("Duplicate symbol, skipping: %r", sym)
            continue
        seen.add(sym)
        result.append(sym)
    return result
