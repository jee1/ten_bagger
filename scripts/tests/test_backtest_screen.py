#!/usr/bin/env python3
"""Backtest screen comparison tests."""

from __future__ import annotations

import json
from unittest.mock import patch

from backtest_screen import snapshot


def test_snapshot_structure_without_universe():
    with patch("backtest_screen.screen_market") as mock_screen:
        mock_screen.return_value = ([], type("S", (), {
            "screened": 0,
            "passed_threshold": 0,
            "skipped_red_flags": 0,
        })())
        data = snapshot("US", 2, 3)
    assert data["version"] == 2
    assert data["market"] == "US"
    assert "top_symbols" in data
