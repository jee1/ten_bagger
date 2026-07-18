"""Human-readable (KO/EN) reasoning text for a ScoreResult."""

from __future__ import annotations

from typing import Any

from config import COMPOSITE_THRESHOLD
from scoring.models import ScoreResult


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
            f"임계 {COMPOSITE_THRESHOLD}를 상회했습니다. "
            "소형·가치·현금·진입 타이밍이 균형을 이룹니다."
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
            f"12M price range {range_pct}%, {from_high}% from 52W high — "
            f"entry score {result.entry}."
        )
        momentum_ko = f"6개월 수익률 {ret6}% — 보조 모멘텀 점수 {result.momentum}."
        momentum_en = f"6M return {ret6}% — auxiliary momentum score {result.momentum}."
        quality_ko = f"ROE {roe}%, ROA {roa}%, FCF/순이익 {fcf_ni} — 품질 점수 {result.quality}."
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
        growth_en = (
            f"Revenue growth {rev}% and earnings growth {earn}% — growth score {result.growth}."
        )
        valuation_ko = f"PER {pe}, PEG {peg} — 밸류 점수 {result.valuation}."
        valuation_en = f"P/E {pe}, PEG {peg} — valuation score {result.valuation}."
        size_ko = ""
        size_en = ""
        entry_ko = (
            f"6개월 수익률 {ret6}%, 52주 고점 대비 {from_high}% — 모멘텀 점수 {result.momentum}."
        )
        entry_en = (
            f"6M return {ret6}%, {from_high}% from 52W high — momentum score {result.momentum}."
        )
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
