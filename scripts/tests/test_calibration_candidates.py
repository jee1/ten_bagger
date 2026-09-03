"""Tests for calibration candidate validation."""

from __future__ import annotations

import pytest
from calibration.candidates import parse_candidates, validate_weights

VALID = {
    "WEIGHT_SIZE": 0.15,
    "WEIGHT_VALUATION": 0.25,
    "WEIGHT_GROWTH": 0.20,
    "WEIGHT_QUALITY": 0.20,
    "WEIGHT_ENTRY": 0.10,
    "WEIGHT_MOMENTUM": 0.10,
}


def test_validate_weights_accepts_unit_sum():
    assert validate_weights(VALID)["WEIGHT_SIZE"] == 0.15


def test_validate_weights_rejects_bad_sum():
    bad = {**VALID, "WEIGHT_MOMENTUM": 0.20}
    with pytest.raises(ValueError, match="sum"):
        validate_weights(bad)


def test_validate_weights_rejects_unknown_keys():
    bad = {**VALID, "WEIGHT_NESTED": 0.0}
    with pytest.raises(ValueError, match="unknown"):
        validate_weights(bad)


def test_parse_candidates_rejects_more_than_ten():
    raw = [{"candidateId": f"c{i}", "threshold": None, "weights": None} for i in range(11)]
    with pytest.raises(ValueError, match="10"):
        parse_candidates(raw, mode="search")
