"""Valuation scoring. _score_pe_peg feeds both v1 and v2; FCF yield and P/B are v2-only."""

from __future__ import annotations

import math
from typing import Any

from config import (
    BM_EXCELLENT,
    BM_FAIR,
    BM_GOOD,
    BM_SCORE_EXCELLENT,
    BM_SCORE_FAIR,
    BM_SCORE_GOOD,
    BM_SCORE_POOR,
    FCF_SCORE_EXCELLENT,
    FCF_SCORE_FAIR,
    FCF_SCORE_GOOD,
    FCF_SCORE_NEGATIVE,
    FCF_SCORE_POOR,
    FCF_YIELD_EXCELLENT,
    FCF_YIELD_FAIR,
    FCF_YIELD_GOOD,
    FCF_YIELD_POOR,
    PE_BLEND_WEIGHT,
    PE_SCORE_EXCELLENT,
    PE_SCORE_FAIR,
    PE_SCORE_GOOD,
    PE_SCORE_POOR,
    PE_TIER_EXCELLENT,
    PE_TIER_FAIR,
    PE_TIER_GOOD,
    PEG_BLEND_WEIGHT,
    PEG_SCORE_EXCELLENT,
    PEG_SCORE_FAIR,
    PEG_SCORE_GOOD,
    PEG_SCORE_POOR,
    PEG_TIER_EXCELLENT,
    PEG_TIER_FAIR,
    PEG_TIER_GOOD,
    VAL_FCF_WEIGHT,
    VAL_PB_WEIGHT,
    VAL_PE_PEG_WEIGHT,
    UniverseSymbol,
)

from scoring.common import _clamp, _resolve_market_cap, _safe_float


def _score_pe_peg(info: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    pe = _safe_float(info.get("trailingPE"))
    peg = _safe_float(info.get("pegRatio"))
    fwd_pe = _safe_float(info.get("forwardPE"))

    pe_ref = pe if pe > 0 else fwd_pe
    pe_score = 50.0
    if pe_ref > 0:
        if pe_ref <= PE_TIER_EXCELLENT:
            pe_score = PE_SCORE_EXCELLENT
        elif pe_ref <= PE_TIER_GOOD:
            pe_score = PE_SCORE_GOOD
        elif pe_ref <= PE_TIER_FAIR:
            pe_score = PE_SCORE_FAIR
        else:
            pe_score = PE_SCORE_POOR

    peg_score = 50.0
    if peg > 0:
        if peg <= PEG_TIER_EXCELLENT:
            peg_score = PEG_SCORE_EXCELLENT
        elif peg <= PEG_TIER_GOOD:
            peg_score = PEG_SCORE_GOOD
        elif peg <= PEG_TIER_FAIR:
            peg_score = PEG_SCORE_FAIR
        else:
            peg_score = PEG_SCORE_POOR

    score = _clamp(pe_score * PE_BLEND_WEIGHT + peg_score * PEG_BLEND_WEIGHT)
    metrics = {"pe": round(pe_ref, 2) if pe_ref else None, "peg": round(peg, 2) if peg else None}
    return score, metrics


def _score_fcf_yield(info: dict[str, Any], meta: UniverseSymbol) -> tuple[float, dict[str, Any]]:
    fcf = _safe_float(info.get("freeCashflow"), default=float("nan"))
    cap = _resolve_market_cap(meta, info)

    if math.isnan(fcf) or cap <= 0:
        return 50.0, {"fcf_yield_pct": None}

    yield_pct = (fcf / cap) * 100
    if fcf < 0:
        fcf_score = FCF_SCORE_NEGATIVE
    elif yield_pct >= FCF_YIELD_EXCELLENT:
        fcf_score = FCF_SCORE_EXCELLENT
    elif yield_pct >= FCF_YIELD_GOOD:
        fcf_score = FCF_SCORE_GOOD
    elif yield_pct >= FCF_YIELD_FAIR:
        fcf_score = FCF_SCORE_FAIR
    elif yield_pct >= FCF_YIELD_POOR:
        fcf_score = FCF_SCORE_POOR
    else:
        fcf_score = 30.0

    return _clamp(fcf_score), {"fcf_yield_pct": round(yield_pct, 2)}


def _score_price_to_book(info: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    pb = _safe_float(info.get("priceToBook"))
    if pb <= 0:
        return 50.0, {"price_to_book": None, "book_to_market": None}

    bm = 1.0 / pb
    if bm >= BM_EXCELLENT:
        pb_score = BM_SCORE_EXCELLENT
    elif bm >= BM_GOOD:
        pb_score = BM_SCORE_GOOD
    elif bm >= BM_FAIR:
        pb_score = BM_SCORE_FAIR
    else:
        pb_score = BM_SCORE_POOR

    return _clamp(pb_score), {
        "price_to_book": round(pb, 2),
        "book_to_market": round(bm, 3),
    }


def _score_valuation(info: dict[str, Any], meta: UniverseSymbol) -> tuple[float, dict[str, Any]]:
    pe_score, pe_m = _score_pe_peg(info)
    fcf_score, fcf_m = _score_fcf_yield(info, meta)
    pb_score, pb_m = _score_price_to_book(info)
    score = _clamp(
        pe_score * VAL_PE_PEG_WEIGHT + fcf_score * VAL_FCF_WEIGHT + pb_score * VAL_PB_WEIGHT
    )
    return score, {**pe_m, **fcf_m, **pb_m}
