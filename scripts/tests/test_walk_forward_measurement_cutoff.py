"""Regression: measurementAsOfDate propagates beyond foldSpec.endDate (#93)."""

from __future__ import annotations

from walk_forward.config import RunConfig, config_hash, effective_measurement_as_of
from walk_forward.execute import generated_at_from_config
from walk_forward.runner import run_folds

FOLD_SPEC = {
    "mode": "rolling",
    "trainSessions": 2,
    "oosSessions": 1,
    "stepSessions": 1,
    "startDate": "2026-08-03",
    "endDate": "2026-09-02",
}

FOLD = {
    "foldIndex": 0,
    "trainRange": {"start": "2026-08-03", "end": "2026-08-04"},
    "oosRange": {"start": "2026-08-05", "end": "2026-09-02"},
    "trainSessions": ["2026-08-03", "2026-08-04"],
    "oosSessions": ["2026-08-05"],
}


def _cfg(*, measurement_as_of: str | None = None) -> RunConfig:
    return RunConfig(
        runIntent="exploratory",
        measurementSource="fixture-recompute",
        candidateId="score-v2-baseline",
        markets=["KR"],
        foldSpec=dict(FOLD_SPEC),
        measurementAsOfDate=measurement_as_of,
    )


def test_effective_measurement_as_of_legacy_fallback_uses_fold_end():
    cfg = _cfg()
    assert effective_measurement_as_of(cfg) == "2026-09-02"


def test_effective_measurement_as_of_prefers_explicit_cutoff():
    cfg = _cfg(measurement_as_of="2026-10-04")
    assert effective_measurement_as_of(cfg) == "2026-10-04"


def test_config_hash_includes_measurement_cutoff():
    base = _cfg()
    with_cutoff = _cfg(measurement_as_of="2026-10-04")
    assert config_hash(base) != config_hash(with_cutoff)


def test_generated_at_uses_measurement_cutoff():
    cfg = _cfg(measurement_as_of="2026-10-04")
    assert generated_at_from_config(cfg) == "2026-10-04T23:59:59Z"


def test_run_folds_passes_measurement_cutoff_to_measure_fn():
    captured: list[str] = []

    def measure_fn(_picks, _cfg, as_of_date):
        captured.append(as_of_date)
        return []

    def pit(_market, _session, _exclude):
        return "SIMPLE.KR", False

    cfg = _cfg(measurement_as_of="2026-10-04")
    run_folds(cfg, [FOLD], measure_fn, pit_fn=pit)
    assert captured == ["2026-10-04"]


def test_run_folds_legacy_fallback_uses_fold_end():
    captured: list[str] = []

    def measure_fn(_picks, _cfg, as_of_date):
        captured.append(as_of_date)
        return []

    def pit(_market, _session, _exclude):
        return "SIMPLE.KR", False

    cfg = _cfg()
    run_folds(cfg, [FOLD], measure_fn, pit_fn=pit)
    assert captured == ["2026-09-02"]


def test_run_folds_oct4_cutoff_avoids_artificial_incomplete_horizon():
    """Sep 2 fold end with Oct 4 measurement — H20 can complete vs legacy Sep 2 cutoff."""

    def measure_fn(_picks, _cfg, as_of):
        complete = as_of >= "2026-10-04"
        return [
            {
                "horizonId": "H20",
                "completionStatus": "complete" if complete else "incomplete",
            }
        ]

    def pit(_market, _session, _exclude):
        return "SIMPLE.KR", False

    cfg = _cfg(measurement_as_of="2026-10-04")
    results = run_folds(cfg, [FOLD], measure_fn, pit_fn=pit)
    assert results[0]["status"] == "complete"

    legacy = _cfg()
    legacy_results = run_folds(legacy, [FOLD], measure_fn, pit_fn=pit)
    assert legacy_results[0]["status"] == "incomplete_horizon"
