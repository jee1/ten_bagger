"""End-to-end walk-forward integration tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from config import WALK_FORWARD_SCHEMA_PATH
from validate_content import load_validator
from walk_forward.config import load_run_config
from walk_forward.folds import build_decision_sessions, generate_rolling_folds
from walk_forward.measure import (
    fixture_benchmark_provider,
    fixture_price_provider,
    measure_oos_picks,
)
from walk_forward.report import build_report, serialize_report
from walk_forward.runner import run_folds

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "walk_forward"
GENERATED_AT = "2026-09-01T12:00:00Z"


def _stub_pit(_market: str, as_of_date: str, _exclude: set[str]) -> tuple[str | None, bool]:
    day = int(as_of_date.split("-")[2])
    if day % 3 == 0:
        return None, True
    return "SIMPLE.KR", False


def _measure_fn(picks, run_config, as_of_date):
    return measure_oos_picks(
        picks,
        run_config,
        as_of_date,
        fixture_price_provider(as_of_date),
        fixture_benchmark_provider(as_of_date),
    )


def test_integration_fixture_recompute_two_folds_deterministic(tmp_path):
    config_path = FIXTURES / "smoke-run-config.json"
    run_config = load_run_config(config_path)
    fold_spec = run_config.foldSpec
    sessions = build_decision_sessions(
        fold_spec["startDate"],
        fold_spec["endDate"],
        run_config.markets,
    )
    folds = generate_rolling_folds(fold_spec, sessions)
    assert len(folds) >= 2

    fold_results = run_folds(
        run_config,
        folds,
        _measure_fn,
        pit_fn=_stub_pit,
        as_of_date=fold_spec["endDate"],
    )
    report = build_report(
        run_config=run_config,
        fold_results=fold_results,
        run_id="integration-test",
        generated_at=GENERATED_AT,
    )
    b1 = serialize_report(report)
    b2 = serialize_report(report)
    assert b1 == b2

    validator = load_validator(WALK_FORWARD_SCHEMA_PATH)
    errors = sorted(validator.iter_errors(report), key=lambda e: e.path)
    assert not errors, [f"{'.'.join(map(str, e.path))}: {e.message}" for e in errors]

    h20 = [h for h in report["aggregate"]["horizons"] if h["horizonId"] == "H20"]
    assert h20


def test_train_oos_ranges_disjoint_and_match_generator():
    config_path = FIXTURES / "smoke-run-config.json"
    run_config = load_run_config(config_path)
    fold_spec = run_config.foldSpec
    sessions = build_decision_sessions(
        fold_spec["startDate"],
        fold_spec["endDate"],
        run_config.markets,
    )
    folds = generate_rolling_folds(fold_spec, sessions)
    fold_results = run_folds(
        run_config,
        folds,
        _measure_fn,
        pit_fn=_stub_pit,
        as_of_date=fold_spec["endDate"],
    )
    report = build_report(
        run_config=run_config,
        fold_results=fold_results,
        run_id="range-test",
        generated_at=GENERATED_AT,
    )
    for gen, rep in zip(folds, report["folds"], strict=True):
        assert rep["trainRange"] == gen["trainRange"]
        assert rep["oosRange"] == gen["oosRange"]
        train = set(gen["trainSessions"])
        oos = set(gen["oosSessions"])
        assert train.isdisjoint(oos)


def test_partial_market_kr_only_skips_us_sessions():
    config_path = FIXTURES / "smoke-run-config.json"
    run_config = load_run_config(config_path)
    fold_spec = run_config.foldSpec
    sessions = build_decision_sessions(
        fold_spec["startDate"],
        fold_spec["endDate"],
        ["KR"],
    )
    kr_sessions = [s for s in sessions if int(s.split("-")[2]) % 2 == 1]
    assert kr_sessions
    folds = generate_rolling_folds(fold_spec, kr_sessions)
    fold_results = run_folds(
        run_config,
        folds,
        _measure_fn,
        pit_fn=_stub_pit,
        as_of_date=fold_spec["endDate"],
    )
    total_evaluated = sum(f["pickDays"] + f["noPickDays"] for f in fold_results)
    assert total_evaluated > 0


def test_ledger_missing_symbol_surfaces_incomplete(tmp_path):
    perf_dir = tmp_path / "performance"
    perf_dir.mkdir()
    (perf_dir / "KR.json").write_text(
        json.dumps({"measurements": []}),
        encoding="utf-8",
    )
    from walk_forward.config import RunConfig

    cfg = RunConfig(
        runIntent="exploratory",
        measurementSource="ledger",
        candidateId="score-v2-baseline",
        markets=["KR"],
        foldSpec={"endDate": "2026-02-28"},
        performanceDir=perf_dir,
    )
    picks = [{"pickDate": "2026-01-05", "symbol": "MISSING.KR", "market": "KR"}]
    measurements = measure_oos_picks(
        picks,
        cfg,
        "2026-02-28",
        fixture_price_provider("2026-02-28"),
        fixture_benchmark_provider("2026-02-28"),
    )
    assert measurements[0]["completionStatus"] == "incomplete"
    assert measurements[0]["incompleteReason"] == "missing_ledger_row"


def test_corrupt_performance_bundle_raises_actionable(tmp_path):
    perf_dir = tmp_path / "performance"
    perf_dir.mkdir()
    (perf_dir / "KR.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError, match="corrupt performance bundle"):
        from walk_forward.ledger_loader import load_performance_index

        load_performance_index(perf_dir)


def test_skipped_empty_train_when_no_train_picks():
    from walk_forward.config import RunConfig

    cfg = RunConfig(
        runIntent="exploratory",
        measurementSource="fixture-recompute",
        candidateId="score-v2-baseline",
        markets=["KR"],
        foldSpec={"endDate": "2026-02-28"},
    )
    fold = {
        "foldIndex": 0,
        "trainRange": {"start": "2026-01-01", "end": "2026-01-05"},
        "oosRange": {"start": "2026-01-06", "end": "2026-01-10"},
        "trainSessions": ["2026-01-01", "2026-01-03", "2026-01-05"],
        "oosSessions": ["2026-01-07", "2026-01-09"],
    }

    def _never_pick(_m, _d, _e):
        return None, True

    results = run_folds(cfg, [fold], _measure_fn, pit_fn=_never_pick, as_of_date="2026-02-28")
    assert results[0]["status"] == "skipped_empty_train"


def test_go_evidence_missing_measurement_raises(tmp_path):
    perf_dir = tmp_path / "performance"
    perf_dir.mkdir()
    (perf_dir / "KR.json").write_text(json.dumps({"measurements": []}), encoding="utf-8")
    from walk_forward.config import RunConfig

    cfg = RunConfig(
        runIntent="go_evidence",
        measurementSource="ledger",
        candidateId="score-v2-baseline",
        markets=["KR"],
        foldSpec={"endDate": "2026-02-28"},
        performanceDir=perf_dir,
    )
    picks = [{"pickDate": "2026-01-05", "symbol": "MISSING.KR", "market": "KR"}]
    with pytest.raises(ValueError, match="regenerate"):
        measure_oos_picks(
            picks,
            cfg,
            "2026-02-28",
            fixture_price_provider("2026-02-28"),
            fixture_benchmark_provider("2026-02-28"),
        )
