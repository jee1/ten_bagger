"""Unit tests for screening score functions."""

from __future__ import annotations

import pytest

from config import (
    COMPOSITE_THRESHOLD,
    MAX_GROWTH_PCT,
    MIN_MARKET_CAP_KR,
    UniverseSymbol,
)
from screen import (
    _clip_growth_pct,
    _score_growth,
    _score_quality,
    _score_valuation,
    passes_market_cap_filter,
)


def test_clip_growth_pct_caps_spike():
    assert _clip_growth_pct(492.1) == MAX_GROWTH_PCT
    assert _clip_growth_pct(50.0) == 50.0
    assert _clip_growth_pct(-10.0) == 0.0


def test_score_growth_clips_earnings_spike():
    info = {"revenueGrowth": 0.15, "earningsGrowth": 4.92}
    score, metrics = _score_growth(info)
    assert metrics["earnings_growth_pct"] == MAX_GROWTH_PCT
    assert score <= 100.0


def test_score_valuation_low_pe_high_score():
    info = {"trailingPE": 10, "pegRatio": 0.7}
    score, metrics = _score_valuation(info)
    assert score >= 80
    assert metrics["pe"] == 10
    assert metrics["peg"] == 0.7


def test_score_valuation_high_pe_low_score():
    info = {"trailingPE": 50, "pegRatio": 3.0}
    score, _ = _score_valuation(info)
    assert score < 50


def test_score_quality_positive_roe():
    info = {"returnOnEquity": 0.20, "debtToEquity": 40, "operatingMargins": 0.15}
    score, metrics = _score_quality(info)
    assert score > 50
    assert metrics["roe_pct"] == pytest.approx(20.0)


def test_market_cap_filter_kr():
    small = UniverseSymbol("000001.KQ", "a", "a", "KOSDAQ", "KRW", market_cap=1_000_000_000)
    large = UniverseSymbol("005930.KS", "b", "b", "KOSPI", "KRW", market_cap=MIN_MARKET_CAP_KR)
    assert passes_market_cap_filter(small, "KR") is False
    assert passes_market_cap_filter(large, "KR") is True
    assert passes_market_cap_filter(small, "US", {"marketCap": 1_000_000_000}) is True


def test_composite_threshold_is_documented():
    assert COMPOSITE_THRESHOLD == 70.0
