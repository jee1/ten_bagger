"""Score v1 — retained only for backtest_screen.py comparisons (Epic #27 / #34).

Not used on the production path (score_version=2); kept isolated here so the
v2 modules (growth.py, quality.py, ...) stay free of legacy branches.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from config import (
    GROWTH_BASE_SCORE,
    GROWTH_SCORE_MULTIPLIER,
    MOMENTUM_DEEP_PULLBACK_SCORE,
    MOMENTUM_DEFAULT_SCORE,
    MOMENTUM_HIGH_WEIGHT,
    MOMENTUM_LOOKBACK_DAYS,
    MOMENTUM_MIN_HISTORY_DAYS,
    MOMENTUM_NEAR_HIGH_SCORE,
    MOMENTUM_RECOVERY_HIGH,
    MOMENTUM_RECOVERY_LOW,
    MOMENTUM_RECOVERY_SCORE,
    MOMENTUM_RET_BASE,
    MOMENTUM_RET_WEIGHT,
    QUALITY_DEBT_EXCELLENT,
    QUALITY_DEBT_FAIR,
    QUALITY_DEBT_GOOD,
    QUALITY_DEBT_SCORE_EXCELLENT,
    QUALITY_DEBT_SCORE_FAIR,
    QUALITY_DEBT_SCORE_GOOD,
    QUALITY_DEBT_SCORE_POOR,
    QUALITY_MARGIN_BASE,
    QUALITY_MARGIN_MULTIPLIER,
    QUALITY_ROE_DEFAULT,
    QUALITY_ROE_MULTIPLIER,
    V1_QUALITY_DEBT_WEIGHT,
    V1_QUALITY_MARGIN_WEIGHT,
    V1_QUALITY_ROE_WEIGHT,
    V1_WEIGHT_GROWTH,
    V1_WEIGHT_MOMENTUM,
    V1_WEIGHT_QUALITY,
    V1_WEIGHT_VALUATION,
)
from scoring.common import _blended_growth_pct, _clamp, _safe_float
from scoring.valuation import _score_pe_peg


def _score_growth_v1(info: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    rev_pct, earn_pct, blended = _blended_growth_pct(info)
    score = _clamp(GROWTH_BASE_SCORE + blended * GROWTH_SCORE_MULTIPLIER)
    return score, {
        "revenue_growth_pct": round(rev_pct, 2),
        "earnings_growth_pct": round(earn_pct, 2),
    }


def _score_valuation_v1(info: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    return _score_pe_peg(info)


def _score_momentum_v1(hist: pd.DataFrame) -> tuple[float, dict[str, Any]]:
    ret_mult = 1.5
    if hist.empty or len(hist) < MOMENTUM_MIN_HISTORY_DAYS:
        return MOMENTUM_DEFAULT_SCORE, {"six_month_return_pct": None, "from_52w_high_pct": None}

    close = hist["Close"]
    latest = float(close.iloc[-1])
    six_month = float(close.iloc[-min(MOMENTUM_LOOKBACK_DAYS, len(close))])
    high_52w = float(close.max())

    ret_6m = (latest / six_month - 1) * 100 if six_month else 0
    from_high = (latest / high_52w - 1) * 100 if high_52w else 0

    ret_score = _clamp(MOMENTUM_RET_BASE + ret_6m * ret_mult)
    if MOMENTUM_RECOVERY_LOW <= from_high <= MOMENTUM_RECOVERY_HIGH:
        high_score = MOMENTUM_RECOVERY_SCORE
    elif from_high > MOMENTUM_RECOVERY_HIGH:
        high_score = MOMENTUM_NEAR_HIGH_SCORE
    else:
        high_score = MOMENTUM_DEEP_PULLBACK_SCORE

    score = _clamp(ret_score * MOMENTUM_RET_WEIGHT + high_score * MOMENTUM_HIGH_WEIGHT)
    return score, {
        "six_month_return_pct": round(ret_6m, 2),
        "from_52w_high_pct": round(from_high, 2),
    }


def _score_quality_v1(info: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    roe = _safe_float(info.get("returnOnEquity"))
    debt = _safe_float(info.get("debtToEquity"))
    margin = _safe_float(info.get("operatingMargins"))

    roe_pct = roe * 100 if abs(roe) < 5 else roe
    roe_score = _clamp(roe_pct * QUALITY_ROE_MULTIPLIER) if roe_pct > 0 else QUALITY_ROE_DEFAULT

    debt_score = 70.0
    if debt > 0:
        if debt < QUALITY_DEBT_EXCELLENT:
            debt_score = QUALITY_DEBT_SCORE_EXCELLENT
        elif debt < QUALITY_DEBT_GOOD:
            debt_score = QUALITY_DEBT_SCORE_GOOD
        elif debt < QUALITY_DEBT_FAIR:
            debt_score = QUALITY_DEBT_SCORE_FAIR
        else:
            debt_score = QUALITY_DEBT_SCORE_POOR

    margin_pct = margin * 100 if abs(margin) < 2 else margin
    margin_score = _clamp(QUALITY_MARGIN_BASE + margin_pct * QUALITY_MARGIN_MULTIPLIER)

    score = _clamp(
        roe_score * V1_QUALITY_ROE_WEIGHT
        + debt_score * V1_QUALITY_DEBT_WEIGHT
        + margin_score * V1_QUALITY_MARGIN_WEIGHT
    )
    return score, {
        "roe_pct": round(roe_pct, 2),
        "debt_to_equity": round(debt, 2) if debt else None,
        "operating_margin_pct": round(margin_pct, 2),
    }


def _composite_v1(growth: float, valuation: float, momentum: float, quality: float) -> float:
    return (
        growth * V1_WEIGHT_GROWTH
        + valuation * V1_WEIGHT_VALUATION
        + momentum * V1_WEIGHT_MOMENTUM
        + quality * V1_WEIGHT_QUALITY
    )
