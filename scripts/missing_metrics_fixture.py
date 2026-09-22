"""Build a generate_daily pick entry with missing price metrics for render regression."""

from __future__ import annotations

import json
import math

import generate_daily
from config import ENTRY_DEFAULT_SCORE, MOMENTUM_DEFAULT_SCORE, UniverseSymbol
from generate_daily import build_pick
from scoring.models import ScoreResult
from screen import ScreenStats


def build_missing_metrics_pick_entry() -> dict:
    generate_daily.get_ticker_info = lambda _symbol: {"longName": "Test Co"}
    generate_daily.build_stock_profile = lambda *_args, **_kwargs: None

    result = ScoreResult(
        symbol="TEST",
        meta=UniverseSymbol("TEST", "테스트", "Test Co", "NASDAQ", "USD"),
        size=80.0,
        growth=85.0,
        valuation=70.0,
        entry=ENTRY_DEFAULT_SCORE,
        momentum=MOMENTUM_DEFAULT_SCORE,
        quality=72.0,
        composite=84.3,
        metrics={
            "revenue_growth_pct": 10.0,
            "earnings_growth_pct": 20.0,
            "blended_growth_pct": 14.0,
            "pe": None,
            "peg": math.nan,
            "fcf_yield_pct": 5.0,
            "price_to_book": None,
            "market_cap": 800_000_000,
            "twelve_month_range_pct": None,
            "from_52w_high_pct": math.nan,
            "six_month_return_pct": math.nan,
            "roe_pct": 10.0,
            "roa_pct": 5.0,
            "fcf_to_net_income": 1.2,
        },
        score_version=2,
    )
    stats = ScreenStats(screened=1, passed_threshold=1)
    return build_pick("2026-09-23", "US", result, stats)


def main() -> int:
    print(json.dumps(build_missing_metrics_pick_entry(), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
