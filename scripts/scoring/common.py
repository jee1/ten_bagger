"""Shared numeric helpers used across scoring modules (v1 and v2)."""

from __future__ import annotations

import math
from typing import Any

from config import GROWTH_EARN_WEIGHT, GROWTH_REV_WEIGHT, MAX_GROWTH_PCT, UniverseSymbol


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _clip_growth_pct(value: float) -> float:
    if value <= 0:
        return 0.0
    return min(value, MAX_GROWTH_PCT)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        f = float(value)
        if math.isnan(f) or math.isinf(f):
            return default
        return f
    except (TypeError, ValueError):
        return default


def _optional_float(value: Any) -> float | None:
    """Parse a float, returning None when missing/invalid (not a defaulted zero)."""
    if value is None:
        return None
    try:
        f = float(value)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (TypeError, ValueError):
        return None


def _resolve_market_cap(meta: UniverseSymbol, info: dict[str, Any]) -> float:
    cap = _safe_float(info.get("marketCap"))
    if cap > 0:
        return cap
    if meta.market_cap:
        return float(meta.market_cap)
    return 0.0


def _blended_growth_pct(info: dict[str, Any]) -> tuple[float, float, float]:
    rev_growth = _safe_float(info.get("revenueGrowth"))
    earn_growth = _safe_float(info.get("earningsGrowth"))
    rev_q = _safe_float(info.get("quarterlyRevenueGrowthYOY"))
    earn_q = _safe_float(info.get("quarterlyEarningsGrowthYOY"))

    rev_pct = _clip_growth_pct(max(rev_growth, rev_q) * 100 if max(rev_growth, rev_q) else 0)
    earn_pct = _clip_growth_pct(max(earn_growth, earn_q) * 100 if max(earn_growth, earn_q) else 0)
    blended = rev_pct * GROWTH_REV_WEIGHT + earn_pct * GROWTH_EARN_WEIGHT
    return rev_pct, earn_pct, blended
