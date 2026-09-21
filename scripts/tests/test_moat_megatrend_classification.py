"""Tests for observational moat/megatrend classification (Issue #149)."""

from __future__ import annotations

import inspect
import json
import sys
from datetime import UTC, datetime

import generate_daily
import pytest
from config import SCHEMA_PATH, SCORE_VERSION, UniverseSymbol
from moat_megatrend_classification import (
    classify_candidate_moat_megatrend,
    classify_top_candidate_moat_megatrend,
    megatrend_text_for_theme,
    moat_text_for_width,
)
from screen import ScoreResult, ScreenStats


def _candidate(symbol: str, rank: int = 1) -> dict:
    return {
        "rank": rank,
        "symbol": symbol,
        "name": {"ko": symbol, "en": symbol},
        "exchange": "NASDAQ",
        "currency": "USD",
        "scores": {
            "composite": 80.0,
            "size": 80.0,
            "growth": 80.0,
            "valuation": 80.0,
            "entry": 80.0,
            "momentum": 80.0,
            "quality": 80.0,
            "version": SCORE_VERSION,
        },
    }


def _fixed_now() -> datetime:
    return datetime(2026, 9, 21, 4, 0, 0, tzinfo=UTC)


def _success_record(tag: str, input_at: str) -> dict:
    return {
        "model": "jev-1.13.0",
        "sdkVersion": "0.7.0",
        "inputAt": input_at,
        "tag": tag,
        "fallback": False,
    }


def test_success_maps_moat_and_megatrend_choices():
    def ok(_summary: str, input_at: str):
        return (
            "wide",
            _success_record("wide", input_at),
            "robotics",
            _success_record("robotics", input_at),
        )

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("TYPESAFE_API_KEY", "test-key")
    try:
        row = classify_candidate_moat_megatrend(
            _candidate("BOT"),
            info_fetcher=lambda _s: {"longBusinessSummary": "Industrial robotics OEM"},
            classifier=ok,
            now=_fixed_now,
        )
    finally:
        monkeypatch.undo()

    assert row["moatWidth"] == "wide"
    assert row["megatrendTheme"] == "robotics"
    assert row["moatText"] == moat_text_for_width("wide")
    assert row["megatrendText"] == megatrend_text_for_theme("robotics")
    assert row["moatClassification"]["fallback"] is False
    assert row["megatrendClassification"]["fallback"] is False


def test_classify_top_candidates_calls_at_most_five():
    calls: list[str] = []

    def fake_classify(summary: str, input_at: str):
        calls.append(summary)
        return (
            "narrow",
            _success_record("narrow", input_at),
            "ai_infrastructure",
            _success_record("ai_infrastructure", input_at),
        )

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("TYPESAFE_API_KEY", "test-key")
    try:
        rows = [_candidate(f"S{i}", i) for i in range(1, 9)]
        enriched = classify_top_candidate_moat_megatrend(
            rows,
            info_fetcher=lambda sym: {"longBusinessSummary": f"summary for {sym}"},
            classifier=fake_classify,
            now=_fixed_now,
        )
        assert len(enriched) == 8
        assert len(calls) == 5
        assert enriched[0]["moatWidth"] == "narrow"
        assert "moatWidth" not in enriched[5]
    finally:
        monkeypatch.undo()


def test_missing_api_key_hides_tags(monkeypatch):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    row = classify_candidate_moat_megatrend(_candidate("A"), now=_fixed_now)
    assert row["moatClassification"]["fallback"] is True
    assert row["megatrendClassification"]["fallback"] is True
    assert row["moatClassification"]["fallbackReason"] == "missing_api_key"
    assert "moatWidth" not in row
    assert "megatrendTheme" not in row


def test_missing_summary_skips_model_call(monkeypatch):
    calls = 0

    def should_not_run(_summary: str, _input_at: str):
        nonlocal calls
        calls += 1
        raise AssertionError("classifier must not run without summary")

    monkeypatch.setenv("TYPESAFE_API_KEY", "test-key")
    row = classify_candidate_moat_megatrend(
        _candidate("A"),
        info_fetcher=lambda _s: {},
        classifier=should_not_run,
        now=_fixed_now,
    )
    assert calls == 0
    assert row["moatClassification"]["fallbackReason"] == "missing_summary"
    assert "moatWidth" not in row


def test_api_failure_preserves_generation_and_schema(content_dirs, monkeypatch):
    import jsonschema

    daily_dir, _manifest = content_dirs
    stats = _fake_stats()
    pick = _fake_pick("AAPL")

    def fail_classifier(_summary: str, input_at: str):
        raise RuntimeError("timeout")

    monkeypatch.setenv("TYPESAFE_API_KEY", "test-key")
    monkeypatch.setattr(
        generate_daily,
        "classify_top_candidate_moat_megatrend",
        lambda rows: classify_top_candidate_moat_megatrend(
            rows,
            info_fetcher=lambda _s: {"longBusinessSummary": "Cloud AI platform"},
            classifier=fail_classifier,
            now=_fixed_now,
        ),
    )
    monkeypatch.setattr(generate_daily, "screen_market", lambda _m, _ex: ([pick], stats))
    monkeypatch.setattr(generate_daily, "get_ticker_info", lambda _s: {"longName": "Apple Inc"})
    monkeypatch.setattr(generate_daily, "build_stock_profile", lambda *_a, **_k: None)
    monkeypatch.setattr(
        generate_daily,
        "classify_top_candidate_risks",
        lambda rows: rows,
    )
    monkeypatch.setattr(sys, "argv", ["generate_daily.py", "2026-07-08"])

    assert generate_daily.main() == 0
    entry = json.loads((daily_dir / "2026-07-08.json").read_text(encoding="utf-8"))
    assert entry["status"] == "pick"
    assert entry["stock"]["symbol"] == "AAPL"
    assert entry["topCandidates"][0]["moatClassification"]["fallback"] is True
    assert "moatWidth" not in entry["topCandidates"][0]

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert list(jsonschema.Draft202012Validator(schema).iter_errors(entry)) == []


def test_pick_and_rank_invariants_unchanged(content_dirs, monkeypatch):
    daily_dir, _ = content_dirs
    stats = _fake_stats()
    pick = _fake_pick("AAPL")
    runner = _fake_pick("MSFT")
    runner.composite = 60.0

    monkeypatch.setattr(generate_daily, "screen_market", lambda _m, _ex: ([pick, runner], stats))
    monkeypatch.setattr(generate_daily, "get_ticker_info", lambda _s: {"longName": "x"})
    monkeypatch.setattr(generate_daily, "build_stock_profile", lambda *_a, **_k: None)
    monkeypatch.setattr(generate_daily, "classify_top_candidate_risks", lambda rows: rows)
    monkeypatch.setattr(
        generate_daily,
        "classify_top_candidate_moat_megatrend",
        lambda rows: [
            {
                **row,
                "moatWidth": "wide",
                "moatText": moat_text_for_width("wide"),
                "megatrendTheme": "power_grid",
                "megatrendText": megatrend_text_for_theme("power_grid"),
            }
            for row in rows
        ],
    )
    monkeypatch.setattr(sys, "argv", ["generate_daily.py", "2026-07-08"])

    assert generate_daily.main() == 0
    entry = json.loads((daily_dir / "2026-07-08.json").read_text(encoding="utf-8"))
    assert entry["stock"]["symbol"] == "AAPL"
    assert entry["topCandidates"][0]["symbol"] == "AAPL"
    assert entry["topCandidates"][0]["rank"] == 1
    assert entry["topCandidates"][1]["symbol"] == "MSFT"
    assert entry["scores"]["composite"] == 76.5


def test_generate_daily_moat_runs_after_pick_selection():
    main_src = inspect.getsource(generate_daily.main)
    assert main_src.index("select_pick") < main_src.index("classify_top_candidate_moat_megatrend")
    assert "classify_top_candidate_moat_megatrend" not in inspect.getsource(
        generate_daily.build_pick
    )
    assert "classify_top_candidate_moat_megatrend" not in inspect.getsource(
        generate_daily.build_no_pick
    )


def _fake_stats(**kwargs) -> ScreenStats:
    defaults: dict = {
        "screened": 10,
        "passed_threshold": 1,
        "skipped_recent": 0,
        "skipped_market_cap": 0,
        "skipped_red_flags": 0,
        "no_data": 0,
        "errors": 0,
    }
    defaults.update(kwargs)
    return ScreenStats(**defaults)


def _fake_pick(symbol: str = "TEST") -> ScoreResult:
    meta = UniverseSymbol(symbol, "테스트", "Test Co", "NASDAQ", "USD")
    return ScoreResult(
        symbol=symbol,
        meta=meta,
        size=80.0,
        growth=75.0,
        valuation=78.0,
        entry=70.0,
        momentum=65.0,
        quality=72.0,
        composite=76.5,
        metrics={},
        score_version=SCORE_VERSION,
    )


@pytest.fixture
def content_dirs(tmp_path, monkeypatch):
    daily_dir = tmp_path / "daily"
    daily_dir.mkdir()
    manifest_path = tmp_path / "manifest.json"

    monkeypatch.setattr(generate_daily, "DAILY_DIR", daily_dir)
    monkeypatch.setattr("sync_manifest.DAILY_DIR", daily_dir)
    monkeypatch.setattr("sync_manifest.MANIFEST_PATH", manifest_path)

    return daily_dir, manifest_path
