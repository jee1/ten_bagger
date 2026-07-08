"""Unit tests for screening score functions."""

from __future__ import annotations

import pandas as pd
import pytest

from config import (
    COMPOSITE_THRESHOLD,
    MAX_GROWTH_PCT,
    MAX_IDEAL_MARKET_CAP_US,
    MIN_MARKET_CAP_KR,
    SCORE_VERSION,
    UniverseSymbol,
)
from screen import (
    _clip_growth_pct,
    _score_entry,
    _score_growth,
    _score_pe_peg,
    _score_quality,
    _score_size,
    _score_valuation,
    passes_market_cap_filter,
    passes_red_flags,
)


def test_clip_growth_pct_caps_spike():
    assert _clip_growth_pct(492.1) == MAX_GROWTH_PCT
    assert _clip_growth_pct(50.0) == 50.0
    assert _clip_growth_pct(-10.0) == 0.0


def test_score_growth_sweet_spot_beats_extreme():
    moderate = {"revenueGrowth": 0.25, "earningsGrowth": 0.35}
    extreme = {"revenueGrowth": 0.80, "earningsGrowth": 0.90}
    mod_score, _ = _score_growth(moderate)
    ext_score, _ = _score_growth(extreme)
    assert mod_score > ext_score


def test_score_growth_clips_earnings_spike_metrics():
    info = {"revenueGrowth": 0.15, "earningsGrowth": 4.92}
    _, metrics = _score_growth(info)
    assert metrics["earnings_growth_pct"] == MAX_GROWTH_PCT


def test_score_pe_peg_low_pe_high_score():
    info = {"trailingPE": 10, "pegRatio": 0.7}
    score, metrics = _score_pe_peg(info)
    assert score >= 80
    assert metrics["pe"] == 10
    assert metrics["peg"] == 0.7


def test_score_pe_peg_high_pe_low_score():
    info = {"trailingPE": 50, "pegRatio": 3.0}
    score, _ = _score_pe_peg(info)
    assert score < 50


def test_score_valuation_includes_fcf_and_pb():
    meta = UniverseSymbol("TEST", "t", "Test", "NASDAQ", "USD")
    info = {
        "trailingPE": 10,
        "pegRatio": 0.7,
        "freeCashflow": 50_000_000,
        "marketCap": 500_000_000,
        "priceToBook": 1.5,
    }
    score, metrics = _score_valuation(info, meta)
    assert score >= 70
    assert metrics["fcf_yield_pct"] == 10.0
    assert metrics["price_to_book"] == 1.5


def test_score_size_small_cap_scores_higher():
    small_meta = UniverseSymbol("S", "s", "Small", "NASDAQ", "USD")
    large_meta = UniverseSymbol("L", "l", "Large", "NASDAQ", "USD")
    small_info = {"marketCap": 400_000_000}
    large_info = {"marketCap": 50_000_000_000}
    small_score, _ = _score_size(small_meta, small_info, "US")
    large_score, _ = _score_size(large_meta, large_info, "US")
    assert small_score > large_score


def test_score_size_ideal_cap_gets_max_band():
    meta = UniverseSymbol("M", "m", "Mid", "NASDAQ", "USD")
    info = {"marketCap": MAX_IDEAL_MARKET_CAP_US, "numberOfAnalystOpinions": 2}
    score, _ = _score_size(meta, info, "US")
    assert score == 100.0


def test_score_size_low_coverage_beats_high_coverage_at_ideal_cap():
    meta = UniverseSymbol("M", "m", "Mid", "NASDAQ", "USD")
    low = {"marketCap": MAX_IDEAL_MARKET_CAP_US, "numberOfAnalystOpinions": 2}
    high = {"marketCap": MAX_IDEAL_MARKET_CAP_US, "numberOfAnalystOpinions": 20}
    low_score, _ = _score_size(meta, low, "US")
    high_score, _ = _score_size(meta, high, "US")
    assert low_score > high_score


def test_score_quality_positive_roe_and_roa():
    info = {
        "returnOnEquity": 0.20,
        "returnOnAssets": 0.08,
        "debtToEquity": 40,
        "operatingMargins": 0.15,
        "freeCashflow": 100,
        "netIncomeToCommon": 80,
    }
    score, metrics = _score_quality(info)
    assert score > 50
    assert metrics["roe_pct"] == pytest.approx(20.0)
    assert metrics["roa_pct"] == pytest.approx(8.0)


def test_score_entry_penalizes_near_high():
    dates = pd.date_range("2025-01-01", periods=260, freq="B")
    near_high_close = [50.0] * 240 + [100.0] * 20
    mid_range_close = [50.0] * 100 + [100.0] * 100 + [75.0] * 60
    hist_high = pd.DataFrame({"Close": near_high_close}, index=dates)
    hist_mid = pd.DataFrame({"Close": mid_range_close}, index=dates)
    near_high, _ = _score_entry(hist_high)
    mid, _ = _score_entry(hist_mid)
    assert near_high < mid


def test_market_cap_filter_kr():
    small = UniverseSymbol("000001.KQ", "a", "a", "KOSDAQ", "KRW", market_cap=1_000_000_000)
    large = UniverseSymbol("005930.KS", "b", "b", "KOSPI", "KRW", market_cap=MIN_MARKET_CAP_KR)
    assert passes_market_cap_filter(small, "KR") is False
    assert passes_market_cap_filter(large, "KR") is True
    assert passes_market_cap_filter(small, "US", {"marketCap": 1_000_000_000}) is True


def test_passes_red_flags_negative_equity():
    assert passes_red_flags({"bookValue": -1, "priceToBook": -1}) is False


def test_passes_red_flags_negative_book_value_alone():
    assert passes_red_flags({"bookValue": -5, "priceToBook": 1.2}) is False


def test_passes_red_flags_missing_equity_fields_pass():
    assert passes_red_flags({}) is True
    assert passes_red_flags({"freeCashflow": 10, "operatingCashflow": 20}) is True


def test_passes_red_flags_dual_negative_cashflow():
    assert passes_red_flags({"freeCashflow": -1, "operatingCashflow": -1, "bookValue": 10}) is False


def test_passes_red_flags_clean_pass():
    assert passes_red_flags({"bookValue": 10, "priceToBook": 1.5, "freeCashflow": 5, "operatingCashflow": 8}) is True


def test_composite_threshold_is_documented():
    assert COMPOSITE_THRESHOLD == 70.0


def test_score_version_default_is_v2():
    assert SCORE_VERSION == 2
