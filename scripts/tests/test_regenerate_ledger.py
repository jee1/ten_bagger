"""CLI and atomic-failure tests for regenerate_ledger."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import regenerate_ledger
from tests.fixtures.price_loader import load_price_fixture

SCRIPTS = Path(__file__).resolve().parents[1]


def test_missing_as_of_date_exit_2():
    assert regenerate_ledger.main([]) == 2


def test_malformed_as_of_date_exit_2():
    assert regenerate_ledger.main(["--as-of-date", "not-a-date"]) == 2
    assert regenerate_ledger.main(["--as-of-date", "2026-13-40"]) == 2


def test_corrupt_daily_exit_1_prior_ledger_unchanged(tmp_path, monkeypatch):
    daily_dir = tmp_path / "daily"
    daily_dir.mkdir()
    (daily_dir / "bad.json").write_text("{not json", encoding="utf-8")

    ledger_dir = tmp_path / "ledger"
    ledger_dir.mkdir()
    prior = {"schemaVersion": "0.1.0", "market": "KR", "asOfDate": "2026-01-01", "entries": []}
    prior_path = ledger_dir / "KR.json"
    prior_path.write_text(json.dumps(prior), encoding="utf-8")
    perf_dir = tmp_path / "performance"
    perf_dir.mkdir()
    (perf_dir / "KR.json").write_text(
        json.dumps(
            {
                "schemaVersion": "0.1.0",
                "market": "KR",
                "asOfDate": "2026-01-01",
                "runMeta": {
                    "provider": "fixture",
                    "priceAdjustment": "adjusted_preferred",
                    "generatedAt": "2026-01-01T00:00:00+00:00",
                    "asOfDate": "2026-01-01",
                },
                "measurements": [],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(regenerate_ledger, "DAILY_DIR", daily_dir)
    monkeypatch.setattr(regenerate_ledger, "LEDGER_DIR", ledger_dir)
    monkeypatch.setattr(regenerate_ledger, "PERFORMANCE_DIR", perf_dir)

    rc = regenerate_ledger.main(["--as-of-date", "2026-02-01"])
    assert rc == 1
    assert json.loads(prior_path.read_text()) == prior


def test_missing_date_daily_fails_run(tmp_path):
    from performance.load_dailies import load_eligible_dailies

    daily_dir = tmp_path / "daily"
    daily_dir.mkdir()
    (daily_dir / "nodate.json").write_text(
        json.dumps({"market": "KR", "status": "no_pick"}), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="missing required 'date'"):
        load_eligible_dailies(daily_dir, "2026-02-01")


def test_atomic_replace_validation_failure_leaves_prior(tmp_path):
    from config import LEDGER_SCHEMA_PATH
    from performance.write_atomic import atomic_replace
    from validate_content import load_validator

    ledger_dir = tmp_path / "ledger"
    ledger_dir.mkdir()
    prior = {"schemaVersion": "0.1.0", "market": "KR", "asOfDate": "2026-01-01", "entries": []}
    path = ledger_dir / "KR.json"
    path.write_text(json.dumps(prior), encoding="utf-8")
    prior_bytes = path.read_bytes()

    invalid = {"schemaVersion": "0.1.0", "market": "KR"}  # missing asOfDate/entries
    with pytest.raises(ValueError):
        atomic_replace({path: invalid}, [load_validator(LEDGER_SCHEMA_PATH)])
    assert path.read_bytes() == prior_bytes
    assert not path.with_name(path.name + ".tmp").exists()


def test_success_path_writes_schema_valid_outputs(tmp_path, monkeypatch):
    daily_dir = tmp_path / "daily"
    daily_dir.mkdir()
    daily = {
        "date": "2026-01-02",
        "market": "KR",
        "status": "pick",
        "stock": {"symbol": "SIMPLE.KR"},
        "scores": {"composite": 80, "version": 2},
    }
    (daily_dir / "2026-01-02.json").write_text(json.dumps(daily), encoding="utf-8")
    ledger_dir = tmp_path / "ledger"
    perf_dir = tmp_path / "performance"

    bars = load_price_fixture("simple_kr_h20")

    monkeypatch.setattr(
        regenerate_ledger,
        "default_price_provider",
        lambda _as_of: (lambda _s, _m: bars),
    )
    monkeypatch.setattr(
        regenerate_ledger, "default_benchmark_provider", lambda _as_of: lambda _b: None
    )

    regenerate_ledger.regenerate(
        as_of_date="2026-02-10",
        markets=("KR",),
        daily_dir=daily_dir,
        ledger_dir=ledger_dir,
        performance_dir=perf_dir,
        provider_label="fixture",
    )
    assert (ledger_dir / "KR.json").exists()
    assert (perf_dir / "KR.json").exists()
    perf = json.loads((perf_dir / "KR.json").read_text())
    assert len(perf["measurements"]) == 8


def test_dry_run_leaves_targets_unwritten(tmp_path, monkeypatch):
    daily_dir = tmp_path / "daily"
    daily_dir.mkdir()
    ledger_dir = tmp_path / "ledger"
    perf_dir = tmp_path / "performance"

    monkeypatch.setattr(
        regenerate_ledger,
        "default_price_provider",
        lambda _as_of: (lambda _s, _m: load_price_fixture("simple_kr_h20")),
    )
    monkeypatch.setattr(
        regenerate_ledger, "default_benchmark_provider", lambda _as_of: lambda _b: None
    )

    regenerate_ledger.regenerate(
        as_of_date="2026-01-01",
        markets=("KR",),
        daily_dir=daily_dir,
        ledger_dir=ledger_dir,
        performance_dir=perf_dir,
        dry_run=True,
    )
    assert not (ledger_dir / "KR.json").exists()


def test_daily_files_untouched(tmp_path, monkeypatch):
    daily_dir = tmp_path / "daily"
    daily_dir.mkdir()
    daily_path = daily_dir / "2026-01-02.json"
    original = json.dumps(
        {
            "date": "2026-01-02",
            "market": "KR",
            "status": "pick",
            "stock": {"symbol": "SIMPLE.KR"},
            "scores": {"composite": 80},
        }
    )
    daily_path.write_text(original, encoding="utf-8")
    ledger_dir = tmp_path / "ledger"
    perf_dir = tmp_path / "performance"

    monkeypatch.setattr(
        regenerate_ledger,
        "default_price_provider",
        lambda _as_of: (lambda _s, _m: load_price_fixture("simple_kr_h20")),
    )
    monkeypatch.setattr(
        regenerate_ledger, "default_benchmark_provider", lambda _as_of: lambda _b: None
    )

    regenerate_ledger.regenerate(
        as_of_date="2026-02-10",
        markets=("KR",),
        daily_dir=daily_dir,
        ledger_dir=ledger_dir,
        performance_dir=perf_dir,
        provider_label="fixture",
    )
    assert daily_path.read_text() == original


def test_offline_no_yfinance(monkeypatch):
    """T032: block yfinance import path in unit tests."""
    import performance.prices_live as prices_live

    def boom(*_a, **_k):
        raise AssertionError("yfinance must not be called in offline tests")

    monkeypatch.setattr(prices_live, "fetch_live_bars", boom)
    bars = load_price_fixture("simple_kr_h20")
    m = __import__("performance.returns", fromlist=["measure_pick_horizon"]).measure_pick_horizon(
        bars=bars,
        benchmark_bars=None,
        pick_date="2026-01-02",
        as_of_date="2026-02-10",
        market="KR",
        symbol="SIMPLE.KR",
        horizon_id="H20",
    )
    assert m["completionStatus"] == "complete"
