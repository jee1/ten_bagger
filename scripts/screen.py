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
    COMPOSITE_THRESHOLD,
    GROWTH_BASE_SCORE,
    GROWTH_EARN_WEIGHT,
    GROWTH_REV_WEIGHT,
    GROWTH_SCORE_MULTIPLIER,
    MAX_GROWTH_PCT,
    MIN_MARKET_CAP_KR,
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
    MOMENTUM_RET_MULTIPLIER,
    MOMENTUM_RET_WEIGHT,
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
    QUALITY_DEBT_FAIR,
    QUALITY_DEBT_GOOD,
    QUALITY_DEBT_EXCELLENT,
    QUALITY_DEBT_SCORE_EXCELLENT,
    QUALITY_DEBT_SCORE_FAIR,
    QUALITY_DEBT_SCORE_GOOD,
    QUALITY_DEBT_SCORE_POOR,
    QUALITY_DEBT_WEIGHT,
    QUALITY_MARGIN_BASE,
    QUALITY_MARGIN_MULTIPLIER,
    QUALITY_MARGIN_WEIGHT,
    QUALITY_ROE_DEFAULT,
    QUALITY_ROE_MULTIPLIER,
    QUALITY_ROE_WEIGHT,
    SCREEN_WORKERS,
    UNIVERSE_DIR,
    WEIGHT_GROWTH,
    WEIGHT_MOMENTUM,
    WEIGHT_QUALITY,
    WEIGHT_VALUATION,
    UniverseSymbol,
)
from yf_cache import get_ticker_history, get_ticker_info

logger = logging.getLogger(__name__)


@dataclass
class ScoreResult:
    symbol: str
    meta: UniverseSymbol
    growth: float
    valuation: float
    momentum: float
    quality: float
    composite: float
    metrics: dict[str, Any]


@dataclass
class ScreenStats:
    screened: int = 0
    passed_threshold: int = 0
    skipped_recent: int = 0
    skipped_market_cap: int = 0
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


def passes_market_cap_filter(meta: UniverseSymbol, market: str) -> bool:
    if market != "KR":
        return True
    if meta.market_cap is None:
        return True
    return meta.market_cap >= MIN_MARKET_CAP_KR


def _score_growth(info: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    rev_growth = _safe_float(info.get("revenueGrowth"))
    earn_growth = _safe_float(info.get("earningsGrowth"))
    rev_q = _safe_float(info.get("quarterlyRevenueGrowthYOY"))
    earn_q = _safe_float(info.get("quarterlyEarningsGrowthYOY"))

    rev_pct = _clip_growth_pct(max(rev_growth, rev_q) * 100 if max(rev_growth, rev_q) else 0)
    earn_pct = _clip_growth_pct(max(earn_growth, earn_q) * 100 if max(earn_growth, earn_q) else 0)
    blended = rev_pct * GROWTH_REV_WEIGHT + earn_pct * GROWTH_EARN_WEIGHT

    score = _clamp(GROWTH_BASE_SCORE + blended * GROWTH_SCORE_MULTIPLIER)
    return score, {"revenue_growth_pct": round(rev_pct, 2), "earnings_growth_pct": round(earn_pct, 2)}


def _score_valuation(info: dict[str, Any]) -> tuple[float, dict[str, Any]]:
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
    return score, {"pe": round(pe_ref, 2) if pe_ref else None, "peg": round(peg, 2) if peg else None}


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


def _score_quality(info: dict[str, Any]) -> tuple[float, dict[str, Any]]:
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
        roe_score * QUALITY_ROE_WEIGHT
        + debt_score * QUALITY_DEBT_WEIGHT
        + margin_score * QUALITY_MARGIN_WEIGHT
    )
    return score, {
        "roe_pct": round(roe_pct, 2),
        "debt_to_equity": round(debt, 2) if debt else None,
        "operating_margin_pct": round(margin_pct, 2),
    }


def score_symbol(meta: UniverseSymbol) -> ScoreResult | None:
    info = get_ticker_info(meta.symbol)
    if not info.get("symbol") and not info.get("shortName"):
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

    growth, g_m = _score_growth(info)
    valuation, v_m = _score_valuation(info)
    hist = get_ticker_history(meta.symbol)
    momentum, m_m = _score_momentum(hist)
    quality, q_m = _score_quality(info)

    composite = (
        growth * WEIGHT_GROWTH
        + valuation * WEIGHT_VALUATION
        + momentum * WEIGHT_MOMENTUM
        + quality * WEIGHT_QUALITY
    )

    return ScoreResult(
        symbol=meta.symbol,
        meta=meta,
        growth=round(growth, 1),
        valuation=round(valuation, 1),
        momentum=round(momentum, 1),
        quality=round(quality, 1),
        composite=round(composite, 1),
        metrics={**g_m, **v_m, **m_m, **q_m},
    )


def screen_market(market: str, exclude_symbols: set[str]) -> tuple[list[ScoreResult], ScreenStats]:
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

    def _score_one(meta: UniverseSymbol) -> ScoreResult | None:
        return score_symbol(meta)

    workers = min(SCREEN_WORKERS, max(1, stats.screened))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_score_one, meta): meta for meta in to_screen}
        for future in as_completed(futures):
            meta = futures[future]
            try:
                scored = future.result()
            except Exception as exc:
                stats.errors += 1
                if len(stats.error_samples) < 5:
                    stats.error_samples.append(f"{meta.symbol}: {exc}")
                logger.warning("Screen error for %s: %s", meta.symbol, exc)
                continue

            if scored is None:
                stats.no_data += 1
                continue
            if scored.composite >= COMPOSITE_THRESHOLD:
                results.append(scored)
                stats.passed_threshold += 1

    results.sort(key=lambda r: r.composite, reverse=True)
    logger.info(
        "Screen %s: screened=%d passed=%d no_data=%d errors=%d skipped_mcap=%d",
        market,
        stats.screened,
        stats.passed_threshold,
        stats.no_data,
        stats.errors,
        stats.skipped_market_cap,
    )
    if stats.error_samples:
        logger.warning("Sample errors: %s", "; ".join(stats.error_samples))

    return results, stats


def build_reasoning(result: ScoreResult) -> dict[str, Any]:
    m = result.metrics
    rev = m.get("revenue_growth_pct")
    earn = m.get("earnings_growth_pct")
    pe = m.get("pe")
    peg = m.get("peg")
    ret6 = m.get("six_month_return_pct")
    from_high = m.get("from_52w_high_pct")
    roe = m.get("roe_pct")

    return {
        "summary": {
            "ko": (
                f"{result.meta.name_ko}({result.symbol})는 복합 점수 {result.composite}로 "
                f"임계 {COMPOSITE_THRESHOLD}를 상회했습니다. 성장·밸류·모멘텀 균형이 양호합니다."
            ),
            "en": (
                f"{result.meta.name_en} ({result.symbol}) cleared the {COMPOSITE_THRESHOLD} "
                f"threshold with composite score {result.composite}; growth, valuation, and momentum align."
            ),
        },
        "growth": {
            "ko": f"매출 성장 {rev}% / 이익 성장 {earn}% 수준으로 성장 점수 {result.growth}입니다.",
            "en": f"Revenue growth {rev}% and earnings growth {earn}% yield growth score {result.growth}.",
        },
        "valuation": {
            "ko": f"PER {pe}, PEG {peg} 기준 밸류 점수 {result.valuation}입니다.",
            "en": f"At P/E {pe} and PEG {peg}, valuation score is {result.valuation}.",
        },
        "momentum": {
            "ko": f"6개월 수익률 {ret6}%, 52주 고점 대비 {from_high}% — 모멘텀 점수 {result.momentum}.",
            "en": f"6M return {ret6}%, {from_high}% from 52W high — momentum score {result.momentum}.",
        },
        "quality": {
            "ko": f"ROE {roe}%, 영업이익률 기준 품질 점수 {result.quality}입니다.",
            "en": f"ROE {roe}%, operating margin basis — quality score {result.quality}.",
        },
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
