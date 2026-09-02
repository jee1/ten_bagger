"""Aggregate metrics tests for walk-forward reports."""

from __future__ import annotations

from walk_forward.aggregate import aggregate_fold_horizons, aggregate_report


def _measurement(
    *,
    pick_date: str = "2026-01-05",
    forward: float = 0.10,
    benchmark: float = 0.05,
    complete: bool = True,
) -> dict:
    status = "complete" if complete else "incomplete"
    row = {
        "market": "KR",
        "pickDate": pick_date,
        "symbol": "SIMPLE.KR",
        "horizonId": "H20",
        "benchmarkId": "KR-KOSPI",
        "completionStatus": status,
        "benchmarkCompletionStatus": status,
        "survivorshipFlag": "listed",
        "asOfDate": "2026-02-28",
    }
    if complete:
        row["forwardReturn"] = forward
        row["benchmarkReturn"] = benchmark
    return row


def test_pick_return_mean_excludes_no_pick_days():
    measurements = [
        _measurement(forward=0.10, benchmark=0.05),
        _measurement(pick_date="2026-01-07", forward=-0.02, benchmark=0.01),
    ]
    horizons = aggregate_fold_horizons(measurements, market="KR")
    h20 = next(h for h in horizons if h["horizonId"] == "H20")
    assert h20["pickReturnMean"] == 0.04
    assert h20["sampleCount"] == 2


def test_hit_rate_and_excess_return():
    measurements = [
        _measurement(forward=0.10, benchmark=0.05),
        _measurement(pick_date="2026-01-07", forward=-0.02, benchmark=-0.01),
    ]
    h20 = aggregate_fold_horizons(measurements, market="KR")[0]
    assert h20["hitRate"] == 0.5
    assert h20["excessReturnMean"] == 0.02


def test_insufficient_coverage_for_go_evidence():
    folds = [
        {"pickDays": 5, "noPickDays": 3, "measurements": [_measurement()]},
        {"pickDays": 10, "noPickDays": 2, "measurements": [_measurement()]},
    ]
    _, coverage = aggregate_report(folds, "go_evidence")
    assert coverage["oosPickDays"] == 15
    assert coverage["insufficientCoverage"] is True


def test_insufficient_coverage_false_for_exploratory():
    folds = [{"pickDays": 1, "noPickDays": 0, "measurements": [_measurement()]}]
    _, coverage = aggregate_report(folds, "exploratory")
    assert coverage["insufficientCoverage"] is False


def test_incomplete_horizon_status_in_aggregate():
    measurements = [_measurement(complete=False)]
    h20 = aggregate_fold_horizons(measurements, market="KR")[0]
    assert h20["status"] == "incomplete"
    assert h20["pickReturnMean"] is None
