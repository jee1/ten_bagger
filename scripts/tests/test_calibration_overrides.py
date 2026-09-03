"""Override context manager tests."""

from __future__ import annotations

import config as live_config
import scoring.composite as scoring_composite
import screening.core as screening_core
from calibration.overrides import apply_candidate_overrides

VALID = {
    "WEIGHT_SIZE": 0.15,
    "WEIGHT_VALUATION": 0.20,
    "WEIGHT_GROWTH": 0.20,
    "WEIGHT_QUALITY": 0.25,
    "WEIGHT_ENTRY": 0.10,
    "WEIGHT_MOMENTUM": 0.10,
}


def test_overrides_restore_and_do_not_mutate_config_module():
    live_thr = live_config.COMPOSITE_THRESHOLD
    live_w = live_config.WEIGHT_SIZE
    core_thr = screening_core.COMPOSITE_THRESHOLD
    score_w = scoring_composite.WEIGHT_QUALITY

    with apply_candidate_overrides(99.0, VALID):
        assert screening_core.COMPOSITE_THRESHOLD == 99.0
        assert scoring_composite.WEIGHT_QUALITY == 0.25

    assert screening_core.COMPOSITE_THRESHOLD == core_thr
    assert scoring_composite.WEIGHT_QUALITY == score_w
    assert live_config.COMPOSITE_THRESHOLD == live_thr
    assert live_config.WEIGHT_SIZE == live_w
