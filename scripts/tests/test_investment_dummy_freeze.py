"""Freeze regression for Score v3 investment-dummy candidate (Issue #68).

Live COMPOSITE_THRESHOLD / WEIGHT_* must stay unchanged. Candidate flag must
default OFF. passes_red_flags must not gain an investment_dummy branch.
"""

from __future__ import annotations

import inspect

import config as live_config
from screening.core import passes_red_flags

# Live Score v2 weight snapshot — must not change in this feature.
_LIVE_WEIGHT_SNAPSHOT = {
    "WEIGHT_SIZE": 0.15,
    "WEIGHT_VALUATION": 0.25,
    "WEIGHT_GROWTH": 0.20,
    "WEIGHT_QUALITY": 0.20,
    "WEIGHT_ENTRY": 0.10,
    "WEIGHT_MOMENTUM": 0.10,
}


def test_composite_threshold_frozen():
    assert live_config.COMPOSITE_THRESHOLD == 70.0


def test_live_weights_snapshot_unchanged():
    for name, expected in _LIVE_WEIGHT_SNAPSHOT.items():
        assert getattr(live_config, name) == expected, f"{name} drifted"


def test_investment_dummy_candidate_flag_default_off():
    assert live_config.ENABLE_INVESTMENT_DUMMY_CANDIDATE is False


def test_investment_dummy_soft_penalty_floor():
    assert live_config.INVESTMENT_DUMMY_SOFT_PENALTY >= 15.0


def test_passes_red_flags_negative_equity():
    assert passes_red_flags({"bookValue": -1, "priceToBook": -1}) is False


def test_passes_red_flags_dual_negative_cashflow():
    assert passes_red_flags({"freeCashflow": -1, "operatingCashflow": -1, "bookValue": 10}) is False


def test_passes_red_flags_clean_pass():
    assert (
        passes_red_flags(
            {
                "bookValue": 10,
                "priceToBook": 1.5,
                "freeCashflow": 5,
                "operatingCashflow": 8,
            }
        )
        is True
    )


def test_passes_red_flags_source_has_no_investment_dummy_branch():
    source = inspect.getsource(passes_red_flags)
    assert "investment_dummy" not in source
