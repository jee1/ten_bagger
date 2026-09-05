"""Apply-variant tests for Issue #70 macro rate gate."""

from __future__ import annotations

import config as live_config
from scoring.macro_rate_gate import clear_regime_cache, effective_selection_knobs

HIKE_DAY = "2022-06-15"
NON_HIKE_DAY = "2020-06-15"
OUTSIDE_DAY = "1990-01-01"


def setup_function() -> None:
    clear_regime_cache()


def teardown_function() -> None:
    clear_regime_cache()


def test_threshold_raise_when_enabled_and_hike() -> None:
    knobs = effective_selection_knobs(
        as_of_date=HIKE_DAY,
        market="US",
        variant="threshold_raise",
        enabled=True,
    )
    assert knobs.gate_applied is True
    assert knobs.composite_threshold == 70.0 + live_config.THRESHOLD_HIKE_DELTA
    assert live_config.COMPOSITE_THRESHOLD == 70.0


def test_size_tighten_when_enabled_and_hike() -> None:
    knobs = effective_selection_knobs(
        as_of_date=HIKE_DAY,
        market="KR",
        variant="size_tighten",
        enabled=True,
    )
    assert knobs.gate_applied is True
    mult = live_config.SIZE_TIGHTEN_MIN_MCAP_MULT
    assert knobs.min_market_cap_kr == int(round(live_config.MIN_MARKET_CAP_KR * mult))
    assert knobs.min_market_cap_us == int(round(live_config.MIN_MARKET_CAP_US * mult))
    assert live_config.MIN_MARKET_CAP_KR == 50_000_000_000
    assert live_config.MIN_MARKET_CAP_US == 300_000_000


def test_flag_off_no_gate_even_on_hike() -> None:
    assert live_config.ENABLE_MACRO_RATE_GATE_CANDIDATE is False
    knobs = effective_selection_knobs(
        as_of_date=HIKE_DAY,
        market="US",
        variant="threshold_raise",
        enabled=None,
    )
    assert knobs.enabled is False
    assert knobs.gate_applied is False
    assert knobs.composite_threshold == live_config.COMPOSITE_THRESHOLD


def test_non_hike_no_gate_when_enabled() -> None:
    knobs = effective_selection_knobs(
        as_of_date=NON_HIKE_DAY,
        market="US",
        variant="threshold_raise",
        enabled=True,
    )
    assert knobs.hike_regime is False
    assert knobs.gate_applied is False
    assert knobs.composite_threshold == 70.0


def test_unavailable_fail_open() -> None:
    knobs = effective_selection_knobs(
        as_of_date=OUTSIDE_DAY,
        market="KR",
        variant="size_tighten",
        enabled=True,
    )
    assert knobs.regime_status == "unavailable"
    assert knobs.gate_applied is False
    assert knobs.min_market_cap_kr == live_config.MIN_MARKET_CAP_KR


def test_both_variants_selectable() -> None:
    t = effective_selection_knobs(
        as_of_date=HIKE_DAY, market="US", variant="threshold_raise", enabled=True
    )
    s = effective_selection_knobs(
        as_of_date=HIKE_DAY, market="US", variant="size_tighten", enabled=True
    )
    assert t.gate_applied and s.gate_applied
    assert t.composite_threshold > live_config.COMPOSITE_THRESHOLD
    assert s.min_market_cap_us > live_config.MIN_MARKET_CAP_US
