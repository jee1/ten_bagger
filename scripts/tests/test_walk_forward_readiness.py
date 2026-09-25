"""Search go_evidence readiness (#91 / 030)."""

from __future__ import annotations

import json
from pathlib import Path

from walk_forward.folds import build_decision_sessions
from walk_forward.readiness import assess_search_go_evidence_readiness


def _write_perf(tmp_path: Path, pick_dates: list[str]) -> Path:
    perf_dir = tmp_path / "performance"
    perf_dir.mkdir()
    measurements = []
    for d in pick_dates:
        for horizon in ("H20", "H60"):
            measurements.append(
                {
                    "market": "KR",
                    "pickDate": d,
                    "symbol": f"T{d}.KR",
                    "horizonId": horizon,
                    "benchmarkId": "KR-KOSPI",
                    "completionStatus": "complete" if horizon == "H20" else "incomplete",
                    "benchmarkCompletionStatus": "complete",
                    "survivorshipFlag": "listed",
                    "asOfDate": "2026-09-05",
                }
            )
    (perf_dir / "KR.json").write_text(
        json.dumps({"measurements": measurements}),
        encoding="utf-8",
    )
    return perf_dir


def _aligned_sessions(start: str, end: str, count: int) -> list[str]:
    sessions = build_decision_sessions(start, end, ["KR"])
    return sessions[:count]


def test_not_ready_when_fewer_than_40_aligned_h20_complete(tmp_path):
    dates = _aligned_sessions("2026-01-01", "2026-03-31", 30)
    perf = _write_perf(tmp_path, dates)
    report = assess_search_go_evidence_readiness(
        as_of_date="2026-09-05",
        markets=["KR"],
        performance_dir=perf,
    )
    assert report["status"] == "not_ready"
    assert report["h20CompleteAlignedPickDays"] == 30
    assert report["projectedOosPickDays"] is None or report["projectedOosPickDays"] < 20
    assert any("40" in r or "aligned" in r.lower() for r in report["reasons"])


def test_not_ready_when_weekend_pick_days_do_not_fill_carve(tmp_path):
    weekdays = _aligned_sessions("2026-01-01", "2026-04-30", 35)
    weekends = [
        "2026-01-04",
        "2026-01-11",
        "2026-01-12",
        "2026-01-18",
        "2026-01-19",
        "2026-01-25",
    ]
    all_dates = sorted(set(weekdays + weekends))
    perf = _write_perf(tmp_path, all_dates)
    report = assess_search_go_evidence_readiness(
        as_of_date="2026-09-05",
        markets=["KR"],
        performance_dir=perf,
    )
    assert report["h20CompletePickDays"] == len(all_dates)
    assert report["h20CompleteAlignedPickDays"] == len(weekdays)
    assert report["status"] == "not_ready"


def test_ready_when_at_least_40_aligned_h20_complete(tmp_path):
    # OOS carve needs >20 decision sessions once rolling train overhead is applied.
    dates = _aligned_sessions("2025-01-01", "2025-08-31", 65)
    perf = _write_perf(tmp_path, dates)
    is_dates = dates[:45]
    oos_dates = dates[45:65]
    report = assess_search_go_evidence_readiness(
        as_of_date="2026-09-05",
        markets=["KR"],
        performance_dir=perf,
        is_fold_spec={
            "mode": "rolling",
            "trainSessions": 6,
            "oosSessions": 2,
            "stepSessions": 2,
            "startDate": is_dates[0],
            "endDate": is_dates[-1],
        },
        oos_fold_spec={
            "mode": "rolling",
            "trainSessions": 6,
            "oosSessions": 2,
            "stepSessions": 2,
            "startDate": oos_dates[0],
            "endDate": oos_dates[-1],
        },
    )
    assert report["status"] == "ready"
    assert report["h20CompleteAlignedPickDays"] >= 45
    assert report["projectedOosPickDays"] >= 20
    assert report["proposedIs"] is not None
    assert report["proposedOos"] is not None
    assert report["proposedIs"]["endDate"] < report["proposedOos"]["startDate"]


def test_not_ready_when_fold_spec_structural_ceiling_below_20(tmp_path):
    dates = _aligned_sessions("2026-01-01", "2026-04-30", 40)
    perf = _write_perf(tmp_path, dates)
    is_dates = dates[:20]
    oos_dates = dates[20:40]
    oos = assess_search_go_evidence_readiness(
        as_of_date="2026-09-05",
        markets=["KR"],
        performance_dir=perf,
        is_fold_spec={
            "mode": "rolling",
            "trainSessions": 6,
            "oosSessions": 3,
            "stepSessions": 3,
            "startDate": is_dates[0],
            "endDate": is_dates[-1],
        },
        oos_fold_spec={
            "mode": "rolling",
            "trainSessions": 6,
            "oosSessions": 3,
            "stepSessions": 3,
            "startDate": oos_dates[0],
            "endDate": oos_dates[-1],
        },
    )
    assert oos["status"] == "not_ready"
    assert oos["projectedOosPickDays"] is not None
    assert oos["projectedOosPickDays"] < 20
    assert any("walk-forward" in r.lower() for r in oos["reasons"])


def test_readiness_deterministic(tmp_path):
    dates = _aligned_sessions("2026-03-01", "2026-06-30", 45)
    perf = _write_perf(tmp_path, dates)
    a = assess_search_go_evidence_readiness(
        as_of_date="2026-09-05", markets=["KR"], performance_dir=perf
    )
    b = assess_search_go_evidence_readiness(
        as_of_date="2026-09-05", markets=["KR"], performance_dir=perf
    )
    assert a == b
