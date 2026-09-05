"""Freeze assertions for Issue #70 macro rate gate — live knobs must not change."""

from __future__ import annotations

import config as live_config


def test_live_threshold_and_weights_frozen() -> None:
    assert live_config.COMPOSITE_THRESHOLD == 70.0
    assert live_config.SCORE_VERSION == 2
    assert live_config.WEIGHT_SIZE == 0.15
    assert live_config.WEIGHT_VALUATION == 0.25
    assert live_config.WEIGHT_GROWTH == 0.20
    assert live_config.WEIGHT_QUALITY == 0.20
    assert live_config.WEIGHT_ENTRY == 0.10
    assert live_config.WEIGHT_MOMENTUM == 0.10


def test_live_min_market_caps_frozen() -> None:
    assert live_config.MIN_MARKET_CAP_KR == 50_000_000_000
    assert live_config.MIN_MARKET_CAP_US == 300_000_000


def test_macro_gate_candidate_defaults() -> None:
    assert live_config.ENABLE_MACRO_RATE_GATE_CANDIDATE is False
    assert live_config.THRESHOLD_HIKE_DELTA == 5.0
    assert live_config.SIZE_TIGHTEN_MIN_MCAP_MULT == 1.5
    assert live_config.FED_HIKE_REGIME_PATH.is_file()
