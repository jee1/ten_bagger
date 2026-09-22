"""Human-readable (KO/EN) reasoning text for a ScoreResult."""

from __future__ import annotations

import math
import re
from typing import Any

from config import COMPOSITE_THRESHOLD, ENTRY_DEFAULT_SCORE, MOMENTUM_DEFAULT_SCORE
from scoring.models import ScoreResult

MISSING_LABEL = {"ko": "데이터 없음", "en": "No data"}
_FORBIDDEN_RENDER_TOKENS = re.compile(r"\b(nan|NaN|Infinity)\b|None")

STATIC_RISKS: list[dict[str, str]] = [
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
]


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return True
    return False


def _fmt_metric(value: Any, lang: str, *, pct: bool = False) -> str:
    if _is_missing(value):
        return MISSING_LABEL[lang]
    text = str(value)
    return f"{text}%" if pct else text


def _price_factor_note(
    metrics: dict[str, Any],
    metric_keys: list[str],
    score: float,
    default_score: float,
    lang: str,
    *,
    factor_ko: str,
    factor_en: str,
) -> str:
    missing = [_is_missing(metrics.get(key)) for key in metric_keys]
    if all(missing) and score == default_score:
        if lang == "ko":
            return (
                f" (가격 이력 부족: 기본 {factor_ko} 점수 {default_score} 적용; "
                f"해당 점수는 복합에 포함되며 선정은 복합 임계 {COMPOSITE_THRESHOLD} 기준)"
            )
        return (
            f" (insufficient price history: default {factor_en} score {default_score}; "
            f"score still enters composite; selection uses composite threshold "
            f"{COMPOSITE_THRESHOLD})"
        )
    if any(missing):
        if lang == "ko":
            return (
                f" (일부 가격 입력 없음; {factor_ko} 점수 {score}는 가용 데이터로 계산; "
                f"복합에 포함, 선정은 복합 임계 {COMPOSITE_THRESHOLD} 기준)"
            )
        return (
            f" (some price inputs missing; {factor_en} score {score} from available data; "
            f"still enters composite; selection uses composite threshold {COMPOSITE_THRESHOLD})"
        )
    return ""


def reasoning_has_forbidden_tokens(reasoning: dict[str, Any]) -> bool:
    """True when any reasoning string would expose nan/NaN/Infinity/None to readers."""
    for section in reasoning.values():
        if isinstance(section, dict) and "ko" in section and "en" in section:
            for lang in ("ko", "en"):
                if _FORBIDDEN_RENDER_TOKENS.search(str(section[lang])):
                    return True
            continue
        if isinstance(section, list):
            for item in section:
                if isinstance(item, dict):
                    for lang in ("ko", "en"):
                        if lang in item and _FORBIDDEN_RENDER_TOKENS.search(str(item[lang])):
                            return True
    return False


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
            f"매출 {_fmt_metric(rev, 'ko', pct=True)} / 이익 {_fmt_metric(earn, 'ko', pct=True)} "
            f"(혼합 {_fmt_metric(blended, 'ko', pct=True)}) — 지속 가능 성장 점수 {result.growth}."
        )
        growth_en = (
            f"Revenue {_fmt_metric(rev, 'en', pct=True)} / "
            f"earnings {_fmt_metric(earn, 'en', pct=True)} "
            f"(blended {_fmt_metric(blended, 'en', pct=True)}) — "
            f"sustainable growth score {result.growth}."
        )
        valuation_ko = (
            f"PER {_fmt_metric(pe, 'ko')}, PEG {_fmt_metric(peg, 'ko')}, "
            f"FCF수익률 {_fmt_metric(fcf_yield, 'ko', pct=True)}, PBR {_fmt_metric(pb, 'ko')} — "
            f"밸류 점수 {result.valuation}."
        )
        valuation_en = (
            f"P/E {_fmt_metric(pe, 'en')}, PEG {_fmt_metric(peg, 'en')}, "
            f"FCF yield {_fmt_metric(fcf_yield, 'en', pct=True)}, P/B {_fmt_metric(pb, 'en')} — "
            f"valuation score {result.valuation}."
        )
        size_ko = f"시가총액 {_fmt_metric(mcap, 'ko')} 기준 규모 점수 {result.size}."
        size_en = f"Market cap {_fmt_metric(mcap, 'en')} — size score {result.size}."
        entry_note_ko = _price_factor_note(
            m,
            ["twelve_month_range_pct", "from_52w_high_pct"],
            result.entry,
            ENTRY_DEFAULT_SCORE,
            "ko",
            factor_ko="진입",
            factor_en="entry",
        )
        entry_note_en = _price_factor_note(
            m,
            ["twelve_month_range_pct", "from_52w_high_pct"],
            result.entry,
            ENTRY_DEFAULT_SCORE,
            "en",
            factor_ko="진입",
            factor_en="entry",
        )
        entry_ko = (
            f"12개월 가격대 {_fmt_metric(range_pct, 'ko', pct=True)}, "
            f"52주 고점 대비 {_fmt_metric(from_high, 'ko', pct=True)} — "
            f"진입 점수 {result.entry}.{entry_note_ko}"
        )
        entry_en = (
            f"12M price range {_fmt_metric(range_pct, 'en', pct=True)}, "
            f"{_fmt_metric(from_high, 'en', pct=True)} from 52W high — "
            f"entry score {result.entry}.{entry_note_en}"
        )
        momentum_note_ko = _price_factor_note(
            m,
            ["six_month_return_pct"],
            result.momentum,
            MOMENTUM_DEFAULT_SCORE,
            "ko",
            factor_ko="모멘텀",
            factor_en="momentum",
        )
        momentum_note_en = _price_factor_note(
            m,
            ["six_month_return_pct"],
            result.momentum,
            MOMENTUM_DEFAULT_SCORE,
            "en",
            factor_ko="모멘텀",
            factor_en="momentum",
        )
        momentum_ko = (
            f"6개월 수익률 {_fmt_metric(ret6, 'ko', pct=True)} — "
            f"보조 모멘텀 점수 {result.momentum}.{momentum_note_ko}"
        )
        momentum_en = (
            f"6M return {_fmt_metric(ret6, 'en', pct=True)} — "
            f"auxiliary momentum score {result.momentum}.{momentum_note_en}"
        )
        quality_ko = (
            f"ROE {_fmt_metric(roe, 'ko', pct=True)}, ROA {_fmt_metric(roa, 'ko', pct=True)}, "
            f"FCF/순이익 {_fmt_metric(fcf_ni, 'ko')} — 품질 점수 {result.quality}."
        )
        quality_en = (
            f"ROE {_fmt_metric(roe, 'en', pct=True)}, ROA {_fmt_metric(roa, 'en', pct=True)}, "
            f"FCF/net income {_fmt_metric(fcf_ni, 'en')} — quality score {result.quality}."
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
        growth_ko = (
            f"매출 성장 {_fmt_metric(rev, 'ko', pct=True)} / "
            f"이익 성장 {_fmt_metric(earn, 'ko', pct=True)} — 성장 점수 {result.growth}."
        )
        growth_en = (
            f"Revenue growth {_fmt_metric(rev, 'en', pct=True)} and "
            f"earnings growth {_fmt_metric(earn, 'en', pct=True)} — growth score {result.growth}."
        )
        valuation_ko = (
            f"PER {_fmt_metric(pe, 'ko')}, PEG {_fmt_metric(peg, 'ko')} — "
            f"밸류 점수 {result.valuation}."
        )
        valuation_en = (
            f"P/E {_fmt_metric(pe, 'en')}, PEG {_fmt_metric(peg, 'en')} — "
            f"valuation score {result.valuation}."
        )
        size_ko = ""
        size_en = ""
        v1_momentum_note_ko = _price_factor_note(
            m,
            ["six_month_return_pct", "from_52w_high_pct"],
            result.momentum,
            MOMENTUM_DEFAULT_SCORE,
            "ko",
            factor_ko="모멘텀",
            factor_en="momentum",
        )
        v1_momentum_note_en = _price_factor_note(
            m,
            ["six_month_return_pct", "from_52w_high_pct"],
            result.momentum,
            MOMENTUM_DEFAULT_SCORE,
            "en",
            factor_ko="모멘텀",
            factor_en="momentum",
        )
        entry_ko = (
            f"6개월 수익률 {_fmt_metric(ret6, 'ko', pct=True)}, "
            f"52주 고점 대비 {_fmt_metric(from_high, 'ko', pct=True)} — "
            f"모멘텀 점수 {result.momentum}.{v1_momentum_note_ko}"
        )
        entry_en = (
            f"6M return {_fmt_metric(ret6, 'en', pct=True)}, "
            f"{_fmt_metric(from_high, 'en', pct=True)} from 52W high — "
            f"momentum score {result.momentum}.{v1_momentum_note_en}"
        )
        momentum_ko = entry_ko
        momentum_en = entry_en
        quality_ko = f"ROE {_fmt_metric(roe, 'ko', pct=True)} — 품질 점수 {result.quality}."
        quality_en = f"ROE {_fmt_metric(roe, 'en', pct=True)} — quality score {result.quality}."

    reasoning: dict[str, Any] = {
        "summary": {"ko": summary_ko, "en": summary_en},
        "growth": {"ko": growth_ko, "en": growth_en},
        "valuation": {"ko": valuation_ko, "en": valuation_en},
        "momentum": {"ko": momentum_ko, "en": momentum_en},
        "quality": {"ko": quality_ko, "en": quality_en},
        "risks": list(STATIC_RISKS),
    }
    if result.score_version >= 2:
        reasoning["size"] = {"ko": size_ko, "en": size_en}
        reasoning["entry"] = {"ko": entry_ko, "en": entry_en}

    # Candidate-path soft label only — live picks never set this while flag is OFF.
    labels = m.get("red_flag_labels") or []
    if "investment_dummy" in labels:
        reasoning["risks"].append(
            {
                "ko": "자산 성장이 EBITDA 성장을 상회(investment_dummy) — 투자 효율 저하 리스크",
                "en": (
                    "Asset growth exceeds EBITDA growth (investment_dummy) "
                    "— investment-efficiency risk"
                ),
            }
        )
    assert not reasoning_has_forbidden_tokens(reasoning), (
        "reasoning must not expose nan/NaN/Infinity/None"
    )
    return reasoning
