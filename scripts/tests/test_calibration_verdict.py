"""Calibration verdict tests."""

from __future__ import annotations

from calibration.verdict import overall_verdict, verdict_from_oos_report


def _wf(*, picks: int, excess: float | None, intent: str = "go_evidence") -> dict:
    return {
        "runIntent": intent,
        "coverage": {
            "oosPickDays": picks,
            "noPickDays": 5,
            "noPickRatio": 5 / (picks + 5) if picks else 1.0,
            "insufficientCoverage": intent == "go_evidence" and picks < 20,
        },
        "aggregate": {
            "horizons": [
                {
                    "horizonId": "H20",
                    "excessReturnMean": excess,
                    "status": "complete",
                },
                {
                    "horizonId": "H60",
                    "excessReturnMean": excess,
                    "status": "complete",
                },
            ]
        },
    }


def test_go_when_coverage_and_positive_excess():
    entry = verdict_from_oos_report(
        _wf(picks=25, excess=0.01),
        candidate_id="c1",
        walk_forward_report_path="walk-forward/x.json",
        walk_forward_config_hash="a" * 64,
    )
    assert entry["verdict"] == "GO"
    assert entry["failedBullets"] == []


def test_nogo_insufficient_coverage():
    entry = verdict_from_oos_report(
        _wf(picks=5, excess=0.5),
        candidate_id="c1",
        walk_forward_report_path="p",
        walk_forward_config_hash="a" * 64,
    )
    assert entry["verdict"] == "NO-GO"
    assert "insufficient_coverage" in entry["failedBullets"]


def test_nogo_non_positive_excess():
    entry = verdict_from_oos_report(
        _wf(picks=25, excess=0.0),
        candidate_id="c1",
        walk_forward_report_path="p",
        walk_forward_config_hash="a" * 64,
    )
    assert entry["verdict"] == "NO-GO"


def test_no_pick_alone_does_not_fail():
    report = _wf(picks=25, excess=0.02)
    report["coverage"]["noPickRatio"] = 0.9
    entry = verdict_from_oos_report(
        report,
        candidate_id="c1",
        walk_forward_report_path="p",
        walk_forward_config_hash="a" * 64,
    )
    assert entry["verdict"] == "GO"


def test_overall_incomplete():
    v, failed = overall_verdict([], package_intent="go_evidence", incomplete=True)
    assert v == "NO-GO"
    assert any("incomplete" in b for b in failed)


def test_overall_na_for_exploratory():
    v, _ = overall_verdict([], package_intent="exploratory")
    assert v == "N/A"
