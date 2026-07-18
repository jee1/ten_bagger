"""Quality scoring — v2 production path (ROE/debt/margin/FCF-to-NI/ROA blend)."""

from __future__ import annotations

import math
from typing import Any

from config import (
    QUALITY_DEBT_EXCELLENT,
    QUALITY_DEBT_FAIR,
    QUALITY_DEBT_GOOD,
    QUALITY_DEBT_SCORE_EXCELLENT,
    QUALITY_DEBT_SCORE_FAIR,
    QUALITY_DEBT_SCORE_GOOD,
    QUALITY_DEBT_SCORE_POOR,
    QUALITY_DEBT_WEIGHT,
    QUALITY_FCF_NI_EXCELLENT,
    QUALITY_FCF_NI_GOOD,
    QUALITY_FCF_NI_WEIGHT,
    QUALITY_MARGIN_BASE,
    QUALITY_MARGIN_MULTIPLIER,
    QUALITY_MARGIN_WEIGHT,
    QUALITY_ROA_MULTIPLIER,
    QUALITY_ROA_WEIGHT,
    QUALITY_ROE_DEFAULT,
    QUALITY_ROE_MULTIPLIER,
    QUALITY_ROE_WEIGHT,
)

from scoring.common import _clamp, _safe_float


def _score_quality(info: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    roe = _safe_float(info.get("returnOnEquity"))
    debt = _safe_float(info.get("debtToEquity"))
    margin = _safe_float(info.get("operatingMargins"))
    roa = _safe_float(info.get("returnOnAssets"))
    fcf = _safe_float(info.get("freeCashflow"), default=float("nan"))
    net_income = _safe_float(info.get("netIncomeToCommon"), default=float("nan"))

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

    roa_pct = roa * 100 if abs(roa) < 2 else roa
    roa_score = _clamp(roa_pct * QUALITY_ROA_MULTIPLIER) if roa_pct > 0 else 40.0

    fcf_ni_ratio = None
    fcf_ni_score = 50.0
    if not math.isnan(fcf) and not math.isnan(net_income) and net_income > 0:
        fcf_ni_ratio = fcf / net_income
        if fcf_ni_ratio >= QUALITY_FCF_NI_EXCELLENT:
            fcf_ni_score = 90.0
        elif fcf_ni_ratio >= QUALITY_FCF_NI_GOOD:
            fcf_ni_score = 75.0
        elif fcf_ni_ratio > 0:
            fcf_ni_score = 60.0
        else:
            fcf_ni_score = 35.0

    score = _clamp(
        roe_score * QUALITY_ROE_WEIGHT
        + debt_score * QUALITY_DEBT_WEIGHT
        + margin_score * QUALITY_MARGIN_WEIGHT
        + fcf_ni_score * QUALITY_FCF_NI_WEIGHT
        + roa_score * QUALITY_ROA_WEIGHT
    )
    return score, {
        "roe_pct": round(roe_pct, 2),
        "roa_pct": round(roa_pct, 2),
        "debt_to_equity": round(debt, 2) if debt else None,
        "operating_margin_pct": round(margin_pct, 2),
        "fcf_to_net_income": round(fcf_ni_ratio, 2) if fcf_ni_ratio is not None else None,
    }
