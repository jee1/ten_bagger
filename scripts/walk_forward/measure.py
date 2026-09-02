"""OOS pick measurement for walk-forward folds."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd
from performance.returns import BENCHMARK_IDS, measure_pick_horizon
from tests.fixtures.price_loader import load_price_fixture

from walk_forward.config import RunConfig
from walk_forward.ledger_loader import load_performance_index, lookup_measurement

WALK_FORWARD_HORIZONS = ("H20", "H60")

PriceProvider = Callable[[str, str], pd.DataFrame]
BenchmarkProvider = Callable[[str], pd.DataFrame | None]

_FIXTURE_MAP: dict[str, str] = {
    "SIMPLE.KR": "simple_kr_h20",
    "SIMPLE.US": "simple_us_h20",
    "LOOKAHEAD.KR": "lookahead_kr",
}


def fixture_price_provider(_as_of_date: str) -> PriceProvider:
    def provider(symbol: str, _market: str) -> pd.DataFrame:
        fixture_name = _FIXTURE_MAP.get(symbol, "simple_kr_h20")
        return load_price_fixture(fixture_name)

    return provider


def fixture_benchmark_provider(_as_of_date: str) -> BenchmarkProvider:
    def provider(benchmark_id: str) -> pd.DataFrame | None:
        if benchmark_id == "KR-KOSPI":
            return load_price_fixture("benchmark_kr")
        if benchmark_id == "US-SPX":
            return load_price_fixture("benchmark_us")
        return None

    return provider


def measure_oos_picks(
    picks: list[dict[str, Any]],
    run_config: RunConfig,
    as_of_date: str,
    price_provider: PriceProvider,
    benchmark_provider: BenchmarkProvider,
) -> list[dict[str, Any]]:
    """Measure H20/H60 for each OOS pick (fixture-recompute or ledger lookup)."""
    if run_config.measurementSource == "ledger":
        perf_dir = run_config.performanceDir or Path("content/performance")
        index = load_performance_index(perf_dir)
        measurements: list[dict[str, Any]] = []
        for pick in picks:
            for horizon_id in WALK_FORWARD_HORIZONS:
                row = lookup_measurement(
                    index,
                    pick_date=pick["pickDate"],
                    symbol=pick["symbol"],
                    horizon_id=horizon_id,
                    run_intent=run_config.runIntent,
                )
                if row is None:
                    measurements.append(_missing_measurement_row(pick, horizon_id, as_of_date))
                else:
                    measurements.append(row)
        return measurements

    measurements = []
    for pick in picks:
        market = pick["market"]
        symbol = pick["symbol"]
        bars = price_provider(symbol, market)
        bench_id = BENCHMARK_IDS[market]
        benchmark_bars = benchmark_provider(bench_id)
        for horizon_id in WALK_FORWARD_HORIZONS:
            measurements.append(
                measure_pick_horizon(
                    bars=bars,
                    benchmark_bars=benchmark_bars,
                    pick_date=pick["pickDate"],
                    as_of_date=as_of_date,
                    market=market,
                    symbol=symbol,
                    horizon_id=horizon_id,
                )
            )
    return measurements


def _missing_measurement_row(
    pick: dict[str, Any], horizon_id: str, as_of_date: str
) -> dict[str, Any]:
    market = pick["market"]
    return {
        "market": market,
        "pickDate": pick["pickDate"],
        "symbol": pick["symbol"],
        "horizonId": horizon_id,
        "benchmarkId": BENCHMARK_IDS[market],
        "completionStatus": "incomplete",
        "benchmarkCompletionStatus": "incomplete",
        "survivorshipFlag": "unknown",
        "asOfDate": as_of_date,
        "incompleteReason": "missing_ledger_row",
    }
