"""Stage 0 (#175): non-PIT fundamentals contamination on override re-screen."""

from __future__ import annotations

from calibration.verdict import verdict_from_oos_report
from walk_forward.config import RunConfig
from walk_forward.fundamentals_pit import fundamentals_pit_available
from walk_forward.report import build_report

FOLD_SPEC = {
    "mode": "rolling",
    "trainSessions": 4,
    "oosSessions": 2,
    "stepSessions": 2,
    "startDate": "2025-01-01",
    "endDate": "2025-01-31",
}

VALID_WEIGHT_OVERRIDES = {
    "WEIGHT_SIZE": 0.15,
    "WEIGHT_VALUATION": 0.20,
    "WEIGHT_GROWTH": 0.20,
    "WEIGHT_QUALITY": 0.25,
    "WEIGHT_ENTRY": 0.10,
    "WEIGHT_MOMENTUM": 0.10,
}

FOLD_RESULTS = [
    {
        "foldIndex": 0,
        "trainRange": {"start": "2025-01-01", "end": "2025-01-06"},
        "oosRange": {"start": "2025-01-07", "end": "2025-01-08"},
        "trainSessions": ["2025-01-01", "2025-01-03", "2025-01-06", "2025-01-08"],
        "oosSessions": ["2025-01-09", "2025-01-10"],
        "status": "complete",
        "pickDays": 1,
        "noPickDays": 1,
        "picks": [],
        "measurements": [],
        "horizons": [],
    },
]


def _positive_oos_wf(report: dict) -> dict:
    report = dict(report)
    report["coverage"] = {
        "oosPickDays": 25,
        "noPickDays": 0,
        "noPickRatio": 0.0,
        "insufficientCoverage": False,
    }
    report["aggregate"] = {
        "horizons": [
            {"horizonId": "H20", "excessReturnMean": 0.05, "status": "complete"},
            {"horizonId": "H60", "excessReturnMean": 0.05, "status": "complete"},
        ]
    }
    return report


def test_override_rescreen_emits_contamination_and_verdict_nogo():
    cfg = RunConfig(
        runIntent="exploratory",
        measurementSource="fixture-recompute",
        candidateId="growth-candidate",
        markets=["KR"],
        foldSpec=FOLD_SPEC,
        weightOverrides=VALID_WEIGHT_OVERRIDES,
    )
    report = build_report(
        run_config=cfg,
        fold_results=FOLD_RESULTS,
        run_id="pit-stage0",
        generated_at="2026-10-04T23:59:59Z",
    )
    # KR-only run: odd calendar days only (3 of 6 sessions in FOLD_RESULTS).
    assert report["contaminationFindings"] == ["fundamentals_not_pit:3"]

    entry = verdict_from_oos_report(
        _positive_oos_wf(report),
        candidate_id="growth-candidate",
        walk_forward_report_path="walk-forward/pit-stage0.json",
        walk_forward_config_hash="a" * 64,
    )
    assert entry["verdict"] == "NO-GO"
    assert "contamination" in entry["failedBullets"]
    assert entry["contaminationFindings"] == ["fundamentals_not_pit:3"]


def test_ledger_path_no_contamination_finding():
    cfg = RunConfig(
        runIntent="go_evidence",
        measurementSource="ledger",
        candidateId="score-v2-baseline",
        markets=["KR", "US"],
        foldSpec=FOLD_SPEC,
    )
    report = build_report(
        run_config=cfg,
        fold_results=FOLD_RESULTS,
        run_id="ledger-run",
        generated_at="2026-10-04T23:59:59Z",
    )
    assert "contaminationFindings" not in report


def test_no_finding_when_fundamentals_pit_available(monkeypatch):
    monkeypatch.setattr(
        "walk_forward.fundamentals_pit.fundamentals_pit_available",
        lambda _m, _d: True,
    )
    cfg = RunConfig(
        runIntent="exploratory",
        measurementSource="fixture-recompute",
        candidateId="growth-candidate",
        markets=["KR"],
        foldSpec=FOLD_SPEC,
        thresholdOverride=75.0,
    )
    report = build_report(
        run_config=cfg,
        fold_results=FOLD_RESULTS,
        run_id="pit-clean",
        generated_at="2026-10-04T23:59:59Z",
    )
    assert "contaminationFindings" not in report


def test_fundamentals_pit_available_default_false():
    assert fundamentals_pit_available("KR", "2026-01-08") is False
