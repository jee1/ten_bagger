"""PIT screening tests — post-t bars must not affect selection."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from config import UniverseSymbol
from tests.fixtures.price_loader import load_price_fixture
from walk_forward.pit_screen import pit_screen_day

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "walk_forward"
UNIVERSE = FIXTURES / "universe" / "kr.json"


def _good_info(symbol: str) -> dict:
    return {
        "symbol": symbol,
        "shortName": symbol,
        "marketCap": 500_000_000_000,
        "revenueGrowth": 0.25,
        "earningsGrowth": 0.20,
        "trailingPE": 15,
        "pegRatio": 1.0,
        "returnOnEquity": 0.15,
        "debtToEquity": 50,
        "operatingMargins": 0.12,
        "bookValue": 100,
        "priceToBook": 1.5,
        "freeCashflow": 1_000_000,
        "operatingCashflow": 2_000_000,
    }


def _load_test_universe(_market: str) -> list[UniverseSymbol]:
    raw = json.loads(UNIVERSE.read_text(encoding="utf-8"))
    return [
        UniverseSymbol(
            symbol=item["symbol"],
            name_ko=item["name_ko"],
            name_en=item["name_en"],
            exchange=item["exchange"],
            currency=item["currency"],
            market_cap=item.get("market_cap"),
        )
        for item in raw
    ]


def _history_for_symbol(symbol: str, period: str = "1y") -> pd.DataFrame:
    if symbol == "LOOKAHEAD.KR":
        return load_price_fixture("lookahead_kr")
    dates = pd.date_range("2025-06-01", periods=200, freq="B")
    close = [100.0] * 74 + [80.0] * 52 + [92.0] * 74
    return pd.DataFrame({"Close": close}, index=dates)


def test_pit_screen_excludes_post_t_bars(monkeypatch):
    """Contaminated post-t momentum must not change the top pick."""
    monkeypatch.setattr("screening.core.load_universe", _load_test_universe)
    monkeypatch.setattr("screening.core.get_ticker_info", lambda s: _good_info(s))
    monkeypatch.setattr("screening.core.get_ticker_history", _history_for_symbol)

    as_of = "2026-01-08"
    symbol, no_pick = pit_screen_day("KR", as_of, set())
    assert not no_pick
    assert symbol == "GOOD.KR"


def test_pit_screen_no_pick_when_below_threshold(monkeypatch):
    monkeypatch.setattr("screening.core.load_universe", _load_test_universe)
    monkeypatch.setattr("screening.core.get_ticker_info", lambda s: _good_info(s))
    monkeypatch.setattr(
        "screening.core.get_ticker_history",
        lambda _s, period="1y": pd.DataFrame({"Close": [1.0] * 5}),
    )
    monkeypatch.setattr("screening.core.COMPOSITE_THRESHOLD", 999.0)

    symbol, no_pick = pit_screen_day("KR", "2026-01-08", set())
    assert symbol is None
    assert no_pick
