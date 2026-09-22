"""Rendering regression: missing metrics must not surface nan/NaN/Infinity/None."""

from __future__ import annotations

import pytest
from config import COMPOSITE_THRESHOLD, ENTRY_DEFAULT_SCORE, MOMENTUM_DEFAULT_SCORE, UniverseSymbol
from missing_metrics_fixture import build_missing_metrics_pick_entry
from reasoning import MISSING_LABEL, build_reasoning, reasoning_has_forbidden_tokens
from scoring.models import ScoreResult


def _pick(**metrics) -> ScoreResult:
    return ScoreResult(
        symbol="TEST",
        meta=UniverseSymbol("TEST", "테스트", "Test Co", "NASDAQ", "USD"),
        size=80.0,
        growth=85.0,
        valuation=70.0,
        entry=59.0,
        momentum=100.0,
        quality=72.0,
        composite=84.3,
        metrics=metrics,
        score_version=2,
    )


def _all_reasoning_text(reasoning: dict) -> str:
    chunks: list[str] = []
    for section in reasoning.values():
        if isinstance(section, dict) and "ko" in section:
            chunks.extend(str(section[lang]) for lang in ("ko", "en"))
        elif isinstance(section, list):
            for item in section:
                if isinstance(item, dict):
                    chunks.extend(str(item[lang]) for lang in ("ko", "en") if lang in item)
    return "\n".join(chunks)


@pytest.mark.parametrize(
    "metrics",
    [
        {
            "twelve_month_range_pct": None,
            "from_52w_high_pct": None,
            "six_month_return_pct": None,
        },
        {
            "twelve_month_range_pct": float("nan"),
            "from_52w_high_pct": float("nan"),
            "six_month_return_pct": float("nan"),
            "pe": None,
            "peg": float("nan"),
        },
        {
            "twelve_month_range_pct": 50.0,
            "from_52w_high_pct": float("nan"),
            "six_month_return_pct": float("nan"),
        },
    ],
)
def test_build_reasoning_missing_metrics_renders_safe(metrics):
    reasoning = build_reasoning(_pick(**metrics))
    text = _all_reasoning_text(reasoning)

    assert not reasoning_has_forbidden_tokens(reasoning)
    assert "nan" not in text.lower()
    assert "infinity" not in text.lower()
    assert "None" not in text
    assert MISSING_LABEL["ko"] in reasoning["entry"]["ko"]
    assert MISSING_LABEL["en"] in reasoning["entry"]["en"]
    assert f"{MISSING_LABEL['ko']}%" not in reasoning["entry"]["ko"]
    assert f"{MISSING_LABEL['en']}%" not in reasoning["entry"]["en"]
    assert MISSING_LABEL["ko"] in reasoning["momentum"]["ko"]
    assert f"{MISSING_LABEL['ko']}%" not in reasoning["momentum"]["ko"]


def test_build_reasoning_insufficient_history_explains_default_scores():
    result = _pick(
        twelve_month_range_pct=None,
        from_52w_high_pct=None,
        six_month_return_pct=None,
    )
    result.entry = ENTRY_DEFAULT_SCORE
    result.momentum = MOMENTUM_DEFAULT_SCORE

    reasoning = build_reasoning(result)

    assert "기본 진입 점수" in reasoning["entry"]["ko"]
    assert "default entry score" in reasoning["entry"]["en"]
    assert "기본 모멘텀 점수" in reasoning["momentum"]["ko"]
    assert "default momentum score" in reasoning["momentum"]["en"]
    assert f"복합 임계 {COMPOSITE_THRESHOLD}" in reasoning["entry"]["ko"]
    assert f"composite threshold {COMPOSITE_THRESHOLD}" in reasoning["entry"]["en"]


def test_build_reasoning_partial_missing_explains_available_data_score():
    reasoning = build_reasoning(
        _pick(
            twelve_month_range_pct=50.0,
            from_52w_high_pct=float("nan"),
            six_month_return_pct=float("nan"),
        )
    )

    assert "가용 데이터" in reasoning["entry"]["ko"]
    assert "available data" in reasoning["entry"]["en"]
    assert f"복합 임계 {COMPOSITE_THRESHOLD}" in reasoning["entry"]["ko"]
    assert f"composite threshold {COMPOSITE_THRESHOLD}" in reasoning["entry"]["en"]


def test_generate_daily_pick_missing_metrics_reasoning_is_safe():
    entry = build_missing_metrics_pick_entry()
    reasoning = entry["reasoning"]

    assert not reasoning_has_forbidden_tokens(reasoning)
    assert "None" not in _all_reasoning_text(reasoning)
    assert f"{MISSING_LABEL['ko']}%" not in reasoning["entry"]["ko"]
    assert f"{MISSING_LABEL['en']}%" not in reasoning["momentum"]["en"]
