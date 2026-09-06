"""Offline calibration smoke tests (#67)."""

from __future__ import annotations

from pathlib import Path

import config as live_config
import pytest
from calibrate import main as calibrate_main
from calibration.config import load_calibration_config
from calibration.report import build_report, serialize_report

FIX = Path(__file__).resolve().parent / "fixtures" / "calibration"


def test_dry_run_smoke_search():
    code = calibrate_main(["run", "--config", str(FIX / "smoke-search-config.json"), "--dry-run"])
    assert code == 0


def test_invalid_weight_sum_fails_config():
    with pytest.raises(ValueError, match="sum"):
        load_calibration_config(FIX / "invalid-weight-sum-config.json")


def test_overlapping_is_oos_fails_config():
    with pytest.raises(ValueError, match="overlap"):
        load_calibration_config(FIX / "overlapping-is-oos-config.json")


def test_report_bytes_stable_and_config_untouched():
    thr = live_config.COMPOSITE_THRESHOLD
    w = live_config.WEIGHT_SIZE
    cfg = load_calibration_config(FIX / "smoke-baseline-only-config.json")
    report = build_report(
        cal_config=cfg,
        run_id="smoke000smoke000",
        generated_at="2026-04-30T23:59:59Z",
        is_ranking=[],
        selection_rationale="baseline-only",
        oos_evaluations=[],
        overall="N/A",
        failed_bullets=[],
    )
    assert serialize_report(report) == serialize_report(report)
    assert live_config.COMPOSITE_THRESHOLD == thr
    assert live_config.WEIGHT_SIZE == w
    assert report["mergeCriteriaRef"].endswith("threshold-weight-merge-criteria.md")
    assert report["packageIntent"] == "exploratory"
    assert "liveConstantsSnapshot" in report


def test_harness_fail_closed_mentions_walk_forward():
    src = Path(__file__).resolve().parents[1] / "calibration" / "runner.py"
    text = src.read_text(encoding="utf-8")
    assert "npm run walk-forward" in text
    assert "walk-forward harness" in text.lower() or "#66" in text


def test_no_backtest_screen_import_in_runner_source():
    src = Path(__file__).resolve().parents[1] / "calibration" / "runner.py"
    text = src.read_text(encoding="utf-8")
    assert "import backtest_screen" not in text
    assert "from backtest_screen" not in text


def test_baseline_only_go_stdout_does_not_suggest_config_pr(capsys):
    from calibration.runner import _print_pr_hint

    _print_pr_hint(
        {"runId": "x"},
        go=True,
        mode="baseline-only",
        package_intent="go_evidence",
    )
    out = capsys.readouterr().out
    assert "Open an explicit PR" not in out
    assert "freeze evidence only" in out


def test_search_go_hint_score_v3_only_when_compare_baseline(capsys):
    from calibration.runner import _print_pr_hint

    _print_pr_hint(
        {"runId": "y"},
        go=True,
        mode="search",
        package_intent="go_evidence",
        compare_to_live_baseline=False,
    )
    out_default = capsys.readouterr().out
    assert "Open an explicit PR" in out_default
    assert "SCORE_VERSION=3" not in out_default

    _print_pr_hint(
        {"runId": "z"},
        go=True,
        mode="search",
        package_intent="go_evidence",
        compare_to_live_baseline=True,
    )
    out_growth = capsys.readouterr().out
    assert "SCORE_VERSION=3" in out_growth


def test_score_v3_search_go_evidence_config_dry_run():
    root = Path(__file__).resolve().parents[1]
    cfg_path = root / "calibration" / "configs" / "score-v3-search-go-evidence.json"
    code = calibrate_main(["run", "--config", str(cfg_path), "--dry-run"])
    assert code == 0
    cfg = load_calibration_config(cfg_path)
    assert cfg.packageIntent == "go_evidence"
    assert cfg.mode == "search"
    assert cfg.compareToLiveBaseline is True
    assert cfg.measurementSourceOos == "ledger"


def test_preflight_blocks_search_go_when_not_ready(tmp_path, capsys):
    from calibration.candidates import CandidateSpec
    from calibration.config import CalibrationRunConfig
    from calibration.runner import execute_calibration

    perf = tmp_path / "performance"
    perf.mkdir()
    (perf / "KR.json").write_text('{"measurements": []}', encoding="utf-8")
    cal = CalibrationRunConfig(
        packageIntent="go_evidence",
        mode="search",
        candidates=[
            CandidateSpec(
                candidateId="growth_shrink_10_vq",
                threshold=None,
                weights={
                    "WEIGHT_SIZE": 0.15,
                    "WEIGHT_VALUATION": 0.3,
                    "WEIGHT_GROWTH": 0.1,
                    "WEIGHT_QUALITY": 0.25,
                    "WEIGHT_ENTRY": 0.1,
                    "WEIGHT_MOMENTUM": 0.1,
                },
                notes=None,
            )
        ],
        isFoldSpec={
            "mode": "rolling",
            "trainSessions": 4,
            "oosSessions": 2,
            "stepSessions": 2,
            "startDate": "2026-06-01",
            "endDate": "2026-07-15",
        },
        oosFoldSpec={
            "mode": "rolling",
            "trainSessions": 6,
            "oosSessions": 3,
            "stepSessions": 3,
            "startDate": "2026-07-16",
            "endDate": "2026-08-04",
        },
        markets=["KR"],
        promoteTopN=1,
        measurementSourceIs="ledger",
        measurementSourceOos="ledger",
        ledgerDir=tmp_path / "ledger",
        performanceDir=perf,
        outputDir=tmp_path / "out",
        walkForwardOutputDir=tmp_path / "wf",
        compareToLiveBaseline=True,
    )
    code = execute_calibration(cal, write=False)
    assert code == 2
    out = capsys.readouterr().out
    assert "not_ready" in out
    assert "SCORE_VERSION=3" not in out or "no Score v3" in out
