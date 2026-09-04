"""Live freeze regression for Issue #69 growth-weight analysis."""

from __future__ import annotations

import config as live_config

_LIVE_WEIGHT_SNAPSHOT = {
    "WEIGHT_SIZE": 0.15,
    "WEIGHT_VALUATION": 0.25,
    "WEIGHT_GROWTH": 0.20,
    "WEIGHT_QUALITY": 0.20,
    "WEIGHT_ENTRY": 0.10,
    "WEIGHT_MOMENTUM": 0.10,
}


def test_score_version_still_v2():
    assert live_config.SCORE_VERSION == 2


def test_composite_threshold_frozen():
    assert live_config.COMPOSITE_THRESHOLD == 70.0


def test_live_weights_unchanged_by_issue69_analysis():
    for name, expected in _LIVE_WEIGHT_SNAPSHOT.items():
        assert getattr(live_config, name) == expected, f"{name} drifted"
