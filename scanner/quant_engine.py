"""
quant_engine.py — Technical indicator and signal engine for Valkyrie Eyes.

Public API: generate_signals(df) -> pd.DataFrame

Input:  OHLCV DataFrame with columns [ts, open, high, low, close, volume]
        Minimum 50 rows required.
Output: Same DataFrame with all indicator and signal columns appended.
        Original rows are not modified. A copy is always returned.
"""
import math

import numpy as np
import pandas as pd


# ── Indicator helpers ─────────────────────────────────────────────────────────

def _ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Wilder smoothing RSI via exponential weighted mean."""
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100.0 - (100.0 / (1.0 + rs))


def _atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df["high"]
    low = df["low"]
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def _z_score(close: pd.Series, window: int = 20) -> pd.Series:
    mean = close.rolling(window).mean()
    std = close.rolling(window).std()
    return (close - mean) / std.replace(0, np.nan)


def _vol_ratio(volume: pd.Series, window: int = 20) -> pd.Series:
    avg = volume.rolling(window).mean()
    return volume / avg.replace(0, np.nan)


# ── Row-wise classifiers ──────────────────────────────────────────────────────

def _safe_float(v) -> float:
    try:
        f = float(v)
        return f if math.isfinite(f) else 0.0
    except (TypeError, ValueError):
        return 0.0


def _classify_pattern(row: pd.Series) -> str:
    price  = _safe_float(row.get("close"))
    ema20  = _safe_float(row.get("ema20"))
    ema50  = _safe_float(row.get("ema50"))
    ema200 = _safe_float(row.get("ema200"))
    rsi    = _safe_float(row.get("rsi", 50))
    vr     = _safe_float(row.get("vol_ratio", 1.0))
    atp    = _safe_float(row.get("atr_pct", 0))

    if ema50 == 0 or ema200 == 0:
        return "unclear"

    if price > ema20 > ema50 > ema200 and rsi > 60 and vr > 1.5 and atp > 0.5:
        return "bullish_breakout"
    if price < ema20 < ema50 < ema200 and rsi < 40 and vr > 1.5 and atp > 0.5:
        return "bearish_breakdown"
    if vr > 2.0 and atp > 1.0:
        return "volatile_expansion"
    if price < ema20 and ema20 > ema50 > ema200 and rsi < 50:
        return "pullback_bull"
    if price > ema20 and ema20 < ema50 < ema200 and rsi > 50:
        return "pullback_bear"

    ema_spread = abs(ema20 - ema50) / ema50 * 100 if ema50 else 0
    if ema_spread < 0.5 and 40 < rsi < 60:
        return "ranging"

    return "unclear"


def _calc_confluence(row: pd.Series) -> int:
    score = 0
    rsi   = _safe_float(row.get("rsi", 50))
    ema50 = _safe_float(row.get("ema50"))
    ema200= _safe_float(row.get("ema200"))
    price = _safe_float(row.get("close"))
    vr    = _safe_float(row.get("vol_ratio", 1.0))
    atp   = _safe_float(row.get("atr_pct", 0))
    z     = _safe_float(row.get("z_score", 0))
    slope = _safe_float(row.get("ema50_slope", 0))

    if rsi > 60 or rsi < 40:
        score += 1
    if ema50 > 0 and ema200 > 0:
        if ema50 > ema200:
            score += 1
        if price > ema50:
            score += 1
    if vr > 1.5:
        score += 2
    elif vr > 1.2:
        score += 1
    if atp > 0.8:
        score += 1
    if abs(z) > 1.5:
        score += 1
    if abs(slope) > 0.0001:
        score += 1

    return min(score, 10)


def _calc_bias(row: pd.Series) -> str:
    ema50  = _safe_float(row.get("ema50"))
    ema200 = _safe_float(row.get("ema200"))
    price  = _safe_float(row.get("close"))
    rsi    = _safe_float(row.get("rsi", 50))
    slope  = _safe_float(row.get("ema50_slope", 0))

    if ema50 == 0 or ema200 == 0:
        return "neutral"

    bull = int(price > ema50) + int(ema50 > ema200) + int(rsi > 55) + int(slope > 0)
    bear = int(price < ema50) + int(ema50 < ema200) + int(rsi < 45) + int(slope < 0)

    if bull >= 3:
        return "bullish"
    if bear >= 3:
        return "bearish"
    return "neutral"


def _calc_urgency(row: pd.Series) -> str:
    vr  = _safe_float(row.get("vol_ratio", 1.0))
    atp = _safe_float(row.get("atr_pct", 0))
    if vr > 2.0 and atp > 1.0:
        return "high"
    if vr > 1.4:
        return "medium"
    return "low"


def _calc_signal(row: pd.Series) -> str:
    pattern    = row.get("pattern", "unclear")
    bias       = row.get("bias", "neutral")
    confidence = row.get("confidence", "low")

    if pattern == "bullish_breakout" and confidence == "high":
        return "buy"
    if pattern == "bearish_breakdown" and confidence == "high":
        return "sell"
    if pattern == "pullback_bull" and bias == "bullish" and confidence in ("high", "medium"):
        return "buy"
    if pattern == "pullback_bear" and bias == "bearish" and confidence in ("high", "medium"):
        return "sell"
    return "none"


# ── Public API ────────────────────────────────────────────────────────────────

def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute all technical indicators and classify signals for every row.

    Returns a copy of the input DataFrame with the following columns appended:
        ema20, ema50, ema200, rsi, atr, atr_pct, vol_ratio, ema50_slope,
        z_score, confluence_score, pattern, bias, regime_bias, confidence,
        urgency, rr_ratio, signal

    Raises ValueError if df has fewer than 50 rows.
    """
    if len(df) < 50:
        raise ValueError(f"Insufficient data: {len(df)} rows, minimum 50 required")

    df = df.copy()

    # ── Vectorized indicators ─────────────────────────────────────────────────
    df["ema20"]       = _ema(df["close"], 20)
    df["ema50"]       = _ema(df["close"], 50)
    df["ema200"]      = _ema(df["close"], 200)
    df["rsi"]         = _rsi(df["close"])
    df["atr"]         = _atr(df)
    df["atr_pct"]     = (df["atr"] / df["close"].replace(0, np.nan)) * 100
    df["vol_ratio"]   = _vol_ratio(df["volume"])
    df["ema50_slope"] = df["ema50"].diff()
    df["z_score"]     = _z_score(df["close"])

    # ── Row-wise classification ───────────────────────────────────────────────
    df["confluence_score"] = df.apply(_calc_confluence, axis=1)
    df["pattern"]          = df.apply(_classify_pattern, axis=1)
    df["bias"]             = df.apply(_calc_bias, axis=1)
    df["regime_bias"]      = df["bias"]  # alias used by regime detection in scanner
    df["confidence"]       = df["confluence_score"].map(
        lambda s: "high" if s >= 7 else ("medium" if s >= 4 else "low")
    )
    df["urgency"]   = df.apply(_calc_urgency, axis=1)
    df["rr_ratio"]  = 2.0  # fixed: stop=1×ATR, target=2×ATR — upgradeable via config
    df["signal"]    = df.apply(_calc_signal, axis=1)

    return df
