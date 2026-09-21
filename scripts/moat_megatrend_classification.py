"""Observational moat width and megatrend theme for Top-N candidates (Issue #149).

Observational only — does not affect Score v2, ranks, threshold, or pick selection.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from risk_classification import (
    TYPESAFE_API_KEY_ENV,
    cap_sdk_logger,
)
from yf_cache import get_ticker_info

logger = logging.getLogger(__name__)

cap_sdk_logger()

JEV_CLASSIFY_MODEL = "jev-1.13.0"
CLASSIFY_TIMEOUT_SECONDS = 30.0

MOAT_WIDTH_CHOICES: dict[str, dict[str, str | None]] = {
    "none": {
        "ko": "경쟁 우위(해자) 근거 없음",
        "en": "No evident competitive moat",
        "criteria": "Summary shows no durable competitive advantage or defensibility",
    },
    "narrow": {
        "ko": "좁은 해자",
        "en": "Narrow moat",
        "criteria": "Some differentiation but limited scale, durability, or defensibility",
    },
    "wide": {
        "ko": "넓은 해자",
        "en": "Wide moat",
        "criteria": "Strong durable advantages such as brand, network, scale, or switching costs",
    },
}

MEGATREND_THEME_CHOICES: dict[str, dict[str, str | None]] = {
    "none": {
        "ko": "특정 메가트렌드 비중 낮음",
        "en": "Not primarily a listed megatrend theme",
        "criteria": "Business is diversified or not mainly tied to the themes below",
    },
    "ai_infrastructure": {
        "ko": "AI 인프라",
        "en": "AI infrastructure",
        "criteria": "Core exposure to AI compute, data, models, or enabling infrastructure",
    },
    "power_grid": {
        "ko": "전력·그리드",
        "en": "Power grid",
        "criteria": (
            "Core exposure to power generation, grid, electrification, or related infrastructure"
        ),
    },
    "robotics": {
        "ko": "로보틱스·자동화",
        "en": "Robotics",
        "criteria": "Core exposure to robotics, industrial automation, or autonomous systems",
    },
}

MOAT_WIDTHS = frozenset(MOAT_WIDTH_CHOICES)
MEGATREND_THEMES = frozenset(MEGATREND_THEME_CHOICES)

ClassifierFn = Callable[
    [str, str],
    tuple[str | None, dict[str, Any], str | None, dict[str, Any]],
]


def moat_text_for_width(width: str) -> dict[str, str] | None:
    row = MOAT_WIDTH_CHOICES.get(width)
    if not row:
        return None
    return {"ko": str(row["ko"]), "en": str(row["en"])}


def megatrend_text_for_theme(theme: str) -> dict[str, str] | None:
    row = MEGATREND_THEME_CHOICES.get(theme)
    if not row:
        return None
    return {"ko": str(row["ko"]), "en": str(row["en"])}


def _sdk_version() -> str:
    import typesafe_sdk

    cap_sdk_logger()
    return typesafe_sdk.__version__


def _fallback_record(*, input_at: str, reason: str, tag: str | None = None) -> dict[str, Any]:
    record: dict[str, Any] = {
        "model": JEV_CLASSIFY_MODEL,
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
        "model": JEV_CLASSIFY_MODEL,
        "sdkVersion": _sdk_version(),
        "inputAt": input_at,
        "tag": tag,
        "fallback": False,
    }


def _attach_classification(
    candidate: dict[str, Any],
    *,
    moat_width: str | None,
    moat_classification: dict[str, Any],
    megatrend_theme: str | None,
    megatrend_classification: dict[str, Any],
) -> dict[str, Any]:
    out = dict(candidate)
    out["moatClassification"] = moat_classification
    out["megatrendClassification"] = megatrend_classification
    if moat_width and not moat_classification.get("fallback"):
        out["moatWidth"] = moat_width
        text = moat_text_for_width(moat_width)
        if text:
            out["moatText"] = text
    if megatrend_theme and not megatrend_classification.get("fallback"):
        out["megatrendTheme"] = megatrend_theme
        text = megatrend_text_for_theme(megatrend_theme)
        if text:
            out["megatrendText"] = text
    return out


def _parse_choice(answer: Any, valid: frozenset[str]) -> str | None:
    tag = getattr(answer, "choice", None)
    if tag is None and isinstance(answer, dict):
        tag = answer.get("choice")
    if isinstance(tag, str) and tag in valid:
        return tag
    return None


def _classify_summary(
    summary: str, *, input_at: str
) -> tuple[str | None, dict[str, Any], str | None, dict[str, Any]]:
    from typesafe_sdk import Choice, TypeSafeClient, TypeSafeError

    cap_sdk_logger()

    moat_criteria = {
        key: row["criteria"] for key, row in MOAT_WIDTH_CHOICES.items() if row["criteria"]
    }
    theme_criteria = {
        key: row["criteria"] for key, row in MEGATREND_THEME_CHOICES.items() if row["criteria"]
    }
    questions = {
        "moat_width": Choice(
            instructions=(
                "From the company's long business summary, classify observational moat width."
            ),
            criteria=moat_criteria,
        ),
        "megatrend_theme": Choice(
            instructions=(
                "From the company's long business summary, pick the single "
                "best-fit megatrend theme."
            ),
            criteria=theme_criteria,
        ),
    }

    try:
        with TypeSafeClient(model=JEV_CLASSIFY_MODEL) as client:
            response = client.system_one(
                summary,
                questions,
                model=JEV_CLASSIFY_MODEL,
                timeout=CLASSIFY_TIMEOUT_SECONDS,
            )
    except TypeSafeError as exc:
        logger.warning("Moat/megatrend classification API failure: %s", type(exc).__name__)
        reason = type(exc).__name__
        return (
            None,
            _fallback_record(input_at=input_at, reason=reason),
            None,
            _fallback_record(input_at=input_at, reason=reason),
        )
    except Exception as exc:
        logger.warning("Moat/megatrend classification unexpected failure: %s", type(exc).__name__)
        reason = type(exc).__name__
        return (
            None,
            _fallback_record(input_at=input_at, reason=reason),
            None,
            _fallback_record(input_at=input_at, reason=reason),
        )

    moat_answer = response.answers.get("moat_width")
    theme_answer = response.answers.get("megatrend_theme")

    if moat_answer is None:
        moat_width, moat_record = None, _fallback_record(input_at=input_at, reason="missing_answer")
    else:
        moat_width = _parse_choice(moat_answer, MOAT_WIDTHS)
        if moat_width is None:
            moat_record = _fallback_record(input_at=input_at, reason="invalid_choice")
        else:
            moat_record = _success_record(input_at=input_at, tag=moat_width)

    if theme_answer is None:
        theme, theme_record = None, _fallback_record(input_at=input_at, reason="missing_answer")
    else:
        theme = _parse_choice(theme_answer, MEGATREND_THEMES)
        if theme is None:
            theme_record = _fallback_record(input_at=input_at, reason="invalid_choice")
        else:
            theme_record = _success_record(input_at=input_at, tag=theme)

    return moat_width, moat_record, theme, theme_record


def classify_candidate_moat_megatrend(
    candidate: dict[str, Any],
    *,
    info_fetcher: Callable[[str], dict[str, Any]] = get_ticker_info,
    classifier: ClassifierFn | None = None,
    now: Callable[[], datetime] | None = None,
) -> dict[str, Any]:
    """Classify one Top-N row; never raises."""
    clock = now() if now else datetime.now(UTC)
    input_at = clock.isoformat(timespec="seconds")
    symbol = candidate.get("symbol", "")

    if not os.environ.get(TYPESAFE_API_KEY_ENV, "").strip():
        reason = "missing_api_key"
        return _attach_classification(
            candidate,
            moat_width=None,
            moat_classification=_fallback_record(input_at=input_at, reason=reason),
            megatrend_theme=None,
            megatrend_classification=_fallback_record(input_at=input_at, reason=reason),
        )

    try:
        info = info_fetcher(symbol) or {}
    except Exception as exc:
        logger.warning("Moat/megatrend info fetch failed: %s", type(exc).__name__)
        reason = type(exc).__name__
        return _attach_classification(
            candidate,
            moat_width=None,
            moat_classification=_fallback_record(input_at=input_at, reason=reason),
            megatrend_theme=None,
            megatrend_classification=_fallback_record(input_at=input_at, reason=reason),
        )

    if not isinstance(info, dict):
        info = {}

    summary = info.get("longBusinessSummary")
    if not isinstance(summary, str) or not summary.strip():
        reason = "missing_summary"
        return _attach_classification(
            candidate,
            moat_width=None,
            moat_classification=_fallback_record(input_at=input_at, reason=reason),
            megatrend_theme=None,
            megatrend_classification=_fallback_record(input_at=input_at, reason=reason),
        )

    classify = classifier or (lambda text, ts: _classify_summary(text, input_at=ts))
    try:
        moat_width, moat_record, theme, theme_record = classify(summary.strip(), input_at)
    except Exception as exc:
        logger.warning("Moat/megatrend classifier failure: %s", type(exc).__name__)
        reason = type(exc).__name__
        moat_width, moat_record = None, _fallback_record(input_at=input_at, reason=reason)
        theme, theme_record = None, _fallback_record(input_at=input_at, reason=reason)

    return _attach_classification(
        candidate,
        moat_width=moat_width,
        moat_classification=moat_record,
        megatrend_theme=theme,
        megatrend_classification=theme_record,
    )


def classify_top_candidate_moat_megatrend(
    top_candidates: list[dict[str, Any]] | None,
    *,
    info_fetcher: Callable[[str], dict[str, Any]] = get_ticker_info,
    classifier: ClassifierFn | None = None,
    now: Callable[[], datetime] | None = None,
) -> list[dict[str, Any]] | None:
    """Classify at most min(len(top_candidates), 5) rows."""
    if not top_candidates:
        return top_candidates
    target_rows = top_candidates[:5]
    classified = [
        classify_candidate_moat_megatrend(
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
