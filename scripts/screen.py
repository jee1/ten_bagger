"""Rule-based ten-bagger screening engine."""

from __future__ import annotations

import json
import logging
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from config import (
    ANALYST_COVERAGE_BONUS,
    ANALYST_LOW_COVERAGE_MAX,
    BM_EXCELLENT,
    BM_FAIR,
    BM_GOOD,
    BM_SCORE_EXCELLENT,
    BM_SCORE_FAIR,
    BM_SCORE_GOOD,
    BM_SCORE_POOR,
    COMPOSITE_THRESHOLD,
    ENTRY_AT_HIGH_RECOVERY_SCORE,
    ENTRY_DEFAULT_SCORE,
    ENTRY_LOOKBACK_DAYS,
    ENTRY_MID_HIGH_SCORE,
    ENTRY_MID_RANGE_SCORE,
    ENTRY_NEAR_HIGH_PCT,
    ENTRY_NEAR_HIGH_SCORE,
    ENTRY_NEAR_LOW_SCORE,
    ENTRY_RANGE_WEIGHT,
    ENTRY_RECOVERY_WEIGHT,
    FCF_SCORE_EXCELLENT,
    FCF_SCORE_FAIR,
    FCF_SCORE_GOOD,
    FCF_SCORE_NEGATIVE,
    FCF_SCORE_POOR,
    FCF_YIELD_EXCELLENT,
    FCF_YIELD_FAIR,
    FCF_YIELD_GOOD,
    FCF_YIELD_POOR,
    GROWTH_BASE_SCORE,
    GROWTH_EARN_WEIGHT,
    GROWTH_PENALTY_ABOVE,
    GROWTH_REV_WEIGHT,
    GROWTH_SCORE_MULTIPLIER,
    GROWTH_SWEET_HIGH,
    GROWTH_SWEET_LOW,
    GROWTH_SWEET_PEAK,
    MAX_GROWTH_PCT,
    MAX_IDEAL_MARKET_CAP_KR,
    MAX_IDEAL_MARKET_CAP_US,
    MIN_MARKET_CAP_KR,
    MIN_MARKET_CAP_US,
    ENTRY_MID_HIGH_PCT,
    ENTRY_MID_RANGE_PCT,
    MOMENTUM_DEEP_PULLBACK_SCORE,
    MOMENTUM_DEFAULT_SCORE,
    MOMENTUM_DAMPEN_WEIGHT,
    MOMENTUM_FLOOR,
    MOMENTUM_HIGH_WEIGHT,
    MOMENTUM_LOOKBACK_DAYS,
    MOMENTUM_MIN_HISTORY_DAYS,
    MOMENTUM_NEAR_HIGH_SCORE,
    MOMENTUM_RECOVERY_HIGH,
    MOMENTUM_RECOVERY_LOW,
    MOMENTUM_RECOVERY_SCORE,
    MOMENTUM_RET_BASE,
    MOMENTUM_RET_MULTIPLIER,
    MOMENTUM_RET_WEIGHT,
    SIZE_IDEAL_BASE,
    V1_QUALITY_DEBT_WEIGHT,
    V1_QUALITY_MARGIN_WEIGHT,
    V1_QUALITY_ROE_WEIGHT,
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
    SCORE_VERSION,
    SCREEN_WORKERS,
    UNIVERSE_DIR,
    V1_WEIGHT_GROWTH,
    V1_WEIGHT_MOMENTUM,
    V1_WEIGHT_QUALITY,
    V1_WEIGHT_VALUATION,
    VAL_FCF_WEIGHT,
    VAL_PB_WEIGHT,
    VAL_PE_PEG_WEIGHT,
    WEIGHT_ENTRY,
    WEIGHT_GROWTH,
    WEIGHT_MOMENTUM,
    WEIGHT_QUALITY,
    WEIGHT_SIZE,
    WEIGHT_VALUATION,
    UniverseSymbol,
)
from yf_cache import get_ticker_history, get_ticker_info

logger = logging.getLogger(__name__)


@dataclass
class ScoreResult:
    symbol: str
    meta: UniverseSymbol
    size: float
    growth: float
    valuation: float
    entry: float
    momentum: float
    quality: float
    composite: float
    metrics: dict[str, Any]
    score_version: int = SCORE_VERSION


@dataclass
class ScreenStats:
    screened: int = 0
    passed_threshold: int = 0
    skipped_recent: int = 0
    skipped_market_cap: int = 0
    skipped_red_flags: int = 0
    no_data: int = 0
    errors: int = 0
    error_samples: list[str] = field(default_factory=list)


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


def load_universe(market: str) -> list[UniverseSymbol]:
    path = UNIVERSE_DIR / ("kr.json" if market == "KR" else "us.json")
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [
        UniverseSymbol(
            symbol=item["symbol"],
            name_ko=item["name_ko"],
            name_en=item["name_en"],
            exchange=item["exchange"],
            currency=item["currency"],
            market_cap=item.get("market_cap"),
        )
        for item in raw
    ]


def _resolve_market_cap(meta: UniverseSymbol, info: dict[str, Any]) -> float:
    cap = _safe_float(info.get("marketCap"))
    if cap > 0:
        return cap
    if meta.market_cap:
        return float(meta.market_cap)
    return 0.0


def passes_market_cap_filter(
    meta: UniverseSymbol,
    market: str,
    info: dict[str, Any] | None = None,
) -> bool:
    if market == "KR":
        if meta.market_cap is None:
            return True
        return meta.market_cap >= MIN_MARKET_CAP_KR
    if market == "US":
        if info is None:
            return True
        cap = _safe_float(info.get("marketCap"))
        if cap <= 0:
            return True
        return cap >= MIN_MARKET_CAP_US
    return True


def passes_red_flags(info: dict[str, Any]) -> bool:
    """Hard filters for distressed balance sheets (Epic #23).

    Missing book/P/B fields are not treated as negative equity — only explicit
    negative values fail. Dual-negative cash flow requires both fields present.
    """
    book_value = _optional_float(info.get("bookValue"))
    price_to_book = _optional_float(info.get("priceToBook"))
    if book_value is not None and book_value < 0:
        return False
    if price_to_book is not None and price_to_book < 0:
        return False

    free_cashflow = _optional_float(info.get("freeCashflow"))
    operating_cashflow = _optional_float(info.get("operatingCashflow"))
    if (
        free_cashflow is not None
        and operating_cashflow is not None
        and free_cashflow < 0
        and operating_cashflow < 0
    ):
        return False
    return True


def _score_size(meta: UniverseSymbol, info: dict[str, Any], market: str) -> tuple[float, dict[str, Any]]:
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


def _blended_growth_pct(info: dict[str, Any]) -> tuple[float, float, float]:
    rev_growth = _safe_float(info.get("revenueGrowth"))
    earn_growth = _safe_float(info.get("earningsGrowth"))
    rev_q = _safe_float(info.get("quarterlyRevenueGrowthYOY"))
    earn_q = _safe_float(info.get("quarterlyEarningsGrowthYOY"))

    rev_pct = _clip_growth_pct(max(rev_growth, rev_q) * 100 if max(rev_growth, rev_q) else 0)
    earn_pct = _clip_growth_pct(max(earn_growth, earn_q) * 100 if max(earn_growth, earn_q) else 0)
    blended = rev_pct * GROWTH_REV_WEIGHT + earn_pct * GROWTH_EARN_WEIGHT
    return rev_pct, earn_pct, blended


def _score_growth_v1(info: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    rev_pct, earn_pct, blended = _blended_growth_pct(info)
    score = _clamp(GROWTH_BASE_SCORE + blended * GROWTH_SCORE_MULTIPLIER)
    return score, {"revenue_growth_pct": round(rev_pct, 2), "earnings_growth_pct": round(earn_pct, 2)}


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


def _score_valuation_v1(info: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    return _score_pe_peg(info)


def _score_valuation(info: dict[str, Any], meta: UniverseSymbol) -> tuple[float, dict[str, Any]]:
    pe_score, pe_m = _score_pe_peg(info)
    fcf_score, fcf_m = _score_fcf_yield(info, meta)
    pb_score, pb_m = _score_price_to_book(info)
    score = _clamp(
        pe_score * VAL_PE_PEG_WEIGHT
        + fcf_score * VAL_FCF_WEIGHT
        + pb_score * VAL_PB_WEIGHT
    )
    return score, {**pe_m, **fcf_m, **pb_m}


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

    score = _clamp(
        range_score * ENTRY_RANGE_WEIGHT + recovery_score * ENTRY_RECOVERY_WEIGHT
    )
    return score, {
        "twelve_month_range_pct": round(range_pct, 2),
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


def _composite_v1(growth: float, valuation: float, momentum: float, quality: float) -> float:
    return (
        growth * V1_WEIGHT_GROWTH
        + valuation * V1_WEIGHT_VALUATION
        + momentum * V1_WEIGHT_MOMENTUM
        + quality * V1_WEIGHT_QUALITY
    )


def _composite_v2(
    size: float,
    growth: float,
    valuation: float,
    quality: float,
    entry: float,
    momentum: float,
) -> float:
    return (
        size * WEIGHT_SIZE
        + valuation * WEIGHT_VALUATION
        + growth * WEIGHT_GROWTH
        + quality * WEIGHT_QUALITY
        + entry * WEIGHT_ENTRY
        + momentum * WEIGHT_MOMENTUM
    )


def score_symbol(
    meta: UniverseSymbol,
    market: str,
    info: dict[str, Any] | None = None,
    *,
    score_version: int = SCORE_VERSION,
) -> ScoreResult | None:
    if info is None:
        info = get_ticker_info(meta.symbol)
    if not info.get("symbol") and not info.get("shortName"):
        return None
    if not passes_market_cap_filter(meta, market, info):
        return None
    if score_version >= 2 and not passes_red_flags(info):
        return None

    long_name = info.get("longName") or info.get("shortName")
    if long_name:
        meta = UniverseSymbol(
            symbol=meta.symbol,
            name_ko=meta.name_ko,
            name_en=str(long_name),
            exchange=meta.exchange,
            currency=meta.currency,
            market_cap=meta.market_cap,
        )

    hist = get_ticker_history(meta.symbol)

    if score_version < 2:
        growth, g_m = _score_growth_v1(info)
        valuation, v_m = _score_valuation_v1(info)
        momentum, m_m = _score_momentum_v1(hist)
        quality, q_m = _score_quality_v1(info)
        size, s_m, entry, e_m = 0.0, {}, 0.0, {}
        composite = _composite_v1(growth, valuation, momentum, quality)
        version = 1
    else:
        size, s_m = _score_size(meta, info, market)
        growth, g_m = _score_growth(info)
        valuation, v_m = _score_valuation(info, meta)
        entry, e_m = _score_entry(hist)
        momentum, m_m = _score_momentum(hist)
        quality, q_m = _score_quality(info)
        composite = _composite_v2(size, growth, valuation, quality, entry, momentum)
        version = 2

    return ScoreResult(
        symbol=meta.symbol,
        meta=meta,
        size=round(size, 1),
        growth=round(growth, 1),
        valuation=round(valuation, 1),
        entry=round(entry, 1),
        momentum=round(momentum, 1),
        quality=round(quality, 1),
        composite=round(composite, 1),
        metrics={**s_m, **g_m, **v_m, **e_m, **m_m, **q_m},
        score_version=version,
    )


def screen_market(
    market: str,
    exclude_symbols: set[str],
    *,
    score_version: int = SCORE_VERSION,
) -> tuple[list[ScoreResult], ScreenStats]:
    universe = load_universe(market)
    stats = ScreenStats(skipped_recent=len(exclude_symbols))

    to_screen: list[UniverseSymbol] = []
    for meta in universe:
        if meta.symbol in exclude_symbols:
            continue
        if not passes_market_cap_filter(meta, market):
            stats.skipped_market_cap += 1
            continue
        to_screen.append(meta)

    stats.screened = len(to_screen)
    results: list[ScoreResult] = []

    def _score_one(meta: UniverseSymbol) -> tuple[str, ScoreResult | None]:
        info = get_ticker_info(meta.symbol)
        if not info.get("symbol") and not info.get("shortName"):
            return ("no_data", None)
        if not passes_market_cap_filter(meta, market, info):
            return ("skip_mcap", None)
        if score_version >= 2 and not passes_red_flags(info):
            return ("skip_red", None)
        return ("ok", score_symbol(meta, market, info, score_version=score_version))

    workers = min(SCREEN_WORKERS, max(1, stats.screened))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_score_one, meta): meta for meta in to_screen}
        for future in as_completed(futures):
            meta = futures[future]
            try:
                status, scored = future.result()
            except Exception as exc:
                stats.errors += 1
                if len(stats.error_samples) < 5:
                    stats.error_samples.append(f"{meta.symbol}: {exc}")
                logger.warning("Screen error for %s: %s", meta.symbol, exc)
                continue

            if status == "skip_mcap":
                stats.skipped_market_cap += 1
                continue
            if status == "skip_red":
                stats.skipped_red_flags += 1
                continue
            if status == "no_data" or scored is None:
                stats.no_data += 1
                continue
            if scored.composite >= COMPOSITE_THRESHOLD:
                results.append(scored)
                stats.passed_threshold += 1

    results.sort(key=lambda r: r.composite, reverse=True)
    logger.info(
        "Screen %s v%d: screened=%d passed=%d no_data=%d errors=%d skipped_mcap=%d skipped_red=%d",
        market,
        score_version,
        stats.screened,
        stats.passed_threshold,
        stats.no_data,
        stats.errors,
        stats.skipped_market_cap,
        stats.skipped_red_flags,
    )
    if stats.error_samples:
        logger.warning("Sample errors: %s", "; ".join(stats.error_samples))

    return results, stats


def build_reasoning(result: ScoreResult) -> dict[str, Any]:
    m = result.metrics
    rev = m.get("revenue_growth_pct")
    earn = m.get("earnings_growth_pct")
    blended = m.get("blended_growth_pct")
    pe = m.get("pe")
    peg = m.get("peg")
    fcf_yield = m.get("fcf_yield_pct")
    pb = m.get("price_to_book")
    mcap = m.get("market_cap")
    range_pct = m.get("twelve_month_range_pct")
    ret6 = m.get("six_month_return_pct")
    from_high = m.get("from_52w_high_pct")
    roe = m.get("roe_pct")
    roa = m.get("roa_pct")
    fcf_ni = m.get("fcf_to_net_income")

    if result.score_version >= 2:
        summary_ko = (
            f"{result.meta.name_ko}({result.symbol})는 v2 복합 점수 {result.composite}로 "
            f"임계 {COMPOSITE_THRESHOLD}를 상회했습니다. 소형·가치·현금·진입 타이밍이 균형을 이룹니다."
        )
        summary_en = (
            f"{result.meta.name_en} ({result.symbol}) cleared the {COMPOSITE_THRESHOLD} "
            f"threshold with v2 composite {result.composite}; size, value, cash, and entry align."
        )
        growth_ko = (
            f"매출 {rev}% / 이익 {earn}% (혼합 {blended}%) — 지속 가능 성장 점수 {result.growth}."
        )
        growth_en = (
            f"Revenue {rev}% / earnings {earn}% (blended {blended}%) — "
            f"sustainable growth score {result.growth}."
        )
        valuation_ko = (
            f"PER {pe}, PEG {peg}, FCF수익률 {fcf_yield}%, PBR {pb} — 밸류 점수 {result.valuation}."
        )
        valuation_en = (
            f"P/E {pe}, PEG {peg}, FCF yield {fcf_yield}%, P/B {pb} — "
            f"valuation score {result.valuation}."
        )
        size_ko = f"시가총액 {mcap} 기준 규모 점수 {result.size}."
        size_en = f"Market cap {mcap} — size score {result.size}."
        entry_ko = (
            f"12개월 가격대 {range_pct}%, 52주 고점 대비 {from_high}% — 진입 점수 {result.entry}."
        )
        entry_en = (
            f"12M price range {range_pct}%, {from_high}% from 52W high — entry score {result.entry}."
        )
        momentum_ko = f"6개월 수익률 {ret6}% — 보조 모멘텀 점수 {result.momentum}."
        momentum_en = f"6M return {ret6}% — auxiliary momentum score {result.momentum}."
        quality_ko = (
            f"ROE {roe}%, ROA {roa}%, FCF/순이익 {fcf_ni} — 품질 점수 {result.quality}."
        )
        quality_en = (
            f"ROE {roe}%, ROA {roa}%, FCF/net income {fcf_ni} — quality score {result.quality}."
        )
    else:
        summary_ko = (
            f"{result.meta.name_ko}({result.symbol})는 복합 점수 {result.composite}로 "
            f"임계 {COMPOSITE_THRESHOLD}를 상회했습니다."
        )
        summary_en = (
            f"{result.meta.name_en} ({result.symbol}) cleared the {COMPOSITE_THRESHOLD} "
            f"threshold with composite score {result.composite}."
        )
        growth_ko = f"매출 성장 {rev}% / 이익 성장 {earn}% — 성장 점수 {result.growth}."
        growth_en = f"Revenue growth {rev}% and earnings growth {earn}% — growth score {result.growth}."
        valuation_ko = f"PER {pe}, PEG {peg} — 밸류 점수 {result.valuation}."
        valuation_en = f"P/E {pe}, PEG {peg} — valuation score {result.valuation}."
        size_ko = ""
        size_en = ""
        entry_ko = f"6개월 수익률 {ret6}%, 52주 고점 대비 {from_high}% — 모멘텀 점수 {result.momentum}."
        entry_en = f"6M return {ret6}%, {from_high}% from 52W high — momentum score {result.momentum}."
        momentum_ko = entry_ko
        momentum_en = entry_en
        quality_ko = f"ROE {roe}% — 품질 점수 {result.quality}."
        quality_en = f"ROE {roe}% — quality score {result.quality}."

    reasoning: dict[str, Any] = {
        "summary": {"ko": summary_ko, "en": summary_en},
        "growth": {"ko": growth_ko, "en": growth_en},
        "valuation": {"ko": valuation_ko, "en": valuation_en},
        "momentum": {"ko": momentum_ko, "en": momentum_en},
        "quality": {"ko": quality_ko, "en": quality_en},
        "risks": [
            {
                "ko": "실적 가이던스 하향 시 성장 프리미엄 축소 가능",
                "en": "Growth premium may compress on guidance cuts",
            },
            {
                "ko": "글로벌 금리·유동성 변화에 따른 밸류에이션 리레이팅",
                "en": "Valuation re-rating risk from rates and liquidity",
            },
            {
                "ko": "5년 10배는 목표 시나리오이며 달성을 보장하지 않음",
                "en": "10x in five years is a scenario, not a guarantee",
            },
        ],
    }
    if result.score_version >= 2:
        reasoning["size"] = {"ko": size_ko, "en": size_en}
        reasoning["entry"] = {"ko": entry_ko, "en": entry_en}
    return reasoning
