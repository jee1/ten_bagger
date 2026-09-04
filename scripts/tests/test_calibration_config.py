"""Calibration config loader tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from calibration.config import config_hash, load_calibration_config

FIX = Path(__file__).resolve().parent / "fixtures" / "calibration"


def test_load_smoke_search_config():
    cfg = load_calibration_config(FIX / "smoke-search-config.json")
    assert cfg.mode == "search"
    assert cfg.packageIntent == "exploratory"
    assert len(cfg.candidates) == 3
    assert cfg.compareToLiveBaseline is False
    h1 = config_hash(cfg)
    h2 = config_hash(cfg)
    assert h1 == h2 and len(h1) == 64


def test_compare_to_live_baseline_optional_true():
    cfg = load_calibration_config(FIX / "growth-yartseva-smoke-config.json")
    assert cfg.compareToLiveBaseline is True
    assert len(cfg.candidates) == 4


def test_rejects_overlapping_is_oos():
    with pytest.raises(ValueError, match="overlap"):
        load_calibration_config(FIX / "overlapping-is-oos-config.json")


def test_rejects_invalid_weight_sum():
    with pytest.raises(ValueError, match="sum"):
        load_calibration_config(FIX / "invalid-weight-sum-config.json")


def test_rejects_go_evidence_without_ledger_oos(tmp_path):
    data = json.loads((FIX / "smoke-search-config.json").read_text(encoding="utf-8"))
    data["packageIntent"] = "go_evidence"
    data["measurementSourceOos"] = "fixture-recompute"
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="ledger"):
        load_calibration_config(path)


def test_baseline_only_rejects_candidate_grid():
    data = json.loads((FIX / "smoke-baseline-only-config.json").read_text(encoding="utf-8"))
    data["candidates"] = [{"candidateId": "x", "threshold": None, "weights": None}]
    # write via load path
    import tempfile

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
        json.dump(data, fh)
        path = fh.name
    with pytest.raises(ValueError, match="baseline-only"):
        load_calibration_config(path)
