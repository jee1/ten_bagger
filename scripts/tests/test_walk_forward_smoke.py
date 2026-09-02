"""Offline smoke tests for walk-forward harness (US5)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from config import DAILY_DIR, WALK_FORWARD_SCHEMA_PATH
from validate_content import load_validator
from walk_forward.config import load_run_config
from walk_forward.execute import execute_run
from walk_forward.folds import build_decision_sessions, generate_rolling_folds
from walk_forward.pit_screen import pit_screen_day
from walk_forward.report import serialize_report

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "walk_forward"
UNIVERSE = FIXTURES / "universe" / "kr.json"
GENERATED_AT = "2026-09-01T12:00:00Z"

REQUIRED_TOP_LEVEL = [
    "schemaVersion",
    "runId",
    "runIntent",
    "measurementSource",
    "configHash",
    "generatedAt",
    "candidateId",
    "foldSpec",
    "folds",
    "aggregate",
    "coverage",
]


def _load_test_universe(_market: str):
    from config import UniverseSymbol

    raw = json.loads(UNIVERSE.read_text(encoding="utf-8"))
    return [
        UniverseSymbol(
            symbol=item["symbol"],
            name_ko=item["name_ko"],
            name_en=item["name_en"],
            exchange=item["exchange"],
            currency=item["currency"],
            market_cap=item.get("market_cap"),
        )
        for item in raw
    ]


def _good_info(symbol: str) -> dict:
    return {
        "symbol": symbol,
        "shortName": symbol,
        "marketCap": 500_000_000_000,
        "revenueGrowth": 0.25,
        "earningsGrowth": 0.20,
        "trailingPE": 15,
        "pegRatio": 1.0,
        "returnOnEquity": 0.15,
        "debtToEquity": 50,
        "operatingMargins": 0.12,
        "bookValue": 100,
        "priceToBook": 1.5,
        "freeCashflow": 1_000_000,
        "operatingCashflow": 2_000_000,
    }


def _history_for_symbol(symbol: str, period: str = "1y"):
    import pandas as pd
    from tests.fixtures.price_loader import load_price_fixture

    if symbol == "LOOKAHEAD.KR":
        return load_price_fixture("lookahead_kr")
    dates = pd.date_range("2025-06-01", periods=200, freq="B")
    close = [100.0] * 74 + [80.0] * 52 + [92.0] * 74
    return pd.DataFrame({"Close": close}, index=dates)


def _stub_pit(_market: str, as_of_date: str, _exclude: set[str]):
    day = int(as_of_date.split("-")[2])
    if day % 3 == 0:
        return None, True
    return "SIMPLE.KR", False


def test_cli_help_exits_zero():
    result = subprocess.run(
        [sys.executable, "walk_forward.py", "--help"],
        cwd=SCRIPTS_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "run" in result.stdout


def test_smoke_fixture_recompute_offline(tmp_path, monkeypatch):
    monkeypatch.setattr("walk_forward.runner.pit_screen_day", _stub_pit)
    config_path = FIXTURES / "smoke-run-config.json"
    run_config = load_run_config(config_path)
    fold_spec = run_config.foldSpec
    sessions = build_decision_sessions(
        fold_spec["startDate"],
        fold_spec["endDate"],
        run_config.markets,
    )
    folds = generate_rolling_folds(fold_spec, sessions)

    daily_before = (
        {p.name: p.read_bytes() for p in DAILY_DIR.glob("*.json")} if DAILY_DIR.exists() else {}
    )

    report = execute_run(
        run_config,
        folds,
        output_dir=tmp_path,
        json_only=False,
        generated_at=GENERATED_AT,
        write=True,
    )

    for key in REQUIRED_TOP_LEVEL:
        assert key in report
    assert len(report["folds"]) >= 2
    assert report["measurementSource"] == "fixture-recompute"
    h20 = [h for h in report["aggregate"]["horizons"] if h["horizonId"] == "H20"]
    assert h20

    validator = load_validator(WALK_FORWARD_SCHEMA_PATH)
    assert not list(validator.iter_errors(report))

    if DAILY_DIR.exists():
        daily_after = {p.name: p.read_bytes() for p in DAILY_DIR.glob("*.json")}
        assert daily_after == daily_before


def test_smoke_deterministic_bytes(tmp_path, monkeypatch):
    monkeypatch.setattr("walk_forward.runner.pit_screen_day", _stub_pit)
    config_path = FIXTURES / "smoke-run-config.json"
    run_config = load_run_config(config_path)
    fold_spec = run_config.foldSpec
    sessions = build_decision_sessions(
        fold_spec["startDate"],
        fold_spec["endDate"],
        run_config.markets,
    )
    folds = generate_rolling_folds(fold_spec, sessions)

    r1 = execute_run(
        run_config,
        folds,
        output_dir=tmp_path / "a",
        json_only=True,
        generated_at=GENERATED_AT,
        write=False,
    )
    r2 = execute_run(
        run_config,
        folds,
        output_dir=tmp_path / "b",
        json_only=True,
        generated_at=GENERATED_AT,
        write=False,
    )
    assert serialize_report(r1) == serialize_report(r2)


def test_execute_default_generated_at_is_deterministic(tmp_path, monkeypatch):
    monkeypatch.setattr("walk_forward.runner.pit_screen_day", _stub_pit)
    config_path = FIXTURES / "smoke-run-config.json"
    run_config = load_run_config(config_path)
    fold_spec = run_config.foldSpec
    sessions = build_decision_sessions(
        fold_spec["startDate"],
        fold_spec["endDate"],
        run_config.markets,
    )
    folds = generate_rolling_folds(fold_spec, sessions)

    r1 = execute_run(run_config, folds, output_dir=tmp_path, write=False)
    r2 = execute_run(run_config, folds, output_dir=tmp_path, write=False)
    assert r1["generatedAt"] == f"{fold_spec['endDate']}T23:59:59Z"
    assert serialize_report(r1) == serialize_report(r2)


def test_contaminated_post_t_fails_lookahead(monkeypatch):
    """Post-t-only momentum must not win when PIT filter is applied."""
    monkeypatch.setattr("screening.core.load_universe", _load_test_universe)
    monkeypatch.setattr("screening.core.get_ticker_info", lambda s: _good_info(s))
    monkeypatch.setattr("screening.core.get_ticker_history", _history_for_symbol)

    symbol, no_pick = pit_screen_day("KR", "2026-01-08", set())
    assert not no_pick
    assert symbol == "GOOD.KR"
    assert symbol != "LOOKAHEAD.KR"
