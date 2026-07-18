"""Momentum scoring — v2 production path (dampened return; size/entry carry primary weight)."""

from __future__ import annotations

from typing import Any

import pandas as pd
from config import (
    MOMENTUM_DAMPEN_WEIGHT,
    MOMENTUM_DEFAULT_SCORE,
    MOMENTUM_FLOOR,
    MOMENTUM_LOOKBACK_DAYS,
    MOMENTUM_MIN_HISTORY_DAYS,
    MOMENTUM_RET_BASE,
    MOMENTUM_RET_MULTIPLIER,
)

from scoring.common import _clamp


def _score_momentum(hist: pd.DataFrame) -> tuple[float, dict[str, Any]]:
    if hist.empty or len(hist) < MOMENTUM_MIN_HISTORY_DAYS:
        return MOMENTUM_DEFAULT_SCORE, {"six_month_return_pct": None, "from_52w_high_pct": None}

    close = hist["Close"]
    latest = float(close.iloc[-1])
    six_month = float(close.iloc[-min(MOMENTUM_LOOKBACK_DAYS, len(close))])
    high_52w = float(close.max())

    ret_6m = (latest / six_month - 1) * 100 if six_month else 0
    from_high = (latest / high_52w - 1) * 100 if high_52w else 0

    ret_score = _clamp(MOMENTUM_RET_BASE + ret_6m * MOMENTUM_RET_MULTIPLIER)
    score = _clamp(ret_score * MOMENTUM_DAMPEN_WEIGHT + MOMENTUM_FLOOR)
    return score, {
        "six_month_return_pct": round(ret_6m, 2),
        "from_52w_high_pct": round(from_high, 2),
    }
