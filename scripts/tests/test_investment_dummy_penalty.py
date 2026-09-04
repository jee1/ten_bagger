"""Soft penalty + label for investment-dummy candidate path (Issue #68 / US2)."""

from __future__ import annotations

import inspect
from unittest.mock import patch

import config as live_config
import pytest
from config import SCORE_VERSION, UniverseSymbol
from scoring.investment_dummy import (
    InvestmentDummyMetric,
    apply_investment_dummy_adjustment,
    compute_investment_dummy_metric,
)
from scoring.models import ScoreResult
from screening.core import passes_red_flags


def _score(*, composite: float = 80.0, metrics: dict | None = None) -> ScoreResult:
    return ScoreResult(
        symbol="TEST",
        meta=UniverseSymbol("TEST", "테스트", "Test Co", "NASDAQ", "USD"),
        size=80.0,
        growth=75.0,
        valuation=78.0,
        entry=70.0,
        momentum=65.0,
        quality=72.0,
        composite=composite,
        metrics={} if metrics is None else metrics,
        score_version=SCORE_VERSION,
    )


def _hit_metric() -> InvestmentDummyMetric:
    return compute_investment_dummy_metric(
        prior_total_assets=100.0,
        current_total_assets=130.0,
        prior_ebitda=20.0,
        current_ebitda=22.0,
    )


def _no_hit_metric() -> InvestmentDummyMetric:
    return compute_investment_dummy_metric(
        prior_total_assets=100.0,
        current_total_assets=110.0,
        prior_ebitda=20.0,
        current_ebitda=25.0,
    )


def _unavailable_metric() -> InvestmentDummyMetric:
    return compute_investment_dummy_metric(
        prior_total_assets=None,
        current_total_assets=130.0,
        prior_ebitda=20.0,
        current_ebitda=22.0,
    )


# --- T015: enabled + dummy true ---


def test_enabled_dummy_true_applies_soft_penalty_and_label():
    result = _score(composite=80.0)
    metric = _hit_metric()
    assert metric.status == "available"
    assert metric.investment_dummy is True

    adj = apply_investment_dummy_adjustment(result, metric, enabled=True)

    assert adj.enabled is True
    assert adj.applied is True
    assert adj.soft_penalty == live_config.INVESTMENT_DUMMY_SOFT_PENALTY
    assert adj.soft_penalty >= 15.0
    assert adj.label == "investment_dummy"
    assert adj.composite_before == 80.0
    assert adj.composite_after == pytest.approx(80.0 - live_config.INVESTMENT_DUMMY_SOFT_PENALTY)
    assert result.composite == pytest.approx(adj.composite_after)

    assert result.metrics["investment_dummy_status"] == "available"
    assert result.metrics["asset_growth_pct"] == pytest.approx(metric.asset_growth_pct)
    assert result.metrics["ebitda_growth_pct"] == pytest.approx(metric.ebitda_growth_pct)
    assert result.metrics["spread_pct"] == pytest.approx(metric.spread_pct)
    assert result.metrics["investment_dummy"] is True
    assert "investment_dummy" in result.metrics["red_flag_labels"]


# --- T016: no penalty paths ---


def test_enabled_dummy_false_no_penalty_no_label():
    result = _score(composite=80.0)
    adj = apply_investment_dummy_adjustment(result, _no_hit_metric(), enabled=True)

    assert adj.applied is False
    assert adj.soft_penalty == 0.0
    assert adj.label is None
    assert adj.composite_after == 80.0
    assert result.composite == 80.0
    assert "investment_dummy" not in (result.metrics.get("red_flag_labels") or [])


def test_enabled_unavailable_no_penalty_no_label():
    result = _score(composite=80.0)
    adj = apply_investment_dummy_adjustment(result, _unavailable_metric(), enabled=True)

    assert adj.applied is False
    assert adj.soft_penalty == 0.0
    assert adj.label is None
    assert result.composite == 80.0
    assert "investment_dummy" not in (result.metrics.get("red_flag_labels") or [])


def test_flag_off_no_penalty_even_if_dummy_would_hit():
    result = _score(composite=80.0)
    metric = _hit_metric()
    assert metric.investment_dummy is True

    adj = apply_investment_dummy_adjustment(result, metric, enabled=False)

    assert adj.enabled is False
    assert adj.applied is False
    assert adj.soft_penalty == 0.0
    assert adj.label is None
    assert result.composite == 80.0
    assert "investment_dummy" not in (result.metrics.get("red_flag_labels") or [])


def test_enabled_defaults_to_config_flag_off():
    """Default enabled=None must follow ENABLE_INVESTMENT_DUMMY_CANDIDATE (False)."""
    assert live_config.ENABLE_INVESTMENT_DUMMY_CANDIDATE is False
    result = _score(composite=80.0)
    adj = apply_investment_dummy_adjustment(result, _hit_metric())
    assert adj.enabled is False
    assert adj.applied is False
    assert result.composite == 80.0


# --- T017: additive with hard red flags; apply does not touch passes_red_flags ---


def test_hard_red_flags_still_fail_independently():
    assert passes_red_flags({"bookValue": -1, "priceToBook": -1}) is False
    assert (
        passes_red_flags(
            {"freeCashflow": -1, "operatingCashflow": -1, "bookValue": 10}
        )
        is False
    )


def test_apply_does_not_call_passes_red_flags():
    result = _score(composite=80.0)
    with patch("screening.core.passes_red_flags") as spy:
        apply_investment_dummy_adjustment(result, _hit_metric(), enabled=True)
        spy.assert_not_called()


def test_apply_source_does_not_reference_passes_red_flags():
    source = inspect.getsource(apply_investment_dummy_adjustment)
    assert "passes_red_flags" not in source


# --- T019: optional helper must not wire live path by default ---


def test_maybe_apply_helper_exists_and_respects_flag_default():
    from scoring.investment_dummy import maybe_apply_investment_dummy

    result = _score(composite=80.0)
    adj = maybe_apply_investment_dummy(
        result,
        {
            "prior_total_assets": 100.0,
            "current_total_assets": 130.0,
            "prior_ebitda": 20.0,
            "current_ebitda": 22.0,
        },
    )
    assert adj.applied is False
    assert result.composite == 80.0


def test_score_symbol_and_generate_daily_do_not_enable_by_default():
    import generate_daily
    import screening.core as core

    assert "maybe_apply_investment_dummy" not in inspect.getsource(core.score_symbol)
    assert "apply_investment_dummy_adjustment" not in inspect.getsource(core.score_symbol)
    gd_src = inspect.getsource(generate_daily)
    assert "apply_investment_dummy_adjustment" not in gd_src
    assert "maybe_apply_investment_dummy" not in gd_src


# --- T020: optional bilingual risk only when applied ---


def test_build_reasoning_adds_investment_dummy_risk_only_when_applied():
    from reasoning import build_reasoning

    clean = _score(composite=80.0, metrics={"revenue_growth_pct": 20})
    reasoning_clean = build_reasoning(clean)
    risk_text = " ".join(
        f"{r.get('ko', '')} {r.get('en', '')}" for r in reasoning_clean["risks"]
    )
    assert "investment_dummy" not in risk_text.lower()
    assert "자산 성장" not in risk_text

    hit = _score(composite=80.0, metrics={"revenue_growth_pct": 20})
    apply_investment_dummy_adjustment(hit, _hit_metric(), enabled=True)
    reasoning_hit = build_reasoning(hit)
    assert any(
        "investment_dummy" in (r.get("en", "") + r.get("ko", "")).lower()
        or "자산" in r.get("ko", "")
        for r in reasoning_hit["risks"]
    )


# --- T021 REVIEW: freeze invariants still hold ---


def test_review_freeze_threshold_weights_and_passes_red_flags():
    assert live_config.COMPOSITE_THRESHOLD == 70.0
    assert live_config.WEIGHT_SIZE == 0.15
    assert live_config.WEIGHT_VALUATION == 0.25
    assert live_config.WEIGHT_GROWTH == 0.20
    assert live_config.WEIGHT_QUALITY == 0.20
    assert live_config.WEIGHT_ENTRY == 0.10
    assert live_config.WEIGHT_MOMENTUM == 0.10
    assert live_config.ENABLE_INVESTMENT_DUMMY_CANDIDATE is False
    source = inspect.getsource(passes_red_flags)
    assert "investment_dummy" not in source
