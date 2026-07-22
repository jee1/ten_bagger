"""Size (market cap) scoring — v2 production path."""

from __future__ import annotations

from typing import Any

from config import (
    ANALYST_COVERAGE_BONUS,
    ANALYST_LOW_COVERAGE_MAX,
    MAX_IDEAL_MARKET_CAP_KR,
    MAX_IDEAL_MARKET_CAP_US,
    SIZE_IDEAL_BASE,
    UniverseSymbol,
)
from scoring.common import _clamp, _resolve_market_cap, _safe_float


def _score_size(
    meta: UniverseSymbol, info: dict[str, Any], market: str
) -> tuple[float, dict[str, Any]]:
    cap = _resolve_market_cap(meta, info)
    ideal = MAX_IDEAL_MARKET_CAP_KR if market == "KR" else MAX_IDEAL_MARKET_CAP_US

    if cap <= 0:
        base = 50.0
    elif cap <= ideal:
        base = SIZE_IDEAL_BASE
    elif cap <= ideal * 2:
        base = 75.0
    elif cap <= ideal * 5:
        base = 55.0
    elif cap <= ideal * 20:
        base = 35.0
    else:
        base = 15.0

    analysts = info.get("numberOfAnalystOpinions")
    bonus = 0.0
    if analysts is None or _safe_float(analysts, default=-1) < ANALYST_LOW_COVERAGE_MAX:
        bonus = ANALYST_COVERAGE_BONUS

    score = _clamp(base + bonus)
    return score, {
        "market_cap": int(cap) if cap > 0 else None,
        "analyst_count": int(analysts) if analysts is not None else None,
    }
