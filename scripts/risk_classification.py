"""Closed-category business risk tagging for Top-N candidates (Issue #147).

Observational only — does not affect Score v2, ranks, threshold, or pick selection.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from yf_cache import get_ticker_info

logger = logging.getLogger(__name__)

TYPESAFE_LOGGER_NAME = "typesafe_sdk"


def cap_sdk_logger() -> logging.Logger:
    """Set the TypeSafe SDK logger to WARNING so request/response bodies are never emitted."""
    sdk_logger = logging.getLogger(TYPESAFE_LOGGER_NAME)
    sdk_logger.setLevel(logging.WARNING)
    return sdk_logger


cap_sdk_logger()

JEV_RISK_MODEL = "jev-1.13.0"
TYPESAFE_API_KEY_ENV = "TYPESAFE_API_KEY"
CLASSIFY_TIMEOUT_SECONDS = 30.0

RISK_TAG_CHOICES: dict[str, dict[str, str | None]] = {
    "customer_concentration": {
        "ko": "주요 고객·매출 편중 리스크",
        "en": "Customer or revenue concentration risk",
        "criteria": "Revenue or profits depend heavily on a few customers or one channel",
    },
    "regulation": {
        "ko": "규제·컴플라이언스 변화 리스크",
        "en": "Regulatory and compliance change risk",
        "criteria": "Heavily regulated industry or licensing/policy changes are material",
    },
    "single_product_pipeline": {
        "ko": "단일 제품·파이프라인 의존 리스크",
        "en": "Single-product or pipeline dependency risk",
        "criteria": "Business depends on one product, drug, or narrow pipeline",
    },
    "technology_obsolescence": {
        "ko": "기술 진부화·대체 기술 리스크",
        "en": "Technology obsolescence or displacement risk",
        "criteria": "Core technology may become obsolete or be displaced",
    },
    "commodities_fx": {
        "ko": "원자재 가격·환율 변동 리스크",
        "en": "Commodity price and FX volatility risk",
        "criteria": "Margins sensitive to commodity prices or foreign exchange",
    },
    "debt_liquidity": {
        "ko": "부채·유동성 부담 리스크",
        "en": "Debt burden and liquidity risk",
        "criteria": "Leverage, refinancing, or liquidity constraints are salient",
    },
    "holding_complexity": {
        "ko": "지주사·복잡 지배구조 리스크",
        "en": "Holding-company or complex structure risk",
        "criteria": "Holding-company or convoluted corporate structure adds risk",
    },
    "insufficient_evidence": {
        "ko": "사업 요약만으로는 특정 리스크 분류 근거 부족",
        "en": "Insufficient evidence in the business summary for a specific risk tag",
        "criteria": "Summary lacks clear evidence for any specific category above",
    },
}

RISK_TAGS = frozenset(RISK_TAG_CHOICES)


def risk_text_for_tag(tag: str) -> dict[str, str] | None:
    row = RISK_TAG_CHOICES.get(tag)
    if not row:
        return None
    return {"ko": str(row["ko"]), "en": str(row["en"])}


def _sdk_version() -> str:
    import typesafe_sdk

    cap_sdk_logger()
    return typesafe_sdk.__version__


def _fallback_record(
    *,
    input_at: str,
    reason: str,
    tag: str | None = None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "model": JEV_RISK_MODEL,
        "sdkVersion": _sdk_version(),
        "inputAt": input_at,
        "fallback": True,
        "fallbackReason": reason,
    }
    if tag:
        record["tag"] = tag
    return record


def _success_record(*, input_at: str, tag: str) -> dict[str, Any]:
    return {
        "model": JEV_RISK_MODEL,
        "sdkVersion": _sdk_version(),
        "inputAt": input_at,
        "tag": tag,
        "fallback": False,
    }


def _attach_classification(
    candidate: dict[str, Any],
    *,
    tag: str | None,
    classification: dict[str, Any],
) -> dict[str, Any]:
    out = dict(candidate)
    out["riskClassification"] = classification
    if tag and not classification.get("fallback"):
        out["riskTag"] = tag
        text = risk_text_for_tag(tag)
        if text:
            out["riskText"] = text
    return out


def _classify_summary(summary: str, *, input_at: str) -> tuple[str | None, dict[str, Any]]:
    from typesafe_sdk import (
        Choice,
        TypeSafeClient,
        TypeSafeError,
    )

    cap_sdk_logger()

    criteria = {key: row["criteria"] for key, row in RISK_TAG_CHOICES.items() if row["criteria"]}
    question = Choice(
        instructions=(
            "From the company's long business summary, pick the single most salient "
            "company-specific business risk category."
        ),
        criteria=criteria,
    )

    try:
        with TypeSafeClient(model=JEV_RISK_MODEL) as client:
            response = client.system_one(
                summary,
                {"business_risk": question},
                model=JEV_RISK_MODEL,
                timeout=CLASSIFY_TIMEOUT_SECONDS,
            )
    except TypeSafeError as exc:
        logger.warning("Risk classification API failure: %s", type(exc).__name__)
        return None, _fallback_record(input_at=input_at, reason=type(exc).__name__)
    except Exception as exc:
        logger.warning("Risk classification unexpected failure: %s", type(exc).__name__)
        return None, _fallback_record(input_at=input_at, reason=type(exc).__name__)

    answer = response.answers.get("business_risk")
    if answer is None:
        return None, _fallback_record(input_at=input_at, reason="missing_answer")

    tag = getattr(answer, "choice", None)
    if tag is None and isinstance(answer, dict):
        tag = answer.get("choice")
    if not isinstance(tag, str) or tag not in RISK_TAGS:
        return None, _fallback_record(input_at=input_at, reason="invalid_choice")

    return tag, _success_record(input_at=input_at, tag=tag)


def classify_candidate_risk(
    candidate: dict[str, Any],
    *,
    info_fetcher: Callable[[str], dict[str, Any]] = get_ticker_info,
    classifier: Callable[[str, str], tuple[str | None, dict[str, Any]]] | None = None,
    now: Callable[[], datetime] | None = None,
) -> dict[str, Any]:
    """Classify one Top-N row; never raises."""
    clock = now() if now else datetime.now(UTC)
    input_at = clock.isoformat(timespec="seconds")
    symbol = candidate.get("symbol", "")

    if not os.environ.get(TYPESAFE_API_KEY_ENV, "").strip():
        return _attach_classification(
            candidate,
            tag=None,
            classification=_fallback_record(input_at=input_at, reason="missing_api_key"),
        )

    try:
        info = info_fetcher(symbol) or {}
    except Exception as exc:
        logger.warning("Risk classification info fetch failed: %s", type(exc).__name__)
        return _attach_classification(
            candidate,
            tag=None,
            classification=_fallback_record(input_at=input_at, reason=type(exc).__name__),
        )

    if not isinstance(info, dict):
        info = {}

    summary = info.get("longBusinessSummary")
    if not isinstance(summary, str) or not summary.strip():
        return _attach_classification(
            candidate,
            tag="insufficient_evidence",
            classification=_success_record(input_at=input_at, tag="insufficient_evidence"),
        )

    classify = classifier or (lambda text, ts: _classify_summary(text, input_at=ts))
    try:
        tag, record = classify(summary.strip(), input_at)
    except Exception as exc:
        logger.warning("Risk classification classifier failure: %s", type(exc).__name__)
        tag, record = None, _fallback_record(input_at=input_at, reason=type(exc).__name__)
    return _attach_classification(candidate, tag=tag, classification=record)


def classify_top_candidate_risks(
    top_candidates: list[dict[str, Any]] | None,
    *,
    info_fetcher: Callable[[str], dict[str, Any]] = get_ticker_info,
    classifier: Callable[[str, str], tuple[str | None, dict[str, Any]]] | None = None,
    now: Callable[[], datetime] | None = None,
) -> list[dict[str, Any]] | None:
    """Classify at most min(len(top_candidates), 5) rows."""
    if not top_candidates:
        return top_candidates
    target_rows = top_candidates[:5]
    classified = [
        classify_candidate_risk(
            row,
            info_fetcher=info_fetcher,
            classifier=classifier,
            now=now,
        )
        for row in target_rows
    ]
    if len(top_candidates) > 5:
        classified.extend(top_candidates[5:])
    return classified


def apply_pick_risk_reasoning(
    reasoning: dict[str, Any],
    *,
    pick_symbol: str,
    top_candidates: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    """Prepend dynamic risk text for the pick when classification succeeded."""
    if not top_candidates:
        return reasoning

    match = next((row for row in top_candidates if row.get("symbol") == pick_symbol), None)
    if not match:
        return reasoning

    classification = match.get("riskClassification") or {}
    if classification.get("fallback"):
        return reasoning

    tag = classification.get("tag") or match.get("riskTag")
    text = match.get("riskText") or (risk_text_for_tag(tag) if isinstance(tag, str) else None)
    if not text:
        return reasoning

    out = dict(reasoning)
    out["risks"] = [text, *list(reasoning.get("risks") or [])]
    return out
