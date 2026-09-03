"""IS ranking unit tests with mocked walk-forward."""

from __future__ import annotations

from pathlib import Path

from calibration.config import load_calibration_config
from calibration.is_rank import rank_candidates_is, select_promotees

FIX = Path(__file__).resolve().parent / "fixtures" / "calibration"


def test_rank_by_h20_excess_desc():
    cfg = load_calibration_config(FIX / "smoke-search-config.json")

    def fake_wf(candidate):
        metrics = {
            "score-v2-baseline": 0.01,
            "threshold-75": 0.05,
            "weights-tilt-quality": 0.02,
        }
        report = {
            "coverage": {"oosPickDays": 10, "noPickDays": 1},
            "aggregate": {
                "horizons": [
                    {"horizonId": "H20", "excessReturnMean": metrics[candidate.candidateId]}
                ]
            },
        }
        return {
            "report": report,
            "path": f"walk-forward/{candidate.candidateId}.json",
            "configHash": "b" * 64,
        }

    ranking = rank_candidates_is(cfg.candidates, run_wf=fake_wf)
    ranked = [e for e in ranking if e["status"] == "ranked"]
    assert ranked[0]["candidateId"] == "threshold-75"
    assert ranked[0]["rank"] == 1
    promotees, rationale = select_promotees(ranking, promote_top_n=1)
    assert promotees[0]["candidateId"] == "threshold-75"
    assert "H20" in rationale


def test_tie_break_pick_days_then_id():
    cfg = load_calibration_config(FIX / "smoke-search-config.json")

    def fake_wf(candidate):
        pick_days = {
            "score-v2-baseline": 10,
            "threshold-75": 20,
            "weights-tilt-quality": 20,
        }
        report = {
            "coverage": {"oosPickDays": pick_days[candidate.candidateId]},
            "aggregate": {"horizons": [{"horizonId": "H20", "excessReturnMean": 0.05}]},
        }
        return {
            "report": report,
            "path": f"wf/{candidate.candidateId}.json",
            "configHash": "c" * 64,
        }

    ranking = rank_candidates_is(cfg.candidates, run_wf=fake_wf)
    ranked_ids = [e["candidateId"] for e in ranking if e["status"] == "ranked"]
    assert ranked_ids[0] == "threshold-75"
    assert ranked_ids[1] == "weights-tilt-quality"
    assert ranked_ids[2] == "score-v2-baseline"
