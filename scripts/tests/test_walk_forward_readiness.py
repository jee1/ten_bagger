"""Search go_evidence readiness (#91 / 030)."""

from __future__ import annotations

import json
from pathlib import Path

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


def test_not_ready_when_fewer_than_40_h20_complete(tmp_path):
    dates = [f"2026-01-{i:02d}" for i in range(1, 31)]  # 30 days
    perf = _write_perf(tmp_path, dates)
    report = assess_search_go_evidence_readiness(
        as_of_date="2026-09-05",
        markets=["KR"],
        performance_dir=perf,
    )
    assert report["status"] == "not_ready"
    assert report["h20CompletePickDays"] == 30
    assert report["projectedOosPickDays"] is None or report["projectedOosPickDays"] < 20
    assert any("40" in r or "both" in r.lower() or "carve" in r.lower() for r in report["reasons"])


def test_ready_when_at_least_40_h20_complete(tmp_path):
    dates = [f"2026-01-{i:02d}" for i in range(1, 32)] + [
        f"2026-02-{i:02d}" for i in range(1, 10)
    ]  # 31+9=40
    perf = _write_perf(tmp_path, dates)
    report = assess_search_go_evidence_readiness(
        as_of_date="2026-09-05",
        markets=["KR"],
        performance_dir=perf,
    )
    assert report["status"] == "ready"
    assert report["h20CompletePickDays"] == 40
    assert report["projectedOosPickDays"] >= 20
    assert report["proposedIs"] is not None
    assert report["proposedOos"] is not None
    assert report["proposedIs"]["endDate"] < report["proposedOos"]["startDate"]


def test_readiness_deterministic(tmp_path):
    dates = [f"2026-03-{i:02d}" for i in range(1, 41)]
    perf = _write_perf(tmp_path, dates)
    a = assess_search_go_evidence_readiness(
        as_of_date="2026-09-05", markets=["KR"], performance_dir=perf
    )
    b = assess_search_go_evidence_readiness(
        as_of_date="2026-09-05", markets=["KR"], performance_dir=perf
    )
    assert a == b
