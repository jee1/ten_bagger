"""Byte pin for daily entry assembly and the screen filter counters.

The fixtures were captured from the builders before the shared score and meta
helpers. A refactor that changes live selection JSON fails this file.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import generate_daily
import pandas as pd
from config import MIN_MARKET_CAP_KR, SCORE_VERSION, UniverseSymbol
from scoring.models import ScoreResult
from screening.core import ScreenStats, score_symbol, screen_market
from top_n import build_top_candidates

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "entry_builders"

_INFO = {
    "longName": "Apple Inc",
    "sector": "Technology",
    "industry": "Consumer Electronics",
    "longBusinessSummary": "Apple designs phones. It sells them worldwide.",
}


def _result(symbol: str) -> ScoreResult:
    return ScoreResult(
        symbol=symbol,
        meta=UniverseSymbol(symbol, "테스트", "Test Co", "NASDAQ", "USD"),
        size=80.0,
        growth=75.0,
        valuation=78.0,
        entry=70.0,
        momentum=65.0,
        quality=72.0,
        composite=76.5 if symbol == "AAPL" else 60.0,
        metrics={},
        score_version=SCORE_VERSION,
    )


def _stats() -> ScreenStats:
    return ScreenStats(
        screened=10,
        passed_threshold=1,
        skipped_recent=1,
        skipped_market_cap=2,
        skipped_red_flags=3,
        no_data=4,
        errors=0,
    )


def _dump(entry: dict) -> str:
    return json.dumps(entry, ensure_ascii=False, indent=2) + "\n"


def test_build_pick_and_no_pick_match_golden(monkeypatch):
    monkeypatch.setattr(
        generate_daily,
        "now_kst",
        lambda: datetime.fromisoformat("2026-07-08T06:00:00+09:00"),
    )
    monkeypatch.setattr(generate_daily, "get_ticker_info", lambda _symbol: dict(_INFO))
    pick = _result("AAPL")
    runner = _result("MSFT")
    tops = build_top_candidates([pick, runner])
    stats = _stats()

    assert _dump(generate_daily.build_pick("2026-07-08", "US", pick, stats, tops)) == (
        FIXTURES / "pick.json"
    ).read_text(encoding="utf-8")
    assert _dump(generate_daily.build_no_pick("2026-07-08", "US", stats, tops)) == (
        FIXTURES / "no_pick.json"
    ).read_text(encoding="utf-8")
    assert _dump(generate_daily.build_no_pick("2026-07-08", "US", stats, None)) == (
        FIXTURES / "no_pick_without_top.json"
    ).read_text(encoding="utf-8")


def _priced_info(symbol: str, **overrides) -> dict:
    info = {
        "symbol": symbol,
        "shortName": symbol,
        "marketCap": 5_000_000_000,
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
    }
    info.update(overrides)
    return info


def _flat_history(_symbol: str, period: str = "1y") -> pd.DataFrame:
    return pd.DataFrame({"Close": [100.0] * 40})


def test_screen_market_filter_counters_stay_put():
    universe = [
        UniverseSymbol("GOOD", "좋음", "Good", "NASDAQ", "USD", market_cap=5_000_000_000),
        UniverseSymbol("SMALL", "소형", "Small", "NASDAQ", "USD"),
        UniverseSymbol("BAD", "나쁨", "Bad", "NASDAQ", "USD", market_cap=5_000_000_000),
        UniverseSymbol("EMPTY", "빈", "Empty", "NASDAQ", "USD"),
    ]
    infos = {
        "GOOD": _priced_info("GOOD"),
        "SMALL": _priced_info("SMALL", marketCap=10_000_000),
        "BAD": _priced_info("BAD", bookValue=-1, priceToBook=-1),
        "EMPTY": {},
    }
    results, stats = screen_market(
        "US",
        set(),
        info_fn=lambda symbol: infos[symbol],
        history_fn=_flat_history,
        universe=universe,
    )
    assert [row.symbol for row in results] == ["GOOD"]
    assert stats.screened == 4
    assert stats.skipped_market_cap == 1
    assert stats.skipped_red_flags == 1
    assert stats.no_data == 1
    assert stats.errors == 0

    fetched: list[str] = []
    kr_universe = [
        UniverseSymbol("BIG.KS", "대", "Big", "KOSPI", "KRW", market_cap=MIN_MARKET_CAP_KR),
        UniverseSymbol(
            "TINY.KQ",
            "소",
            "Tiny",
            "KOSDAQ",
            "KRW",
            market_cap=MIN_MARKET_CAP_KR - 1,
        ),
    ]

    def kr_info(symbol: str) -> dict:
        fetched.append(symbol)
        return _priced_info(symbol)

    kr_results, kr_stats = screen_market(
        "KR",
        set(),
        info_fn=kr_info,
        history_fn=_flat_history,
        universe=kr_universe,
    )
    assert [row.symbol for row in kr_results] == ["BIG.KS"]
    assert fetched == ["BIG.KS"]
    assert kr_stats.screened == 1
    assert kr_stats.skipped_market_cap == 1
    assert kr_stats.no_data == 0
    assert kr_stats.errors == 0

    small = score_symbol(
        universe[1],
        "US",
        infos["SMALL"],
        history_fn=_flat_history,
    )
    flagged = score_symbol(
        universe[2],
        "US",
        infos["BAD"],
        history_fn=_flat_history,
    )
    assert small is not None and small.symbol == "SMALL"
    assert flagged is not None and flagged.symbol == "BAD"


def test_build_pick_reuses_screening_info(monkeypatch):
    monkeypatch.setattr(
        generate_daily,
        "now_kst",
        lambda: datetime.fromisoformat("2026-07-08T06:00:00+09:00"),
    )

    def refuse_refetch(_symbol: str) -> dict:
        raise AssertionError("refetch")

    monkeypatch.setattr(generate_daily, "get_ticker_info", refuse_refetch)
    pick = _result("AAPL")
    pick.info = dict(_INFO)
    runner = _result("MSFT")
    tops = build_top_candidates([pick, runner])
    entry = generate_daily.build_pick("2026-07-08", "US", pick, _stats(), tops)
    assert _dump(entry) == (FIXTURES / "pick.json").read_text(encoding="utf-8")
