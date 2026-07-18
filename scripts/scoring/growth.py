"""Growth scoring — v2 production path (sustainable-growth sweet-spot curve)."""

from __future__ import annotations

from typing import Any

from config import GROWTH_PENALTY_ABOVE, GROWTH_SWEET_HIGH, GROWTH_SWEET_LOW, GROWTH_SWEET_PEAK
from scoring.common import _blended_growth_pct


def _score_growth(info: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    rev_pct, earn_pct, blended = _blended_growth_pct(info)

    if blended <= 0:
        score = 25.0
    elif blended < GROWTH_SWEET_LOW:
        score = 40.0 + blended
    elif blended <= GROWTH_SWEET_HIGH:
        score = 100.0 - abs(blended - GROWTH_SWEET_PEAK)
    else:
        excess = blended - GROWTH_PENALTY_ABOVE
        score = max(35.0, 80.0 - excess * 1.2)

    return score, {
        "revenue_growth_pct": round(rev_pct, 2),
        "earnings_growth_pct": round(earn_pct, 2),
        "blended_growth_pct": round(blended, 2),
    }
