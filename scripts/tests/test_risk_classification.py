"""Tests for Jev-based Top-N risk classification (Issue #147)."""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone

import generate_daily
import pytest
from config import COMPOSITE_THRESHOLD, SCORE_VERSION, UniverseSymbol
from reasoning import STATIC_RISKS, build_reasoning
from risk_classification import (
    apply_pick_risk_reasoning,
    cap_sdk_logger,
    classify_candidate_risk,
    classify_top_candidate_risks,
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
    return datetime(2026, 9, 21, 4, 0, 0, tzinfo=timezone.utc)


def test_classify_top_candidates_calls_at_most_five(monkeypatch):
    calls: list[str] = []

    def fake_classify(summary: str, input_at: str) -> tuple[str | None, dict]:
        calls.append(summary)
        return "regulation", {
            "model": "jev-1.13.0",
            "sdkVersion": "0.7.0",
            "inputAt": input_at,
            "tag": "regulation",
            "fallback": False,
        }

    monkeypatch.setenv("TYPESAFE_API_KEY", "test-key")
    # Passing 8 rows must only classify the top 5
    rows = [_candidate(f"S{i}", i) for i in range(1, 9)]
    enriched = classify_top_candidate_risks(
        rows,
        info_fetcher=lambda sym: {"longBusinessSummary": f"summary for {sym}"},
        classifier=fake_classify,
        now=_fixed_now,
    )
    assert len(enriched) == 8
    assert len(calls) == 5
    assert enriched[0]["riskTag"] == "regulation"
    assert "riskTag" not in enriched[5]

    # Passing 3 rows must only classify 3 (never exceed actual rows)
    calls.clear()
    few_rows = [_candidate(f"S{i}", i) for i in range(1, 4)]
    enriched_few = classify_top_candidate_risks(
        few_rows,
        info_fetcher=lambda sym: {"longBusinessSummary": f"summary for {sym}"},
        classifier=fake_classify,
        now=_fixed_now,
    )
    assert len(enriched_few) == 3
    assert len(calls) == 3


def test_success_renders_tag_and_pick_reasoning():
    from risk_classification import risk_text_for_tag

    text = risk_text_for_tag("debt_liquidity")
    assert text is not None
    top = [
        {
            **_candidate("PICK"),
            "riskTag": "debt_liquidity",
            "riskText": text,
            "riskClassification": {
                "model": "jev-1.13.0",
                "sdkVersion": "0.7.0",
                "inputAt": "2026-09-21T04:00:00+00:00",
                "tag": "debt_liquidity",
                "fallback": False,
            },
        }
    ]
    pick = _fake_pick("PICK")
    reasoning = build_reasoning(pick)
    merged = apply_pick_risk_reasoning(
        reasoning,
        pick_symbol="PICK",
        top_candidates=top,
    )
    assert merged["risks"][0]["en"] == "Debt burden and liquidity risk"
    assert merged["risks"][1:] == STATIC_RISKS


def test_missing_api_key_uses_static_pick_risks_only(monkeypatch):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    row = classify_candidate_risk(_candidate("A"), now=_fixed_now)
    assert row["riskClassification"]["fallback"] is True
    assert row["riskClassification"]["fallbackReason"] == "missing_api_key"
    assert "riskTag" not in row
    assert "tag" not in row["riskClassification"]

    reasoning = apply_pick_risk_reasoning(
        build_reasoning(_fake_pick("A")),
        pick_symbol="A",
        top_candidates=[row],
    )
    assert reasoning["risks"] == STATIC_RISKS


def test_whitespace_api_key_treated_as_missing(monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "   ")
    row = classify_candidate_risk(_candidate("A"), now=_fixed_now)
    assert row["riskClassification"]["fallback"] is True
    assert row["riskClassification"]["fallbackReason"] == "missing_api_key"
    assert "riskTag" not in row
    assert "tag" not in row["riskClassification"]


def test_api_failure_static_fallback_and_batch_succeeds(monkeypatch, content_dirs):
    import jsonschema
    from config import SCHEMA_PATH

    daily_dir, _manifest = content_dirs
    stats = _fake_stats()
    pick = _fake_pick("AAPL")

    def fail_classifier(_summary: str, input_at: str):
        raise RuntimeError("timeout")

    monkeypatch.setenv("TYPESAFE_API_KEY", "test-key")
    monkeypatch.setattr(
        generate_daily,
        "classify_top_candidate_risks",
        lambda rows: classify_top_candidate_risks(
            rows,
            info_fetcher=lambda _s: {"longBusinessSummary": "Retail bank"},
            classifier=fail_classifier,
            now=_fixed_now,
        ),
    )
    monkeypatch.setattr(generate_daily, "screen_market", lambda _m, _ex: ([pick], stats))
    monkeypatch.setattr(generate_daily, "get_ticker_info", lambda _s: {"longName": "Apple Inc"})
    monkeypatch.setattr(generate_daily, "build_stock_profile", lambda *_a, **_k: None)
    monkeypatch.setattr(sys, "argv", ["generate_daily.py", "2026-07-08"])

    assert generate_daily.main() == 0
    entry = json.loads((daily_dir / "2026-07-08.json").read_text(encoding="utf-8"))
    assert entry["status"] == "pick"
    assert entry["reasoning"]["risks"] == STATIC_RISKS
    assert entry["topCandidates"][0]["riskClassification"]["fallback"] is True
    assert "tag" not in entry["topCandidates"][0]["riskClassification"]

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(entry))
    assert errors == []


def test_provenance_recorded_on_success(monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "test-key")

    def ok(_summary: str, input_at: str) -> tuple[str | None, dict]:
        return "regulation", {
            "model": "jev-1.13.0",
            "sdkVersion": "0.7.0",
            "inputAt": input_at,
            "tag": "regulation",
            "fallback": False,
        }

    row = classify_candidate_risk(
        _candidate("REG"),
        info_fetcher=lambda _s: {"longBusinessSummary": "Insurance holding company"},
        classifier=ok,
        now=_fixed_now,
    )
    rc = row["riskClassification"]
    assert rc["model"] == "jev-1.13.0"
    assert rc["sdkVersion"] == "0.7.0"
    assert rc["inputAt"] == "2026-09-21T04:00:00+00:00"
    assert rc["tag"] == "regulation"
    assert rc["fallback"] is False
    assert row["riskTag"] == "regulation"


def test_pick_and_rank_invariants_unchanged(content_dirs, monkeypatch):
    daily_dir, _ = content_dirs
    stats = _fake_stats()
    pick = _fake_pick("AAPL")
    runner = _fake_pick("MSFT")
    runner.composite = 60.0

    monkeypatch.setattr(generate_daily, "screen_market", lambda _m, _ex: ([pick, runner], stats))
    monkeypatch.setattr(generate_daily, "get_ticker_info", lambda _s: {"longName": "x"})
    monkeypatch.setattr(generate_daily, "build_stock_profile", lambda *_a, **_k: None)
    monkeypatch.setattr(
        generate_daily,
        "classify_top_candidate_risks",
        lambda rows: [
            {**row, "riskTag": "regulation", "riskText": {"ko": "규제", "en": "Regulation"}}
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


def test_classify_handles_typesafe_rate_limit(monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "test-key")

    def fail(_summary: str, input_at: str):
        raise RuntimeError("TypeSafeRateLimitError")

    row = classify_candidate_risk(
        _candidate("X"),
        info_fetcher=lambda _s: {"longBusinessSummary": "Bank"},
        classifier=fail,
        now=_fixed_now,
    )
    assert row["riskClassification"]["fallback"] is True
    assert row["riskClassification"]["fallbackReason"] == "RuntimeError"


def test_info_fetcher_exception_falls_back(monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "test-key")

    def broken_fetcher(_sym: str):
        raise ConnectionError("network down")

    row = classify_candidate_risk(
        _candidate("X"),
        info_fetcher=broken_fetcher,
        now=_fixed_now,
    )
    assert row["riskClassification"]["fallback"] is True
    assert row["riskClassification"]["fallbackReason"] == "ConnectionError"
    assert "tag" not in row["riskClassification"]
    assert "riskTag" not in row


def test_classify_summary_typesafe_error_handling(monkeypatch):
    from risk_classification import _classify_summary
    from typesafe_sdk import (
        TypeSafeAPITimeoutError,
        TypeSafeInternalServerError,
        TypeSafeRateLimitError,
    )
    import httpx2

    class DummyClient:
        def __init__(self, exc):
            self.exc = exc
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def system_one(self, *args, **kwargs):
            raise self.exc

    headers = httpx2.Headers()
    for exc in [
        TypeSafeRateLimitError(429, {}, headers, "rate limited"),
        TypeSafeAPITimeoutError("request timed out"),
        TypeSafeInternalServerError(500, {}, headers, "server error"),
    ]:
        monkeypatch.setattr("typesafe_sdk.TypeSafeClient", lambda *a, **k: DummyClient(exc))
        tag, record = _classify_summary("Retail bank", input_at="2026-09-21T04:00:00+00:00")
        assert tag is None
        assert record["fallback"] is True
        assert record["fallbackReason"] == type(exc).__name__
        assert "tag" not in record


def test_sdk_logger_capped_at_warning_before_request_code_executes(monkeypatch):
    """Ensure business summaries cannot be emitted and SDK logger is capped (Issue #147)."""
    import httpx2
    from risk_classification import _classify_summary
    from typesafe_sdk import TypeSafeClient

    monkeypatch.setenv("TYPESAFE_LOG_LEVEL", "debug")
    sdk_logger = logging.getLogger("typesafe_sdk")
    sdk_logger.setLevel(logging.DEBUG)
    assert sdk_logger.level == logging.DEBUG

    captured_records: list[logging.LogRecord] = []

    class CaptureHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            captured_records.append(record)

    handler = CaptureHandler()
    sdk_logger.addHandler(handler)

    initial_root_level = logging.getLogger().level
    logger_level_at_construction: list[int] = []

    mock_response_data = {
        "model": "jev-1.13.0",
        "usage": {"requests": 1, "tokens": 10},
        "answers": {
            "business_risk": {
                "type": "choice",
                "choice": "customer_concentration",
                "confidence": 0.95,
                "probabilities": {"customer_concentration": 0.95},
            }
        },
    }
    mock_transport = httpx2.MockTransport(lambda req: httpx2.Response(200, json=mock_response_data))

    orig_client_cls = TypeSafeClient

    class TrackedClient(orig_client_cls):
        def __init__(self, *args, **kwargs):
            # Record logger level during TypeSafeClient construction, before any request runs
            logger_level_at_construction.append(logging.getLogger("typesafe_sdk").level)
            kwargs["transport"] = mock_transport
            kwargs["api_key"] = "test-secret-key-xyz"
            super().__init__(*args, **kwargs)

    monkeypatch.setattr("typesafe_sdk.TypeSafeClient", TrackedClient)

    secret_summary = "TOP_SECRET_PROPRIETARY_BUSINESS_SUMMARY_12345"
    try:
        tag, record = _classify_summary(secret_summary, input_at="2026-09-21T04:00:00+00:00")

        # Proves SDK logger is capped before request code executes (at TypeSafeClient construction)
        assert len(logger_level_at_construction) == 1
        assert logger_level_at_construction[0] == logging.WARNING
        assert sdk_logger.level == logging.WARNING

        assert tag == "customer_concentration"
        assert record["fallback"] is False

        # Proves no business summaries or secrets are emitted through the SDK logger
        for rec in captured_records:
            msg = rec.getMessage()
            assert secret_summary not in msg
            assert "test-secret-key-xyz" not in msg
        assert len(captured_records) == 0

        # Proves root logging was not changed
        assert logging.getLogger().level == initial_root_level
    finally:
        sdk_logger.removeHandler(handler)


def test_cap_sdk_logger_direct():
    sdk_logger = logging.getLogger("typesafe_sdk")
    for level in [logging.DEBUG, logging.INFO, logging.NOTSET]:
        sdk_logger.setLevel(level)
        capped = cap_sdk_logger()
        assert capped.level == logging.WARNING
        assert capped.isEnabledFor(logging.DEBUG) is False
        assert capped.isEnabledFor(logging.INFO) is False


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
