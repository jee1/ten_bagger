"""Rule-based ten-bagger screening engine."""

from __future__ import annotations

import json
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yfinance as yf

from config import (
    COMPOSITE_THRESHOLD,
    SCREEN_WORKERS,
    UNIVERSE_DIR,
    WEIGHT_GROWTH,
    WEIGHT_MOMENTUM,
    WEIGHT_QUALITY,
    WEIGHT_VALUATION,
    UniverseSymbol,
)


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


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


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


def _score_growth(info: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    rev_growth = _safe_float(info.get("revenueGrowth"))
    earn_growth = _safe_float(info.get("earningsGrowth"))
    rev_q = _safe_float(info.get("quarterlyRevenueGrowthYOY"))
    earn_q = _safe_float(info.get("quarterlyEarningsGrowthYOY"))

    rev_pct = max(rev_growth, rev_q) * 100 if max(rev_growth, rev_q) else 0
    earn_pct = max(earn_growth, earn_q) * 100 if max(earn_growth, earn_q) else 0
    blended = rev_pct * 0.55 + earn_pct * 0.45

    # 0% -> 20, 15% -> 55, 30%+ -> 90+
    score = _clamp(20 + blended * 2.2)
    return score, {"revenue_growth_pct": round(rev_pct, 2), "earnings_growth_pct": round(earn_pct, 2)}


def _score_valuation(info: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    pe = _safe_float(info.get("trailingPE"))
    peg = _safe_float(info.get("pegRatio"))
    fwd_pe = _safe_float(info.get("forwardPE"))

    pe_ref = pe if pe > 0 else fwd_pe
    pe_score = 50.0
    if pe_ref > 0:
        if pe_ref <= 12:
            pe_score = 85
        elif pe_ref <= 20:
            pe_score = 70
        elif pe_ref <= 35:
            pe_score = 50
        else:
            pe_score = 30

    peg_score = 50.0
    if peg > 0:
        if peg <= 0.8:
            peg_score = 90
        elif peg <= 1.2:
            peg_score = 75
        elif peg <= 2.0:
            peg_score = 55
        else:
            peg_score = 35

    score = _clamp(pe_score * 0.55 + peg_score * 0.45)
    return score, {"pe": round(pe_ref, 2) if pe_ref else None, "peg": round(peg, 2) if peg else None}


def _score_momentum(ticker: yf.Ticker) -> tuple[float, dict[str, Any]]:
    hist = ticker.history(period="1y")
    if hist.empty or len(hist) < 30:
        return 40.0, {"six_month_return_pct": None, "from_52w_high_pct": None}

    close = hist["Close"]
    latest = float(close.iloc[-1])
    six_month = float(close.iloc[-min(126, len(close))])
    high_52w = float(close.max())

    ret_6m = (latest / six_month - 1) * 100 if six_month else 0
    from_high = (latest / high_52w - 1) * 100 if high_52w else 0

    ret_score = _clamp(35 + ret_6m * 1.5)
    # Prefer recovery zone (-25% to -5% from high) or strong uptrend
    if -25 <= from_high <= -5:
        high_score = 75
    elif from_high > -5:
        high_score = 65
    else:
        high_score = 45

    score = _clamp(ret_score * 0.6 + high_score * 0.4)
    return score, {
        "six_month_return_pct": round(ret_6m, 2),
        "from_52w_high_pct": round(from_high, 2),
    }


def _score_quality(info: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    roe = _safe_float(info.get("returnOnEquity"))
    debt = _safe_float(info.get("debtToEquity"))
    margin = _safe_float(info.get("operatingMargins"))

    roe_pct = roe * 100 if abs(roe) < 5 else roe
    roe_score = _clamp(roe_pct * 2.5) if roe_pct > 0 else 30

    debt_score = 70.0
    if debt > 0:
        if debt < 50:
            debt_score = 85
        elif debt < 100:
            debt_score = 70
        elif debt < 200:
            debt_score = 50
        else:
            debt_score = 30

    margin_pct = margin * 100 if abs(margin) < 2 else margin
    margin_score = _clamp(30 + margin_pct * 2)

    score = _clamp(roe_score * 0.45 + debt_score * 0.25 + margin_score * 0.30)
    return score, {
        "roe_pct": round(roe_pct, 2),
        "debt_to_equity": round(debt, 2) if debt else None,
        "operating_margin_pct": round(margin_pct, 2),
    }


def score_symbol(meta: UniverseSymbol) -> ScoreResult | None:
    ticker = yf.Ticker(meta.symbol)
    info = ticker.info or {}
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
    momentum, m_m = _score_momentum(ticker)
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


def screen_market(market: str, exclude_symbols: set[str]) -> tuple[list[ScoreResult], int]:
    universe = load_universe(market)
    to_screen = [meta for meta in universe if meta.symbol not in exclude_symbols]
    screened = len(to_screen)
    results: list[ScoreResult] = []

    def _score_one(meta: UniverseSymbol) -> ScoreResult | None:
        try:
            return score_symbol(meta)
        except Exception:
            return None

    workers = min(SCREEN_WORKERS, max(1, screened))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_score_one, meta) for meta in to_screen]
        for future in as_completed(futures):
            scored = future.result()
            if scored and scored.composite >= COMPOSITE_THRESHOLD:
                results.append(scored)

    results.sort(key=lambda r: r.composite, reverse=True)
    return results, screened


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
