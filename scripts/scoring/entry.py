"""Entry-timing scoring — v2-only (12-month range position + recovery from high)."""

from __future__ import annotations

from typing import Any

import pandas as pd
from config import (
    ENTRY_AT_HIGH_RECOVERY_SCORE,
    ENTRY_DEFAULT_SCORE,
    ENTRY_LOOKBACK_DAYS,
    ENTRY_MID_HIGH_PCT,
    ENTRY_MID_HIGH_SCORE,
    ENTRY_MID_RANGE_PCT,
    ENTRY_MID_RANGE_SCORE,
    ENTRY_NEAR_HIGH_PCT,
    ENTRY_NEAR_HIGH_SCORE,
    ENTRY_NEAR_LOW_SCORE,
    ENTRY_RANGE_WEIGHT,
    ENTRY_RECOVERY_WEIGHT,
    MOMENTUM_DEEP_PULLBACK_SCORE,
    MOMENTUM_MIN_HISTORY_DAYS,
    MOMENTUM_RECOVERY_HIGH,
    MOMENTUM_RECOVERY_LOW,
    MOMENTUM_RECOVERY_SCORE,
)
from scoring.common import _clamp


def _score_entry(hist: pd.DataFrame) -> tuple[float, dict[str, Any]]:
    if hist.empty or len(hist) < MOMENTUM_MIN_HISTORY_DAYS:
        return ENTRY_DEFAULT_SCORE, {"twelve_month_range_pct": None, "from_52w_high_pct": None}

    close = hist["Close"]
    latest = float(close.iloc[-1])
    lookback = min(ENTRY_LOOKBACK_DAYS, len(close))
    window = close.iloc[-lookback:]
    low_12m = float(window.min())
    high_12m = float(window.max())
    high_52w = float(close.max())
    from_high = (latest / high_52w - 1) * 100 if high_52w else 0

    if high_12m > low_12m:
        range_pct = (latest - low_12m) / (high_12m - low_12m) * 100
    else:
        range_pct = 50.0

    if range_pct >= ENTRY_NEAR_HIGH_PCT:
        range_score = ENTRY_NEAR_HIGH_SCORE
    elif range_pct >= ENTRY_MID_HIGH_PCT:
        range_score = ENTRY_MID_HIGH_SCORE
    elif range_pct >= ENTRY_MID_RANGE_PCT:
        range_score = ENTRY_MID_RANGE_SCORE
    else:
        range_score = ENTRY_NEAR_LOW_SCORE

    if MOMENTUM_RECOVERY_LOW <= from_high <= MOMENTUM_RECOVERY_HIGH:
        recovery_score = MOMENTUM_RECOVERY_SCORE
    elif from_high > MOMENTUM_RECOVERY_HIGH:
        recovery_score = ENTRY_AT_HIGH_RECOVERY_SCORE
    else:
        recovery_score = MOMENTUM_DEEP_PULLBACK_SCORE

    score = _clamp(range_score * ENTRY_RANGE_WEIGHT + recovery_score * ENTRY_RECOVERY_WEIGHT)
    return score, {
        "twelve_month_range_pct": round(range_pct, 2),
        "from_52w_high_pct": round(from_high, 2),
    }
