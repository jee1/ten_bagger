"""Regression: execute wires live price providers for ledger measurement (#168)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
import pytest
from walk_forward.config import RunConfig
from walk_forward.execute import make_measure_fn
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


def _aug_sep_bars() -> pd.DataFrame:
    dates = pd.bdate_range("2026-07-01", "2026-10-04")
    close = [100.0 + i * 0.5 for i in range(len(dates))]
    return pd.DataFrame(
        {
            "date": dates.strftime("%Y-%m-%d"),
            "Open": close,
            "Close": [c + 0.2 for c in close],
            "High": [c + 0.5 for c in close],
            "Low": [c - 0.5 for c in close],
            "Volume": [1_000_000] * len(dates),
        }
    )


def _empty_perf(tmp_path: Path) -> Path:
    perf_dir = tmp_path / "performance"
    perf_dir.mkdir()
    for market in ("KR", "US"):
        (perf_dir / f"{market}.json").write_text(
            json.dumps({"measurements": []}),
            encoding="utf-8",
        )
    return perf_dir


def test_fixture_provider_insufficient_history_for_aug_counterfactual_pick():
    """Root cause (#168): fixture bars end Feb 2026; Aug picks fail recompute."""
    cfg = RunConfig(
        runIntent="go_evidence",
        measurementSource="ledger",
        candidateId="growth-candidate",
        markets=["KR"],
        foldSpec={"endDate": "2026-09-02"},
        weightOverrides=VALID_WEIGHT_OVERRIDES,
    )
    picks = [{"pickDate": "2026-08-05", "symbol": "005930.KS", "market": "KR"}]
    measurements = measure_oos_picks(
        picks,
        cfg,
        "2026-10-04",
        fixture_price_provider("2026-10-04"),
        fixture_benchmark_provider("2026-10-04"),
    )
    h20 = next(m for m in measurements if m["horizonId"] == "H20")
    assert h20["completionStatus"] == "incomplete"
    assert h20["incompleteReason"] == "insufficient_history"


def test_make_measure_fn_ledger_uses_default_providers(monkeypatch):
    captured: dict[str, str] = {}

    def fake_price(as_of: str):
        captured["price_as_of"] = as_of
        return lambda _s, _m: _aug_sep_bars()

    def fake_bench(as_of: str):
        captured["bench_as_of"] = as_of
        return lambda _b: _aug_sep_bars()

    monkeypatch.setattr("walk_forward.execute.default_price_provider", fake_price)
    monkeypatch.setattr("walk_forward.execute.default_benchmark_provider", fake_bench)

    cfg = RunConfig(
        runIntent="go_evidence",
        measurementSource="ledger",
        candidateId="growth-candidate",
        markets=["KR"],
        foldSpec={"endDate": "2026-09-02"},
        measurementAsOfDate="2026-10-04",
        weightOverrides=VALID_WEIGHT_OVERRIDES,
    )
    measure_fn = make_measure_fn(cfg)
    picks = [{"pickDate": "2026-08-05", "symbol": "005930.KS", "market": "KR"}]
    out = measure_fn(picks, cfg, "2026-10-04")
    assert captured == {"price_as_of": "2026-10-04", "bench_as_of": "2026-10-04"}
    h20 = next(m for m in out if m["horizonId"] == "H20")
    assert h20["completionStatus"] == "complete"
    assert h20["asOfDate"] == "2026-10-04"


def test_make_measure_fn_fixture_recompute_keeps_fixture_providers(monkeypatch):
    called = {"default": False}

    def should_not_run(_as_of: str):
        called["default"] = True
        return lambda _s, _m: _aug_sep_bars()

    monkeypatch.setattr("walk_forward.execute.default_price_provider", should_not_run)
    monkeypatch.setattr("walk_forward.execute.default_benchmark_provider", should_not_run)

    cfg = RunConfig(
        runIntent="exploratory",
        measurementSource="fixture-recompute",
        candidateId="score-v2-baseline",
        markets=["KR"],
        foldSpec={"endDate": "2026-02-28"},
    )
    measure_fn = make_measure_fn(cfg)
    picks = [{"pickDate": "2026-01-02", "symbol": "SIMPLE.KR", "market": "KR"}]
    out = measure_fn(picks, cfg, "2026-02-28")
    assert called["default"] is False
    h20 = next(m for m in out if m["horizonId"] == "H20")
    assert h20["completionStatus"] == "complete"


def test_counterfactual_recompute_respects_measurement_cutoff(tmp_path, monkeypatch):
    perf_dir = _empty_perf(tmp_path)
    bars = _aug_sep_bars()

    monkeypatch.setattr(
        "walk_forward.execute.default_price_provider",
        lambda as_of: (lambda _s, _m: bars),
    )
    monkeypatch.setattr(
        "walk_forward.execute.default_benchmark_provider",
        lambda as_of: (lambda _b: bars),
    )

    cfg = RunConfig(
        runIntent="go_evidence",
        measurementSource="ledger",
        candidateId="growth-candidate",
        markets=["KR"],
        foldSpec={"endDate": "2026-09-02"},
        measurementAsOfDate="2026-10-04",
        performanceDir=perf_dir,
        weightOverrides=VALID_WEIGHT_OVERRIDES,
    )
    picks = [{"pickDate": "2026-08-05", "symbol": "REAL.KR", "market": "KR"}]
    measurements = make_measure_fn(cfg)(picks, cfg, "2026-10-04")
    h20 = next(m for m in measurements if m["horizonId"] == "H20")
    assert h20["completionStatus"] == "complete"
    assert h20["asOfDate"] == "2026-10-04"


def test_counterfactual_recompute_incomplete_when_cutoff_before_horizon(monkeypatch):
    bars = _aug_sep_bars()

    monkeypatch.setattr(
        "walk_forward.execute.default_price_provider",
        lambda _as_of: (lambda _s, _m: bars),
    )
    monkeypatch.setattr(
        "walk_forward.execute.default_benchmark_provider",
        lambda _as_of: (lambda _b: bars),
    )

    cfg = RunConfig(
        runIntent="go_evidence",
        measurementSource="ledger",
        candidateId="growth-candidate",
        markets=["KR"],
        foldSpec={"endDate": "2026-09-02"},
        measurementAsOfDate="2026-08-10",
        weightOverrides=VALID_WEIGHT_OVERRIDES,
    )
    picks = [{"pickDate": "2026-08-05", "symbol": "REAL.KR", "market": "KR"}]
    measurements = make_measure_fn(cfg)(picks, cfg, "2026-08-10")
    h20 = next(m for m in measurements if m["horizonId"] == "H20")
    assert h20["completionStatus"] == "incomplete"
    assert h20["incompleteReason"] in ("horizon_beyond_asof", "missing_exit")


@pytest.mark.skipif(os.environ.get("LIVE_DATA") != "1", reason="set LIVE_DATA=1 for network smoke")
def test_bounded_live_provider_smoke_one_pick():
    """One real-symbol H20 measurement with Oct 4 cutoff (manual / pre-search smoke)."""
    from performance.prices_live import default_benchmark_provider, default_price_provider

    price = default_price_provider("2026-10-04")
    bench = default_benchmark_provider("2026-10-04")
    cfg = RunConfig(
        runIntent="go_evidence",
        measurementSource="ledger",
        candidateId="growth-candidate",
        markets=["KR"],
        foldSpec={"endDate": "2026-09-02"},
        measurementAsOfDate="2026-10-04",
        weightOverrides=VALID_WEIGHT_OVERRIDES,
    )
    picks = [{"pickDate": "2026-08-05", "symbol": "005930.KS", "market": "KR"}]
    measurements = measure_oos_picks(picks, cfg, "2026-10-04", price, bench)
    h20 = next(m for m in measurements if m["horizonId"] == "H20")
    assert h20["completionStatus"] == "complete"
    assert h20.get("incompleteReason") != "insufficient_history"
    assert h20["asOfDate"] == "2026-10-04"
