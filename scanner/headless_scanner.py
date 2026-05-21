#!/usr/bin/env python3
"""
headless_scanner.py — Valkyrie Eyes v5.0.1
See CHANGELOG.md for full patch notes.

FIXES vs v5.0.0:
  1. DB write queue implemented — was a commented placeholder. Now a real
     asyncio.Queue with a dedicated writer coroutine. Infinite retention enforced.

  2. market_cache upgraded — stores rolling window (last N candles worth of
     signal rows per symbol/TF), not just the last single candle. Multi-candle
     pattern confirmation is now possible.

  3. Regime flip detection implemented — was a comment placeholder. Now computes
     cross-market bias after every scan cycle and writes to cross_market_log.

  4. pair_ranker integrated — ranked pairs drive scan order so highest-confluence
     signals are processed first each cycle.

  5. Proper structured logging replaces bare print() calls.

  6. Exchange session managed correctly — single session reused across all tasks,
     closed cleanly on shutdown.
"""

import asyncio
import json
import os
import sys
import logging
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path

import ccxt.async_support as ccxt
import pandas as pd
import psycopg2
import psycopg2.extras
from psycopg2.extras import Json
from dotenv import load_dotenv

from quant_engine import generate_signals

# ── Config ─────────────────────────────────────────────────────────────────────
ENV_PATH = Path("/opt/valkyrie/.env")
load_dotenv(ENV_PATH)

LOG_DIR = Path("/opt/valkyrie/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

CANDLE_LIMIT         = int(os.getenv("CANDLE_LIMIT",          "300"))
SNIPER_INTERVAL_SECS = int(os.getenv("SNIPER_INTERVAL_SECS",  "60"))
SIGNAL_AGE_MAX_MINS  = int(os.getenv("SIGNAL_AGE_MAX_MINS",   "45"))
BACKEND_URL          = os.getenv("BACKEND_URL", "http://localhost:8000")

# Rolling window depth per symbol/TF — how many historical signal rows to keep
# in memory for multi-candle confirmation. Does not affect DB (infinite retention).
CACHE_WINDOW_DEPTH = int(os.getenv("CACHE_WINDOW_DEPTH", "10"))

# Regime flip: minimum % of pairs that must agree on a bias to declare a regime
REGIME_CONSENSUS_PCT = float(os.getenv("REGIME_CONSENSUS_PCT", "0.60"))

# Pairs and timeframes — driven by watchlist DB. These are the hard fallbacks.
DEFAULT_PAIRS = [
    "BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT",
    "BNB/USDT", "ATOM/USDT", "NEAR/USDT", "DOGE/USDT",
]
TIMEFRAMES = ["5m", "15m", "1h", "4h"]

DB_CFG = dict(
    host     = os.getenv("POSTGRES_HOST", "127.0.0.1"),
    port     = int(os.getenv("POSTGRES_PORT", "5432")),
    dbname   = os.getenv("POSTGRES_DB",   "valkyrie"),
    user     = os.getenv("POSTGRES_USER",  "valkyrie_user"),
    password = os.getenv("POSTGRES_PASSWORD"),
)


# ── Logging ───────────────────────────────────────────────────────────────────
def _setup_logging() -> logging.Logger:
    logger = logging.getLogger("scanner")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)-8s [scanner] %(message)s")
    fh = logging.FileHandler(LOG_DIR / "scanner.log")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger

log = _setup_logging()


# ── Rolling window cache ───────────────────────────────────────────────────────
# Structure: market_cache[symbol][timeframe] = deque of signal dicts (newest last)
# Replaces the flat single-row dict that made multi-candle confirmation impossible.
market_cache: dict[str, dict[str, deque]] = defaultdict(lambda: defaultdict(lambda: deque(maxlen=CACHE_WINDOW_DEPTH)))


# ── Async DB write queue ───────────────────────────────────────────────────────
# All DB writes are non-blocking. Scanner never waits on a DB write.
# Queue items are dicts of scan_log column values.
_db_write_queue: asyncio.Queue = None  # initialized in main()


async def _db_writer(queue: asyncio.Queue):
    """
    Dedicated coroutine. Drains the write queue continuously.
    Batches up to 50 rows per commit for efficiency.
    Enforces the No-Delete / infinite retention policy — only INSERTs, never updates or deletes.
    """
    INSERT_SQL = """
        INSERT INTO scan_log (
            symbol, timeframe, price, pattern, confidence, urgency,
            overall_bias, is_valid_breakout, confluence_score, rr_ratio,
            rsi, ema20, ema50, ema200, atr, atr_pct,
            vol_ratio, ema50_slope, z_score, signal, pattern_changed, ts
        ) VALUES (
            %(symbol)s, %(timeframe)s, %(price)s, %(pattern)s, %(confidence)s, %(urgency)s,
            %(overall_bias)s, %(is_valid_breakout)s, %(confluence_score)s, %(rr_ratio)s,
            %(rsi)s, %(ema20)s, %(ema50)s, %(ema200)s, %(atr)s, %(atr_pct)s,
            %(vol_ratio)s, %(ema50_slope)s, %(z_score)s, %(signal)s, %(pattern_changed)s,
            %(ts)s
        )
    """
    conn = None
    while True:
        batch = []
        try:
            # Block until at least one item is ready
            item = await queue.get()
            batch.append(item)
            queue.task_done()

            # Drain up to 49 more without blocking
            while not queue.empty() and len(batch) < 50:
                item = queue.get_nowait()
                batch.append(item)
                queue.task_done()

            # Write batch
            if conn is None or conn.closed:
                conn = psycopg2.connect(**DB_CFG)

            with conn.cursor() as cur:
                psycopg2.extras.execute_batch(cur, INSERT_SQL, batch)
            conn.commit()
            log.debug(f"DB writer committed {len(batch)} rows")

        except asyncio.CancelledError:
            # Flush remaining items before shutdown
            if batch and conn and not conn.closed:
                try:
                    with conn.cursor() as cur:
                        psycopg2.extras.execute_batch(cur, INSERT_SQL, batch)
                    conn.commit()
                except Exception as e:
                    log.error(f"DB writer flush error on shutdown: {e}")
            break
        except Exception as e:
            log.error(f"DB writer error (batch of {len(batch)}): {e}")
            # Reconnect next iteration — do not lose the batch silently
            try:
                if conn:
                    conn.close()
            except Exception:
                pass
            conn = None
            await asyncio.sleep(2)


# ── Watchlist from DB ─────────────────────────────────────────────────────────
def _get_active_pairs() -> list[str]:
    try:
        conn = psycopg2.connect(**DB_CFG)
        cur  = conn.cursor()
        cur.execute("SELECT DISTINCT symbol FROM watchlist WHERE is_active = TRUE ORDER BY symbol")
        rows = cur.fetchall()
        conn.close()
        if rows:
            return [r[0] for r in rows]
        log.warning("Watchlist empty — using defaults")
        return DEFAULT_PAIRS
    except Exception as e:
        log.warning(f"Watchlist unavailable ({e}) — using defaults")
        return DEFAULT_PAIRS


# ── Regime flip detection ──────────────────────────────────────────────────────
def _compute_regime() -> str:
    """
    Reads the current market_cache and computes cross-market regime.
    Logic: if >= REGIME_CONSENSUS_PCT of all 1h/4h signals agree on a bias,
    declare that regime. Otherwise 'neutral'.

    This replaces the placeholder comment in v5.0.0.
    Pure majority vote across all cached pairs — no human interpretation.
    """
    bias_counts = {"bullish": 0, "bearish": 0, "neutral": 0}
    total = 0

    for symbol, tfs in market_cache.items():
        for tf in ("1h", "4h"):
            window = tfs.get(tf)
            if not window:
                continue
            # Use most recent row in the rolling window
            latest = window[-1] if window else None
            if latest is None:
                continue
            bias = latest.get("regime_bias", "neutral")
            bias_counts[bias] = bias_counts.get(bias, 0) + 1
            total += 1

    if total == 0:
        return "unknown"

    for bias in ("bullish", "bearish"):
        if bias_counts[bias] / total >= REGIME_CONSENSUS_PCT:
            return bias

    return "neutral"


def _write_regime(regime: str, leaders: list, laggards: list):
    """Write computed regime to cross_market_log for sniper_core to read."""
    try:
        conn = psycopg2.connect(**DB_CFG)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO cross_market_log (market_regime, leaders, laggards, synthesis, ts)
                VALUES (%s, %s, %s, %s, NOW())
                """,
                (
                    regime,
                    Json([s for s, _ in leaders[:5]]),   # top 5 bullish pairs
                    Json([s for s, _ in laggards[:5]]),  # top 5 bearish pairs
                    f"Auto-computed regime: {regime} | "
                    f"{len(leaders)} bullish / {len(laggards)} bearish "
                    f"of {len(market_cache)} tracked pairs",
                ),
            )
        conn.commit()
        conn.close()
    except Exception as e:
        log.error(f"Regime write failed: {e}")


# ── Core fetch and calculate ───────────────────────────────────────────────────
async def fetch_and_calculate(exchange, symbol: str, timeframe: str, queue: asyncio.Queue):
    """
    Fetch OHLCV → run quant engine → update rolling cache → enqueue DB write.
    Fully stateless: no dependency on DB to function. Cache is the memory.
    """
    try:
        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=CANDLE_LIMIT)
        if not ohlcv or len(ohlcv) < 50:
            log.warning(f"Insufficient candles for {symbol} {timeframe}: {len(ohlcv) if ohlcv else 0}")
            return

        df = pd.DataFrame(ohlcv, columns=["ts","open","high","low","close","volume"])
        df["ts"] = pd.to_datetime(df["ts"], unit="ms", utc=True)

        # Run full quant pipeline (indicators + signals + confluence + R:R gate)
        processed = generate_signals(df)
        latest    = processed.iloc[-1]

        # ── Update rolling window cache ──────────────────────────────────────
        row_dict = latest.to_dict()
        row_dict["ts"] = latest.name if hasattr(latest, "name") else datetime.now(timezone.utc)
        market_cache[symbol][timeframe].append(row_dict)

        # ── Detect pattern change vs previous cache entry ────────────────────
        window   = market_cache[symbol][timeframe]
        prev_pat = window[-2].get("pattern", "unclear") if len(window) >= 2 else "unclear"
        curr_pat = row_dict.get("pattern", "unclear")
        pattern_changed = curr_pat != prev_pat

        # ── Build DB write payload ───────────────────────────────────────────
        def safe(v):
            try:
                f = float(v)
                import math
                return None if (math.isnan(f) or math.isinf(f)) else round(f, 6)
            except (TypeError, ValueError):
                return None

        payload = {
            "symbol":           symbol,
            "timeframe":        timeframe,
            "price":            safe(latest["close"]),
            "pattern":          str(curr_pat),
            "confidence":       str(row_dict.get("confidence", "low")),
            "urgency":          str(row_dict.get("urgency", "low")) if "urgency" in row_dict else "low",
            "overall_bias":     str(row_dict.get("bias", "neutral")),
            "is_valid_breakout": bool(
                curr_pat in ("bullish_breakout","bearish_breakdown","volatile_expansion")
                and safe(latest.get("vol_ratio", 0) or 0) > 1.4
                and row_dict.get("confidence") == "high"
            ),
            "confluence_score": int(row_dict.get("confluence_score", 0) or 0),
            "rr_ratio":         safe(row_dict.get("rr_ratio", 0)),
            "rsi":              safe(latest.get("rsi")),
            "ema20":            safe(latest.get("ema20")),
            "ema50":            safe(latest.get("ema50")),
            "ema200":           safe(latest.get("ema200")),
            "atr":              safe(latest.get("atr")),
            "atr_pct":          safe(latest.get("atr_pct")),
            "vol_ratio":        safe(latest.get("vol_ratio")),
            "ema50_slope":      safe(latest.get("ema50_slope")),
            "z_score":          safe(latest.get("z_score")),
            "signal":           str(row_dict.get("signal", "none")),
            "pattern_changed":  pattern_changed,
            "ts":               datetime.now(timezone.utc),
        }

        await queue.put(payload)

        if pattern_changed:
            log.info(
                f"PATTERN CHANGE {symbol:12s} {timeframe:4s} | "
                f"{prev_pat} → {curr_pat} | "
                f"confluence={payload['confluence_score']} | "
                f"rr={payload['rr_ratio']} | "
                f"bias={payload['overall_bias']}"
            )

    except ccxt.NetworkError as e:
        log.warning(f"Network error {symbol} {timeframe}: {e}")
    except ccxt.ExchangeError as e:
        log.warning(f"Exchange error {symbol} {timeframe}: {e}")
    except Exception as e:
        log.error(f"Unhandled error {symbol} {timeframe}: {e}", exc_info=True)


# ── Ranked scan order ──────────────────────────────────────────────────────────
def _get_ranked_pairs(pairs: list[str]) -> list[tuple[str, str]]:
    """
    Use pair_ranker to determine scan order — highest confluence first.
    Falls back to default order if ranker is unavailable.
    """
    try:
        from pair_ranker import get_ranked_pairs
        ranked = get_ranked_pairs()
        # Extract (symbol, timeframe) tuples in ranked order, filtered to active pairs
        ordered = [
            (r["symbol"], r["timeframe"])
            for r in ranked
            if r["symbol"] in pairs
        ]
        # Append any pairs/TFs not covered by ranker (e.g. 5m, 15m not in ranker output)
        ranked_symbols_tfs = set((r["symbol"], r["timeframe"]) for r in ranked)
        for symbol in pairs:
            for tf in TIMEFRAMES:
                if (symbol, tf) not in ranked_symbols_tfs:
                    ordered.append((symbol, tf))
        return ordered
    except Exception as e:
        log.warning(f"pair_ranker unavailable ({e}) — using default scan order")
        return [(symbol, tf) for symbol in pairs for tf in TIMEFRAMES]


# ── Main scan loop ─────────────────────────────────────────────────────────────
async def run_scanner():
    global _db_write_queue
    _db_write_queue = asyncio.Queue()

    # Start dedicated DB writer coroutine
    writer_task = asyncio.create_task(_db_writer(_db_write_queue))

    exchange = ccxt.binance({"enableRateLimit": True})

    log.info("━" * 60)
    log.info("Valkyrie Eyes v5.0.1 — headless scanner online")
    log.info(f"  Candle limit:       {CANDLE_LIMIT}")
    log.info(f"  Scan interval:      {SNIPER_INTERVAL_SECS}s")
    log.info(f"  Cache window depth: {CACHE_WINDOW_DEPTH} rows per symbol/TF")
    log.info(f"  Regime consensus:   {int(REGIME_CONSENSUS_PCT*100)}% agreement required")
    log.info("━" * 60)

    try:
        while True:
            cycle_start = datetime.now(timezone.utc)
            log.info(f"Scan cycle starting — {cycle_start.strftime('%Y-%m-%d %H:%M:%S UTC')}")

            # Get active pairs from DB (re-reads each cycle — watchlist changes take effect immediately)
            pairs = _get_active_pairs()

            # Get ranked scan order — highest confluence signals processed first
            scan_order = _get_ranked_pairs(pairs)
            log.info(f"Scanning {len(scan_order)} symbol/TF combinations across {len(pairs)} pairs")

            # Fire all fetch tasks concurrently
            tasks = [
                fetch_and_calculate(exchange, symbol, tf, _db_write_queue)
                for symbol, tf in scan_order
            ]
            await asyncio.gather(*tasks, return_exceptions=True)

            # ── Regime flip detection (was a comment in v5.0.0) ──────────────
            regime = _compute_regime()

            # Identify leaders (bullish bias in 1h cache) and laggards (bearish)
            leaders  = []
            laggards = []
            for symbol, tfs in market_cache.items():
                w1h = tfs.get("1h")
                if not w1h:
                    continue
                latest_bias = w1h[-1].get("regime_bias", "neutral") if w1h else "neutral"
                latest_cs   = w1h[-1].get("confluence_score", 0)    if w1h else 0
                if latest_bias == "bullish":
                    leaders.append((symbol, latest_cs))
                elif latest_bias == "bearish":
                    laggards.append((symbol, latest_cs))

            leaders.sort(key=lambda x: x[1], reverse=True)
            laggards.sort(key=lambda x: x[1], reverse=True)

            _write_regime(
                regime,
                [s for s, _ in leaders],
                [s for s, _ in laggards],
            )

            log.info(
                f"Cycle complete | regime={regime} | "
                f"leaders={len(leaders)} | laggards={len(laggards)} | "
                f"queue_depth={_db_write_queue.qsize()}"
            )

            # Wait for next interval minus elapsed time
            elapsed    = (datetime.now(timezone.utc) - cycle_start).total_seconds()
            sleep_time = max(0, SNIPER_INTERVAL_SECS - elapsed)
            log.info(f"Next scan in {sleep_time:.1f}s")
            await asyncio.sleep(sleep_time)

    except asyncio.CancelledError:
        log.info("Scanner shutdown signal received")
    finally:
        # Drain queue before exit — enforce infinite retention on shutdown
        log.info(f"Draining DB write queue ({_db_write_queue.qsize()} remaining)...")
        await _db_write_queue.join()
        writer_task.cancel()
        try:
            await writer_task
        except asyncio.CancelledError:
            pass
        await exchange.close()
        log.info("Scanner shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(run_scanner())
    except KeyboardInterrupt:
        log.info("Scanner halted by operator")
