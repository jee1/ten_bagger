"""Side-by-side live baseline OOS comparison (Issue #69)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from calibration.config import load_calibration_config
from calibration.runner import LIVE_BASELINE_CANDIDATE_ID, execute_calibration

FIX = Path(__file__).resolve().parent / "fixtures" / "calibration"


def _fake_wf_report(*, candidate_id: str) -> dict:
    return {
        "candidateId": candidate_id,
        "runIntent": "exploratory",
        "aggregate": {
            "scoredPickDays": 25,
            "noPickRatio": 0.1,
            "h20ExcessReturnMean": 0.01,
            "h60ExcessReturnMean": 0.02,
        },
        "contaminationFindings": [],
        "folds": [],
    }


def test_compare_to_live_baseline_appends_baseline_row(tmp_path):
    cfg = load_calibration_config(FIX / "growth-yartseva-smoke-config.json")
    assert cfg.compareToLiveBaseline is True

    call_labels: list[str] = []

    def fake_run(cal_config, candidate, *, fold_spec, run_intent, measurement_source, label, write=True):
        call_labels.append(label)
        cid = candidate.candidateId if candidate else LIVE_BASELINE_CANDIDATE_ID
        report = _fake_wf_report(candidate_id=cid)
        return report, f"walk-forward/{cid}.json", "a" * 64

    with (
        patch("calibration.runner._run_walk_forward_for_candidate", side_effect=fake_run),
        patch("calibration.runner.rank_candidates") as mock_rank,
        patch("calibration.runner.select_promotees") as mock_promote,
        patch("calibration.runner.atomic_replace"),
        patch("calibration.runner.load_validator"),
    ):
        # Skip expensive IS ranking: pretend one promotee already selected
        mock_rank.return_value = (
            [{"candidateId": "growth_shrink_05_vq", "isScore": 1.0}],
            "fixture",
        )
        mock_promote.return_value = [cfg.candidates[0]]

        code = execute_calibration(cfg, output_dir=tmp_path, write=False, json_only=False)
        assert code == 0

    # Rebuild report via a second call that captures build_report input is harder;
    # instead assert baseline walk-forward was invoked after promotee OOS.
    assert "oos" in call_labels
    assert "oos-baseline" in call_labels


def test_compare_false_skips_baseline_append(tmp_path):
    cfg = load_calibration_config(FIX / "smoke-search-config.json")
    assert cfg.compareToLiveBaseline is False

    labels: list[str] = []

    def fake_run(cal_config, candidate, *, fold_spec, run_intent, measurement_source, label, write=True):
        labels.append(label)
        cid = candidate.candidateId if candidate else LIVE_BASELINE_CANDIDATE_ID
        return _fake_wf_report(candidate_id=cid), f"{cid}.json", "b" * 64

    with (
        patch("calibration.runner._run_walk_forward_for_candidate", side_effect=fake_run),
        patch("calibration.runner.rank_candidates") as mock_rank,
        patch("calibration.runner.select_promotees") as mock_promote,
        patch("calibration.runner.atomic_replace"),
        patch("calibration.runner.load_validator"),
    ):
        mock_rank.return_value = (
            [{"candidateId": "threshold-75", "isScore": 1.0}],
            "fixture",
        )
        mock_promote.return_value = [cfg.candidates[1]]
        execute_calibration(cfg, output_dir=tmp_path, write=False)

    assert "oos-baseline" not in labels
