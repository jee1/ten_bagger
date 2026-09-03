"""RunConfig loader and validation tests."""

from __future__ import annotations

import json

import pytest
from walk_forward.config import RunConfig, config_hash, load_run_config

BASE_CONFIG = {
    "runIntent": "exploratory",
    "measurementSource": "fixture-recompute",
    "candidateId": "score-v2-baseline",
    "markets": ["KR", "US"],
    "foldSpec": {
        "mode": "rolling",
        "trainSessions": 40,
        "oosSessions": 20,
        "stepSessions": 20,
        "startDate": "2025-01-02",
        "endDate": "2025-06-30",
    },
    "weightOverrides": None,
}


def test_load_run_config_valid(tmp_path):
    path = tmp_path / "run-config.json"
    path.write_text(json.dumps(BASE_CONFIG), encoding="utf-8")
    cfg = load_run_config(path)
    assert isinstance(cfg, RunConfig)
    assert cfg.runIntent == "exploratory"
    assert cfg.candidateId == "score-v2-baseline"
    assert cfg.foldSpec["mode"] == "rolling"


def test_load_run_config_rejects_go_evidence_with_fixture_recompute(tmp_path):
    bad = {**BASE_CONFIG, "runIntent": "go_evidence", "measurementSource": "fixture-recompute"}
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(ValueError, match="go_evidence"):
        load_run_config(path)


def test_load_run_config_rejects_more_than_four_candidates(tmp_path):
    bad = {**BASE_CONFIG, "candidateIds": ["a", "b", "c", "d", "e"]}
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(ValueError, match="4 candidates"):
        load_run_config(path)


VALID_WEIGHT_OVERRIDES = {
    "WEIGHT_SIZE": 0.15,
    "WEIGHT_VALUATION": 0.20,
    "WEIGHT_GROWTH": 0.20,
    "WEIGHT_QUALITY": 0.25,
    "WEIGHT_ENTRY": 0.10,
    "WEIGHT_MOMENTUM": 0.10,
}


def test_load_run_config_accepts_valid_weight_and_threshold_overrides(tmp_path):
    good = {
        **BASE_CONFIG,
        "weightOverrides": VALID_WEIGHT_OVERRIDES,
        "thresholdOverride": 75.0,
    }
    path = tmp_path / "ok-overrides.json"
    path.write_text(json.dumps(good), encoding="utf-8")
    cfg = load_run_config(path)
    assert cfg.weightOverrides == VALID_WEIGHT_OVERRIDES
    assert cfg.thresholdOverride == 75.0


def test_load_run_config_rejects_bad_weight_sum(tmp_path):
    bad = {
        **BASE_CONFIG,
        "weightOverrides": {**VALID_WEIGHT_OVERRIDES, "WEIGHT_SIZE": 0.99},
    }
    path = tmp_path / "bad-sum.json"
    path.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(ValueError, match="sum|weight"):
        load_run_config(path)


def test_config_hash_includes_overrides(tmp_path):
    path = tmp_path / "base.json"
    path.write_text(json.dumps(BASE_CONFIG), encoding="utf-8")
    cfg_base = load_run_config(path)
    path2 = tmp_path / "ovr.json"
    path2.write_text(
        json.dumps(
            {
                **BASE_CONFIG,
                "weightOverrides": VALID_WEIGHT_OVERRIDES,
                "thresholdOverride": 75.0,
            }
        ),
        encoding="utf-8",
    )
    cfg_ovr = load_run_config(path2)
    assert config_hash(cfg_base) != config_hash(cfg_ovr)


def test_load_run_config_rejects_non_rolling_fold_mode(tmp_path):
    bad = {
        **BASE_CONFIG,
        "foldSpec": {**BASE_CONFIG["foldSpec"], "mode": "anchored"},
    }
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(ValueError, match="rolling"):
        load_run_config(path)


def test_config_hash_is_stable_64_char_hex(tmp_path):
    path = tmp_path / "run-config.json"
    path.write_text(json.dumps(BASE_CONFIG), encoding="utf-8")
    cfg = load_run_config(path)
    h1 = config_hash(cfg)
    h2 = config_hash(cfg)
    assert h1 == h2
    assert len(h1) == 64
    assert all(c in "0123456789abcdef" for c in h1)


def test_config_hash_excludes_secrets(tmp_path):
    path = tmp_path / "c.json"
    path.write_text(json.dumps(BASE_CONFIG), encoding="utf-8")
    cfg = load_run_config(path)
    h_clean = config_hash(cfg)
    h_with_extra = config_hash(
        RunConfig(
            runIntent=cfg.runIntent,
            measurementSource=cfg.measurementSource,
            candidateId=cfg.candidateId,
            markets=cfg.markets,
            foldSpec=cfg.foldSpec,
            weightOverrides=cfg.weightOverrides,
            ledgerDir=cfg.ledgerDir,
            performanceDir=cfg.performanceDir,
            outputDir=cfg.outputDir,
        )
    )
    assert h_with_extra == h_clean
