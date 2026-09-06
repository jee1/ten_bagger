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


def _has_analysis_overrides(run_config: RunConfig) -> bool:
    return bool(run_config.weightOverrides) or run_config.thresholdOverride is not None


def _recompute_pick_horizons(
    pick: dict[str, Any],
    as_of_date: str,
    price_provider: PriceProvider,
    benchmark_provider: BenchmarkProvider,
) -> list[dict[str, Any]]:
    market = pick["market"]
    symbol = pick["symbol"]
    bars = price_provider(symbol, market)
    bench_id = BENCHMARK_IDS[market]
    benchmark_bars = benchmark_provider(bench_id)
    return [
        measure_pick_horizon(
            bars=bars,
            benchmark_bars=benchmark_bars,
            pick_date=pick["pickDate"],
            as_of_date=as_of_date,
            market=market,
            symbol=symbol,
            horizon_id=horizon_id,
        )
        for horizon_id in WALK_FORWARD_HORIZONS
    ]


def measure_oos_picks(
    picks: list[dict[str, Any]],
    run_config: RunConfig,
    as_of_date: str,
    price_provider: PriceProvider,
    benchmark_provider: BenchmarkProvider,
) -> list[dict[str, Any]]:
    """Measure H20/H60 for each OOS pick (fixture-recompute or ledger lookup).

    When ``measurementSource=ledger`` and analysis overrides are present, missing
    ledger rows fall back to ADR-aligned price recompute (#91). Published
    baseline (no overrides) keeps strict go_evidence ledger behavior.
    """
    if run_config.measurementSource == "ledger":
        perf_dir = run_config.performanceDir or Path("content/performance")
        index = load_performance_index(perf_dir)
        allow_recompute = _has_analysis_overrides(run_config)
        measurements: list[dict[str, Any]] = []
        for pick in picks:
            recomputed: dict[str, dict[str, Any]] | None = None
            for horizon_id in WALK_FORWARD_HORIZONS:
                soft_intent = "exploratory" if allow_recompute else run_config.runIntent
                row = lookup_measurement(
                    index,
                    pick_date=pick["pickDate"],
                    symbol=pick["symbol"],
                    horizon_id=horizon_id,
                    run_intent=soft_intent,
                )
                if row is not None:
                    measurements.append(row)
                    continue
                if allow_recompute:
                    if recomputed is None:
                        recomputed = {
                            m["horizonId"]: m
                            for m in _recompute_pick_horizons(
                                pick, as_of_date, price_provider, benchmark_provider
                            )
                        }
                    measurements.append(recomputed[horizon_id])
                else:
                    measurements.append(
                        _missing_measurement_row(pick, horizon_id, as_of_date)
                    )
        return measurements

    measurements = []
    for pick in picks:
        measurements.extend(
            _recompute_pick_horizons(pick, as_of_date, price_provider, benchmark_provider)
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
