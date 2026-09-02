"""Walk-forward report builder and serialization tests."""

from __future__ import annotations

from walk_forward.config import RunConfig, config_hash
from walk_forward.report import SCHEMA_VERSION, build_report, serialize_report

FOLD_SPEC = {
    "mode": "rolling",
    "trainSessions": 4,
    "oosSessions": 2,
    "stepSessions": 2,
    "startDate": "2025-01-01",
    "endDate": "2025-01-31",
}

RUN_CONFIG = RunConfig(
    runIntent="exploratory",
    measurementSource="fixture-recompute",
    candidateId="score-v2-baseline",
    markets=["KR", "US"],
    foldSpec=FOLD_SPEC,
    weightOverrides=None,
)

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

REQUIRED_TOP_LEVEL = [
    "schemaVersion",
    "runId",
    "runIntent",
    "measurementSource",
    "configHash",
    "generatedAt",
    "candidateId",
    "foldSpec",
    "folds",
    "aggregate",
    "coverage",
]


def test_build_report_has_required_top_level_fields():
    report = build_report(
        run_config=RUN_CONFIG,
        fold_results=FOLD_RESULTS,
        run_id="test-run-001",
        generated_at="2025-09-01T12:00:00Z",
    )
    for key in REQUIRED_TOP_LEVEL:
        assert key in report
    assert report["schemaVersion"] == SCHEMA_VERSION
    assert report["configHash"] == config_hash(RUN_CONFIG)


def test_serialize_report_is_deterministic():
    report = build_report(
        run_config=RUN_CONFIG,
        fold_results=FOLD_RESULTS,
        run_id="test-run-001",
        generated_at="2025-09-01T12:00:00Z",
    )
    b1 = serialize_report(report)
    b2 = serialize_report(report)
    assert b1 == b2
    assert isinstance(b1, bytes)
