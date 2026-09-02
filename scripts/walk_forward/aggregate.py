"""Aggregate walk-forward fold metrics and coverage."""

from __future__ import annotations

from typing import Any

from performance.returns import BENCHMARK_IDS
from walk_forward.measure import WALK_FORWARD_HORIZONS

GO_EVIDENCE_MIN_PICK_DAYS = 20


def _horizon_metrics(
    measurements: list[dict[str, Any]],
    *,
    horizon_id: str,
    market: str,
) -> dict[str, Any]:
    rows = [
        m
        for m in measurements
        if m.get("horizonId") == horizon_id and m.get("market") == market
    ]
    complete = [m for m in rows if m.get("completionStatus") == "complete"]
    sample_count = len(complete)
    status = "complete" if rows and sample_count == len(rows) else "incomplete"

    pick_return_mean: float | None = None
    hit_rate: float | None = None
    excess_return_mean: float | None = None

    if complete:
        returns = [float(m["forwardReturn"]) for m in complete]
        pick_return_mean = sum(returns) / len(returns)
        hit_rate = sum(1 for r in returns if r > 0) / len(returns)
        excess: list[float] = []
        for m in complete:
            if m.get("benchmarkCompletionStatus") == "complete":
                excess.append(float(m["forwardReturn"]) - float(m["benchmarkReturn"]))
        if excess:
            excess_return_mean = sum(excess) / len(excess)

    return {
        "horizonId": horizon_id,
        "benchmarkId": BENCHMARK_IDS[market],
        "market": market,
        "pickReturnMean": pick_return_mean,
        "hitRate": hit_rate,
        "excessReturnMean": excess_return_mean,
        "status": status,
        "sampleCount": sample_count,
    }


def aggregate_fold_horizons(
    measurements: list[dict[str, Any]], market: str | None = None
) -> list[dict[str, Any]]:
    """Build per-fold H20/H60 metrics for one market (or all markets present)."""
    markets = {market} if market else {m.get("market") for m in measurements if m.get("market")}
    horizons: list[dict[str, Any]] = []
    for mkt in sorted(markets):
        for horizon_id in WALK_FORWARD_HORIZONS:
            horizons.append(_horizon_metrics(measurements, horizon_id=horizon_id, market=mkt))
    return horizons


def aggregate_report(
    fold_results: list[dict[str, Any]], run_intent: str
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Cross-fold aggregate horizons and coverage block."""
    all_measurements: list[dict[str, Any]] = []
    oos_pick_days = 0
    no_pick_days = 0

    for fold in fold_results:
        oos_pick_days += fold.get("pickDays", 0)
        no_pick_days += fold.get("noPickDays", 0)
        all_measurements.extend(fold.get("measurements") or [])

    aggregate_horizons = aggregate_fold_horizons(all_measurements)
    total_oos = oos_pick_days + no_pick_days
    no_pick_ratio = no_pick_days / total_oos if total_oos else 1.0
    insufficient = run_intent == "go_evidence" and oos_pick_days < GO_EVIDENCE_MIN_PICK_DAYS

    coverage = {
        "oosPickDays": oos_pick_days,
        "noPickDays": no_pick_days,
        "noPickRatio": no_pick_ratio,
        "insufficientCoverage": insufficient,
    }
    return aggregate_horizons, coverage


def enrich_fold_results(fold_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attach per-fold horizon metrics to runner output."""
    enriched: list[dict[str, Any]] = []
    for fold in fold_results:
        measurements = fold.get("measurements") or []
        horizons = aggregate_fold_horizons(measurements)
        enriched.append({**fold, "horizons": horizons})
    return enriched
