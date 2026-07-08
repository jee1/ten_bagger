"""Tests for momentum scoring and reasoning output."""

from __future__ import annotations

import pandas as pd

from config import MAX_GROWTH_PCT, MIN_MARKET_CAP_US, UniverseSymbol
from screen import (
    ScoreResult,
    _score_momentum,
    build_reasoning,
    passes_market_cap_filter,
    score_symbol,
)


def test_score_momentum_recovery_zone():
    dates = pd.date_range("2025-01-01", periods=200, freq="B")
    close = [100.0] * 74 + [80.0] * 52 + [92.0] * 74
    hist = pd.DataFrame({"Close": close}, index=dates)
    score, metrics = _score_momentum(hist)
    assert score >= 35
    assert metrics["six_month_return_pct"] is not None
    assert metrics["from_52w_high_pct"] is not None


def test_score_momentum_insufficient_history():
    hist = pd.DataFrame({"Close": [1.0, 2.0, 3.0]})
    score, metrics = _score_momentum(hist)
    assert metrics["six_month_return_pct"] is None


def test_build_reasoning_v2_includes_size_and_entry():
    result = ScoreResult(
        symbol="TEST",
        meta=UniverseSymbol("TEST", "테스트", "Test Co", "NASDAQ", "USD"),
        size=80.0,
        growth=85.0,
        valuation=70.0,
        entry=65.0,
        momentum=55.0,
        quality=72.0,
        composite=75.0,
        metrics={
            "revenue_growth_pct": 30.0,
            "earnings_growth_pct": MAX_GROWTH_PCT,
            "blended_growth_pct": 35.0,
            "pe": 15.0,
            "peg": 1.0,
            "fcf_yield_pct": 6.0,
            "price_to_book": 1.2,
            "market_cap": 800_000_000,
            "twelve_month_range_pct": 45.0,
            "six_month_return_pct": 10.0,
            "from_52w_high_pct": -10.0,
            "roe_pct": 12.0,
            "roa_pct": 5.0,
            "fcf_to_net_income": 0.9,
        },
        score_version=2,
    )
    reasoning = build_reasoning(result)
    assert "v2" in reasoning["summary"]["ko"]
    assert reasoning["size"]["ko"]
    assert reasoning["entry"]["ko"]
    assert "100" not in reasoning["growth"]["ko"] or "혼합" in reasoning["growth"]["ko"]


def test_us_market_cap_filter():
    small = UniverseSymbol("PENNY", "a", "a", "NASDAQ", "USD")
    assert passes_market_cap_filter(small, "US", {"marketCap": 50_000_000}) is False
    assert passes_market_cap_filter(small, "US", {"marketCap": MIN_MARKET_CAP_US}) is True
    assert passes_market_cap_filter(small, "US", {}) is True


def test_score_symbol_skips_low_us_cap(monkeypatch):
    meta = UniverseSymbol("SMALL", "소형", "Small Inc", "NASDAQ", "USD")

    monkeypatch.setattr(
        "screen.get_ticker_info",
        lambda _symbol: {
            "symbol": "SMALL",
            "shortName": "Small Inc",
            "marketCap": 10_000_000,
            "revenueGrowth": 0.2,
            "earningsGrowth": 0.2,
            "trailingPE": 10,
            "pegRatio": 1,
            "returnOnEquity": 0.15,
            "debtToEquity": 50,
            "operatingMargins": 0.1,
            "bookValue": 5,
            "priceToBook": 1.2,
            "freeCashflow": 1_000_000,
            "operatingCashflow": 2_000_000,
        },
    )
    monkeypatch.setattr(
        "screen.get_ticker_history",
        lambda _symbol, period="1y": pd.DataFrame({"Close": [1.0] * 40}),
    )

    assert score_symbol(meta, "US") is None


def test_score_symbol_skips_red_flags(monkeypatch):
    meta = UniverseSymbol("BAD", "나쁨", "Bad Inc", "NASDAQ", "USD")

    monkeypatch.setattr(
        "screen.get_ticker_info",
        lambda _symbol: {
            "symbol": "BAD",
            "shortName": "Bad Inc",
            "marketCap": 500_000_000,
            "bookValue": -1,
            "priceToBook": -1,
        },
    )
    monkeypatch.setattr(
        "screen.get_ticker_history",
        lambda _symbol, period="1y": pd.DataFrame({"Close": [1.0] * 40}),
    )

    assert score_symbol(meta, "US") is None
