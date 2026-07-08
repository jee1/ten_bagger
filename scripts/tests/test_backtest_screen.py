#!/usr/bin/env python3
"""Backtest screen comparison tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from backtest_screen import snapshot
from config import UniverseSymbol
from screen import ScoreResult


def _fake_result(symbol: str, composite: float, market_cap: int, fcf_yield: float) -> ScoreResult:
    return ScoreResult(
        symbol=symbol,
        meta=UniverseSymbol(symbol, symbol, symbol, "NASDAQ", "USD"),
        size=80.0,
        growth=70.0,
        valuation=75.0,
        entry=60.0,
        momentum=55.0,
        quality=65.0,
        composite=composite,
        metrics={"market_cap": market_cap, "fcf_yield_pct": fcf_yield},
        score_version=2,
    )


def test_snapshot_structure_without_universe():
    with patch("backtest_screen.screen_market") as mock_screen:
        mock_screen.return_value = (
            [],
            type(
                "S",
                (),
                {
                    "screened": 0,
                    "passed_threshold": 0,
                    "skipped_red_flags": 0,
                },
            )(),
        )
        data = snapshot("US", 2, 3)
    assert data["version"] == 2
    assert data["market"] == "US"
    assert "top_symbols" in data


def test_snapshot_passes_score_version_and_summarizes_top():
    results = [
        _fake_result("AAA", 90.0, 400_000_000, 8.0),
        _fake_result("BBB", 85.0, 600_000_000, 6.0),
        _fake_result("CCC", 80.0, 800_000_000, 4.0),
    ]
    stats = MagicMock(screened=100, passed_threshold=3, skipped_red_flags=7)

    with patch("backtest_screen.screen_market", return_value=(results, stats)) as mock_screen:
        data = snapshot("US", 2, 2)

    mock_screen.assert_called_once_with("US", set(), score_version=2)
    assert data["passed_threshold"] == 3
    assert data["skipped_red_flags"] == 7
    assert data["median_market_cap_top"] == 500_000_000
    assert data["avg_fcf_yield_top"] == 7.0
    assert [item["symbol"] for item in data["top_symbols"]] == ["AAA", "BBB"]
