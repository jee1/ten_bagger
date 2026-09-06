"""Counterfactual ledger miss → price recompute (#91 / 030)."""

from __future__ import annotations

import json
from pathlib import Path

from walk_forward.config import RunConfig
from walk_forward.measure import (
    fixture_benchmark_provider,
    fixture_price_provider,
    measure_oos_picks,
)

VALID_WEIGHT_OVERRIDES = {
    "WEIGHT_SIZE": 0.15,
    "WEIGHT_VALUATION": 0.20,
    "WEIGHT_GROWTH": 0.20,
    "WEIGHT_QUALITY": 0.25,
    "WEIGHT_ENTRY": 0.10,
    "WEIGHT_MOMENTUM": 0.10,
}


def _empty_perf(tmp_path: Path) -> Path:
    perf_dir = tmp_path / "performance"
    perf_dir.mkdir()
    (perf_dir / "KR.json").write_text(
        json.dumps({"measurements": []}),
        encoding="utf-8",
    )
    return perf_dir


def _ledger_row(*, pick_date: str, symbol: str, horizon_id: str) -> dict:
    return {
        "market": "KR",
        "pickDate": pick_date,
        "symbol": symbol,
        "horizonId": horizon_id,
        "benchmarkId": "KR-KOSPI",
        "completionStatus": "complete",
        "benchmarkCompletionStatus": "complete",
        "survivorshipFlag": "listed",
        "asOfDate": "2026-02-28",
        "forwardReturn": 0.11,
        "benchmarkReturn": 0.01,
        "source": "ledger-fixture",
    }


def test_override_ledger_miss_uses_price_recompute(tmp_path):
    perf_dir = _empty_perf(tmp_path)
    cfg = RunConfig(
        runIntent="go_evidence",
        measurementSource="ledger",
        candidateId="growth-candidate",
        markets=["KR"],
        foldSpec={"endDate": "2026-02-28"},
        performanceDir=perf_dir,
        weightOverrides=VALID_WEIGHT_OVERRIDES,
    )
    # SIMPLE.KR maps to simple_kr_h20 fixture; pick early enough for H20.
    picks = [{"pickDate": "2026-01-02", "symbol": "SIMPLE.KR", "market": "KR"}]
    measurements = measure_oos_picks(
        picks,
        cfg,
        "2026-02-28",
        fixture_price_provider("2026-02-28"),
        fixture_benchmark_provider("2026-02-28"),
    )
    h20 = [m for m in measurements if m["horizonId"] == "H20"]
    assert len(h20) == 1
    assert h20[0].get("incompleteReason") != "missing_ledger_row"
    assert h20[0]["completionStatus"] == "complete"


def test_override_prefers_ledger_when_row_present(tmp_path):
    perf_dir = tmp_path / "performance"
    perf_dir.mkdir()
    (perf_dir / "KR.json").write_text(
        json.dumps(
            {
                "measurements": [
                    _ledger_row(
                        pick_date="2026-01-02",
                        symbol="SIMPLE.KR",
                        horizon_id="H20",
                    ),
                    _ledger_row(
                        pick_date="2026-01-02",
                        symbol="SIMPLE.KR",
                        horizon_id="H60",
                    ),
                ]
            }
        ),
        encoding="utf-8",
    )
    cfg = RunConfig(
        runIntent="go_evidence",
        measurementSource="ledger",
        candidateId="growth-candidate",
        markets=["KR"],
        foldSpec={"endDate": "2026-02-28"},
        performanceDir=perf_dir,
        weightOverrides=VALID_WEIGHT_OVERRIDES,
    )
    picks = [{"pickDate": "2026-01-02", "symbol": "SIMPLE.KR", "market": "KR"}]
    measurements = measure_oos_picks(
        picks,
        cfg,
        "2026-02-28",
        fixture_price_provider("2026-02-28"),
        fixture_benchmark_provider("2026-02-28"),
    )
    h20 = next(m for m in measurements if m["horizonId"] == "H20")
    assert h20["forwardReturn"] == 0.11
    assert h20.get("source") == "ledger-fixture"


def test_no_override_go_evidence_still_strict_on_miss(tmp_path):
    perf_dir = _empty_perf(tmp_path)
    cfg = RunConfig(
        runIntent="go_evidence",
        measurementSource="ledger",
        candidateId="score-v2-baseline",
        markets=["KR"],
        foldSpec={"endDate": "2026-02-28"},
        performanceDir=perf_dir,
    )
    picks = [{"pickDate": "2026-01-05", "symbol": "MISSING.KR", "market": "KR"}]
    try:
        measure_oos_picks(
            picks,
            cfg,
            "2026-02-28",
            fixture_price_provider("2026-02-28"),
            fixture_benchmark_provider("2026-02-28"),
        )
        raised = False
    except ValueError as exc:
        raised = True
        assert "missing ledger measurement" in str(exc)
    assert raised
