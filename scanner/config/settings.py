"""Phase 1C — Typed configuration dataclasses. Single source of truth for all config."""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from .parsers import parse_bool, parse_csv, parse_float, parse_int

ENV_PATH = Path("/opt/valkyrie/.env")
load_dotenv(ENV_PATH)

_DEFAULT_PAIRS = [
    "BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT",
    "BNB/USDT", "ATOM/USDT", "NEAR/USDT", "DOGE/USDT",
]
_DEFAULT_TIMEFRAMES = ["5m", "15m", "1h", "4h"]


@dataclass(frozen=True)
class RuntimeConfig:
    candle_limit: int
    sniper_interval_secs: int
    signal_age_max_mins: int
    backend_url: str
    cache_window_depth: int
    regime_consensus_pct: float


@dataclass(frozen=True)
class BinanceConfig:
    api_key: str
    api_secret: str


@dataclass(frozen=True)
class CacheConfig:
    max_chunk_size: int


@dataclass(frozen=True)
class LoggingConfig:
    level: str
    dir: Path


@dataclass(frozen=True)
class DatabaseConfig:
    host: str
    port: int
    dbname: str
    user: str
    password: str

    def as_dict(self) -> dict:
        return dict(
            host=self.host,
            port=self.port,
            dbname=self.dbname,
            user=self.user,
            password=self.password,
        )


@dataclass(frozen=True)
class AppConfig:
    runtime: RuntimeConfig
    binance: BinanceConfig
    cache: CacheConfig
    logging: LoggingConfig
    database: DatabaseConfig
    active_pairs: tuple[str, ...]
    scan_timeframes: tuple[str, ...]


def load_config() -> AppConfig:
    return AppConfig(
        runtime=RuntimeConfig(
            candle_limit=parse_int("CANDLE_LIMIT", 300),
            sniper_interval_secs=parse_int("SNIPER_INTERVAL_SECS", 60),
            signal_age_max_mins=parse_int("SIGNAL_AGE_MAX_MINS", 45),
            backend_url=os.getenv("BACKEND_URL", "http://localhost:8000"),
            cache_window_depth=parse_int("CACHE_WINDOW_DEPTH", 10),
            regime_consensus_pct=parse_float("REGIME_CONSENSUS_PCT", 0.60),
        ),
        binance=BinanceConfig(
            api_key=os.getenv("BINANCE_API_KEY", ""),
            api_secret=os.getenv("BINANCE_API_SECRET", ""),
        ),
        cache=CacheConfig(
            max_chunk_size=parse_int("MAX_CHUNK_SIZE", 200),
        ),
        logging=LoggingConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            dir=Path(os.getenv("LOG_DIR", "/opt/valkyrie/logs")),
        ),
        database=DatabaseConfig(
            host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
            port=parse_int("POSTGRES_PORT", 5432),
            dbname=os.getenv("POSTGRES_DB", "valkyrie"),
            user=os.getenv("POSTGRES_USER", "valkyrie_user"),
            password=os.getenv("POSTGRES_PASSWORD", ""),
        ),
        active_pairs=tuple(parse_csv("ACTIVE_PAIRS", _DEFAULT_PAIRS)),
        scan_timeframes=tuple(parse_csv("SCAN_TIMEFRAMES", _DEFAULT_TIMEFRAMES)),
    )
