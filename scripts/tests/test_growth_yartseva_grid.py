"""Issue #69 growth-reallocation grid validation tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest
from calibration.growth_yartseva import (
    DEFAULT_CANDIDATES,
    LIVE_WEIGHT_GROWTH,
    LIVE_WEIGHTS,
    MIN_WEIGHT_GROWTH,
    assert_issue69_grid,
    load_issue69_config,
    validate_growth_reallocation_candidate,
)

FIX = Path(__file__).resolve().parent / "fixtures" / "calibration"
COMMITTED = (
    Path(__file__).resolve().parents[1] / "calibration" / "configs" / "growth-yartseva-issue69.json"
)


def test_default_candidates_validate():
    for item in DEFAULT_CANDIDATES:
        out = validate_growth_reallocation_candidate(item["weights"])
        assert out["WEIGHT_GROWTH"] < LIVE_WEIGHT_GROWTH
        assert out["WEIGHT_GROWTH"] >= MIN_WEIGHT_GROWTH
        assert abs(sum(out.values()) - 1.0) < 1e-6


def test_assert_issue69_grid_default():
    assert_issue69_grid(DEFAULT_CANDIDATES)


def test_smoke_and_committed_configs_match_grid():
    load_issue69_config(FIX / "growth-yartseva-smoke-config.json")
    load_issue69_config(COMMITTED)


def test_reject_growth_at_or_above_live():
    bad = dict(LIVE_WEIGHTS)
    with pytest.raises(ValueError, match="WEIGHT_GROWTH must be <"):
        validate_growth_reallocation_candidate(bad)


def test_reject_growth_below_floor():
    bad = {
        **LIVE_WEIGHTS,
        "WEIGHT_GROWTH": 0.04,
        "WEIGHT_VALUATION": 0.31,
        "WEIGHT_QUALITY": 0.20,
    }
    # sum = 0.15+0.31+0.04+0.20+0.10+0.10 = 0.90 — fix sum
    bad = {
        "WEIGHT_SIZE": 0.15,
        "WEIGHT_VALUATION": 0.31,
        "WEIGHT_GROWTH": 0.04,
        "WEIGHT_QUALITY": 0.20,
        "WEIGHT_ENTRY": 0.10,
        "WEIGHT_MOMENTUM": 0.10,
    }
    # 0.15+0.31+0.04+0.20+0.10+0.10 = 0.90
    bad["WEIGHT_VALUATION"] = 0.41  # 1.0
    with pytest.raises(ValueError, match="floor"):
        validate_growth_reallocation_candidate(bad)


def test_reject_entry_redistribution():
    bad = deepcopy(DEFAULT_CANDIDATES[0]["weights"])
    bad["WEIGHT_ENTRY"] = 0.11
    bad["WEIGHT_VALUATION"] = bad["WEIGHT_VALUATION"] - 0.01
    with pytest.raises(ValueError, match="WEIGHT_ENTRY"):
        validate_growth_reallocation_candidate(bad)


def test_reject_momentum_redistribution():
    bad = deepcopy(DEFAULT_CANDIDATES[0]["weights"])
    bad["WEIGHT_MOMENTUM"] = 0.11
    bad["WEIGHT_QUALITY"] = bad["WEIGHT_QUALITY"] - 0.01
    with pytest.raises(ValueError, match="WEIGHT_MOMENTUM"):
        validate_growth_reallocation_candidate(bad)


def test_reject_wrong_candidate_ids():
    wrong = deepcopy(DEFAULT_CANDIDATES)
    wrong[0] = {**wrong[0], "candidateId": "not_a_real_id"}
    with pytest.raises(ValueError, match="candidate IDs"):
        assert_issue69_grid(wrong)
