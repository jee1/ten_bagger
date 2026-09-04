"""Unit tests for compute_investment_dummy_metric (Issue #68 / feature 024 US1)."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest
from scoring.investment_dummy import compute_investment_dummy_metric

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "investment_dummy"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def _call(fx: dict):
    return compute_investment_dummy_metric(
        prior_total_assets=fx["prior_total_assets"],
        current_total_assets=fx["current_total_assets"],
        prior_ebitda=fx["prior_ebitda"],
        current_ebitda=fx["current_ebitda"],
    )


# --- T008: available hit ---


def test_hit_dummy_asset_growth_exceeds_ebitda():
    fx = _load("hit_dummy.json")
    m = _call(fx)
    exp = fx["expected"]
    assert m.status == "available"
    assert m.asset_growth_pct == pytest.approx(exp["asset_growth_pct"])
    assert m.ebitda_growth_pct == pytest.approx(exp["ebitda_growth_pct"])
    assert m.spread_pct == pytest.approx(exp["spread_pct"])
    assert m.spread_pct == pytest.approx(m.asset_growth_pct - m.ebitda_growth_pct)
    assert m.investment_dummy is True


# --- T009: non-hit, equal, both-negative hit ---


def test_no_hit_when_ebitda_growth_ge_asset():
    fx = _load("no_hit.json")
    m = _call(fx)
    exp = fx["expected"]
    assert m.status == "available"
    assert m.investment_dummy is False
    assert m.spread_pct == pytest.approx(exp["spread_pct"])


def test_equal_growth_is_not_dummy():
    fx = _load("equal_growth.json")
    m = _call(fx)
    assert m.status == "available"
    assert m.asset_growth_pct == pytest.approx(m.ebitda_growth_pct)
    assert m.spread_pct == pytest.approx(0.0)
    assert m.investment_dummy is False


def test_both_negative_growth_can_still_hit():
    fx = _load("both_negative_hit.json")
    m = _call(fx)
    exp = fx["expected"]
    assert m.status == "available"
    assert m.asset_growth_pct == pytest.approx(exp["asset_growth_pct"])
    assert m.ebitda_growth_pct == pytest.approx(exp["ebitda_growth_pct"])
    assert m.asset_growth_pct > m.ebitda_growth_pct
    assert m.investment_dummy is True
    assert m.spread_pct == pytest.approx(exp["spread_pct"])


# --- T010: unavailable ---


def _assert_unavailable(m, *, reason: str | None = None):
    assert m.status == "unavailable"
    assert m.investment_dummy is False
    assert m.asset_growth_pct is None
    assert m.ebitda_growth_pct is None
    assert m.spread_pct is None
    if reason is not None:
        assert m.reason == reason


def test_unavailable_negative_ebitda():
    fx = _load("unavailable_neg_ebitda.json")
    m = _call(fx)
    _assert_unavailable(m, reason="non_positive_ebitda")


def test_unavailable_zero_prior_assets():
    fx = _load("unavailable_zero_prior_assets.json")
    m = _call(fx)
    _assert_unavailable(m, reason="zero_prior_assets")


def test_unavailable_missing_fields():
    m = compute_investment_dummy_metric(
        prior_total_assets=None,
        current_total_assets=120.0,
        prior_ebitda=20.0,
        current_ebitda=22.0,
    )
    _assert_unavailable(m, reason="missing_inputs")


def test_unavailable_zero_ebitda_either_period():
    m = compute_investment_dummy_metric(
        prior_total_assets=100.0,
        current_total_assets=110.0,
        prior_ebitda=0.0,
        current_ebitda=12.0,
    )
    _assert_unavailable(m, reason="non_positive_ebitda")


def test_unavailable_does_not_invent_zero_growth():
    """Missing/invalid inputs must not coerce to 0% growth."""
    m = compute_investment_dummy_metric(
        prior_total_assets=100.0,
        current_total_assets=None,
        prior_ebitda=20.0,
        current_ebitda=22.0,
    )
    _assert_unavailable(m)
    assert m.asset_growth_pct is None
    assert m.ebitda_growth_pct is None
    assert m.spread_pct is None


# --- T011: determinism ---


def test_determinism_identical_inputs_twice():
    kwargs = dict(
        prior_total_assets=100.0,
        current_total_assets=130.0,
        prior_ebitda=20.0,
        current_ebitda=22.0,
    )
    a = compute_investment_dummy_metric(**kwargs)
    b = compute_investment_dummy_metric(**kwargs)
    assert a == b
    assert a.status == b.status
    assert a.asset_growth_pct == b.asset_growth_pct
    assert a.ebitda_growth_pct == b.ebitda_growth_pct
    assert a.spread_pct == b.spread_pct
    assert a.investment_dummy == b.investment_dummy


def test_growth_formula_uses_abs_prior():
    """(current - prior) / abs(prior) * 100 when prior ≠ 0."""
    # Negative prior assets still available if ≠ 0 and EBITDA > 0 both periods
    m = compute_investment_dummy_metric(
        prior_total_assets=-100.0,
        current_total_assets=-80.0,
        prior_ebitda=10.0,
        current_ebitda=12.0,
    )
    assert m.status == "available"
    # (-80 - (-100)) / abs(-100) * 100 = 20
    assert m.asset_growth_pct == pytest.approx(20.0)
    assert math.isfinite(m.asset_growth_pct)


# --- T013: optional statements adapter (analysis-only) ---


def test_extract_period_fundamentals_from_statement_dicts():
    from scoring.investment_dummy import extract_period_fundamentals_from_statement_dicts

    balance = {
        "2023-12-31": {"Total Assets": 130.0},
        "2022-12-31": {"Total Assets": 100.0},
    }
    income = {
        "2023-12-31": {"EBITDA": 22.0},
        "2022-12-31": {"EBITDA": 20.0},
    }
    got = extract_period_fundamentals_from_statement_dicts(balance, income)
    assert got == {
        "prior_total_assets": 100.0,
        "current_total_assets": 130.0,
        "prior_ebitda": 20.0,
        "current_ebitda": 22.0,
    }
    m = compute_investment_dummy_metric(**got)
    assert m.status == "available"
    assert m.investment_dummy is True


def test_extract_missing_column_yields_none():
    from scoring.investment_dummy import extract_period_fundamentals_from_statement_dicts

    balance = {
        "2023-12-31": {"Total Assets": 130.0},
        "2022-12-31": {"Total Assets": 100.0},
    }
    income = {
        "2023-12-31": {},
        "2022-12-31": {"EBITDA": 20.0},
    }
    got = extract_period_fundamentals_from_statement_dicts(balance, income)
    assert got["current_ebitda"] is None
    m = compute_investment_dummy_metric(**got)
    assert m.status == "unavailable"
    assert m.investment_dummy is False
