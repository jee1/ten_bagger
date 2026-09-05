"""Regime signal tests for Issue #70 Fed hike dummy."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from scoring.macro_rate_gate import (
    clear_regime_cache,
    load_fed_hike_regime,
    resolve_hike_regime,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "macro_rate_gate"


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    clear_regime_cache()
    yield
    clear_regime_cache()


def test_hike_date_inside_2022_cycle() -> None:
    sig = resolve_hike_regime("2022-06-15")
    assert sig.status == "available"
    assert sig.hike_regime is True
    assert "fed" in sig.source


def test_non_hike_date_inside_span() -> None:
    sig = resolve_hike_regime("2020-06-15")
    assert sig.status == "available"
    assert sig.hike_regime is False


def test_outside_span_unavailable_fail_open() -> None:
    sig = resolve_hike_regime("1990-01-01")
    assert sig.status == "unavailable"
    assert sig.hike_regime is False


def test_determinism() -> None:
    a = resolve_hike_regime("2016-06-01")
    b = resolve_hike_regime("2016-06-01")
    assert a == b


def test_kr_and_us_same_signal_for_same_date() -> None:
    # Market does not change signal in v1; resolve is date-only.
    kr = resolve_hike_regime("2023-01-10")
    us = resolve_hike_regime("2023-01-10")
    assert kr.hike_regime == us.hike_regime
    assert kr.status == us.status


def test_malformed_interval_hard_fails(tmp_path: Path) -> None:
    bad = tmp_path / "bad_regime.json"
    bad.write_text(
        json.dumps({"intervals": [{"start": "2022-01-01", "end": "not-a-date"}]}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="malformed"):
        load_fed_hike_regime(bad, force_reload=True)


def test_malformed_as_of_date() -> None:
    with pytest.raises(ValueError, match="as_of_date"):
        resolve_hike_regime("2022/06/15")


def test_committed_series_loads() -> None:
    intervals = load_fed_hike_regime(force_reload=True)
    assert len(intervals) >= 1
