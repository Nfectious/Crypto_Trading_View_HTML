"""Phase 1B — Typed config parsers. All read from environment variables."""
import os
import logging
from typing import Optional

log = logging.getLogger(__name__)


def parse_bool(key: str, default: bool = False) -> bool:
    val = os.getenv(key)
    if val is None:
        return default
    v = val.strip().lower()
    if v in ("1", "true", "yes", "on"):
        return True
    if v in ("0", "false", "no", "off"):
        return False
    log.warning("Cannot parse %s=%r as bool, using default %s", key, val, default)
    return default


def parse_int(key: str, default: int) -> int:
    val = os.getenv(key)
    if val is None:
        return default
    try:
        return int(val.strip())
    except ValueError:
        log.warning("Cannot parse %s=%r as int, using default %d", key, val, default)
        return default


def parse_float(key: str, default: float) -> float:
    val = os.getenv(key)
    if val is None:
        return default
    try:
        return float(val.strip())
    except ValueError:
        log.warning("Cannot parse %s=%r as float, using default %f", key, val, default)
        return default


def parse_csv(key: str, default: Optional[list[str]] = None) -> list[str]:
    if default is None:
        default = []
    val = os.getenv(key)
    if val is None or val.strip() == "":
        return default
    return [item.strip() for item in val.split(",") if item.strip()]
