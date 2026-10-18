"""Integration tests for generate_daily pipeline."""

from __future__ import annotations

import json
import sys
from datetime import date, datetime

import generate_daily
import pytest
from config import COMPOSITE_THRESHOLD, SCORE_VERSION, UniverseSymbol
from pit_snapshot import PitWriteResult
from screen import ScoreResult, ScreenStats


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
    monkeypatch.setattr(
        generate_daily,
        "write_daily_pit_snapshots",
        lambda *_a, **_k: PitWriteResult(skipped=True, reason="test"),
    )

    return daily_dir, manifest_path


def test_generate_daily_writes_pick_and_syncs_manifest(content_dirs, monkeypatch):
    daily_dir, manifest_path = content_dirs
    stats = _fake_stats()
    pick = _fake_pick("AAPL")
    runner = _fake_pick("MSFT")
    runner.composite = 60.0  # below threshold near-miss

    monkeypatch.setattr(
        generate_daily, "screen_market", lambda _m, _ex, **_k: ([pick, runner], stats)
    )
    monkeypatch.setattr(generate_daily, "get_ticker_info", lambda _s: {"longName": "Apple Inc"})
    monkeypatch.setattr(generate_daily, "build_stock_profile", lambda *_a, **_k: None)
    monkeypatch.setattr(sys, "argv", ["generate_daily.py", "2026-07-08"])

    assert generate_daily.main() == 0

    out = daily_dir / "2026-07-08.json"
    assert out.exists()
    entry = json.loads(out.read_text(encoding="utf-8"))
    assert entry["status"] == "pick"
    assert entry["stock"]["symbol"] == "AAPL"
    assert entry["scores"]["composite"] == 76.5
    assert entry["scores"]["threshold"] == COMPOSITE_THRESHOLD
    assert entry["market"] == "US"  # even day (8th)
    assert entry["topCandidates"][0]["symbol"] == "AAPL"
    assert entry["topCandidates"][0]["rank"] == 1
    assert len(entry["topCandidates"]) == 2
    assert entry["topCandidates"][1]["symbol"] == "MSFT"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "2026-07-08" in manifest["dates"]

    import jsonschema
    from config import SCHEMA_PATH

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(entry))
    assert errors == []


def test_generate_daily_writes_no_pick(content_dirs, monkeypatch):
    daily_dir, manifest_path = content_dirs
    stats = _fake_stats(passed_threshold=0)

    monkeypatch.setattr(generate_daily, "screen_market", lambda _m, _ex, **_k: ([], stats))
    monkeypatch.setattr(sys, "argv", ["generate_daily.py", "2026-07-09"])

    assert generate_daily.main() == 0

    entry = json.loads((daily_dir / "2026-07-09.json").read_text(encoding="utf-8"))
    assert entry["status"] == "no_pick"
    assert entry["market"] == "KR"  # odd day (9th)
    assert entry["scores"]["composite"] == 0
    assert entry["meta"]["candidatesScreened"] == 10
    assert "topCandidates" not in entry

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["dates"] == ["2026-07-09"]


def test_generate_daily_no_pick_with_near_miss_top_n(content_dirs, monkeypatch):
    daily_dir, _manifest = content_dirs
    stats = _fake_stats(passed_threshold=0)
    near = _fake_pick("NEAR")
    near.composite = 55.0

    monkeypatch.setattr(generate_daily, "screen_market", lambda _m, _ex, **_k: ([near], stats))
    monkeypatch.setattr(sys, "argv", ["generate_daily.py", "2026-07-09"])

    assert generate_daily.main() == 0
    entry = json.loads((daily_dir / "2026-07-09.json").read_text(encoding="utf-8"))
    assert entry["status"] == "no_pick"
    assert "topCandidates" in entry
    assert entry["topCandidates"][0]["symbol"] == "NEAR"
    assert entry["topCandidates"][0]["scores"]["composite"] == 55.0


def test_recent_pick_symbols_excludes_recent_picks(content_dirs, monkeypatch):
    daily_dir, _ = content_dirs
    past = {
        "date": "2026-07-01",
        "status": "pick",
        "stock": {"symbol": "OLD.KS"},
    }
    (daily_dir / "2026-07-01.json").write_text(json.dumps(past), encoding="utf-8")

    excluded = generate_daily.recent_pick_symbols(30, date.fromisoformat("2026-07-05"))
    assert "OLD.KS" in excluded


def test_recent_pick_symbols_ignores_outside_window(content_dirs, monkeypatch):
    daily_dir, _ = content_dirs
    old = {
        "date": "2026-05-01",
        "status": "pick",
        "stock": {"symbol": "STALE.KS"},
    }
    (daily_dir / "2026-05-01.json").write_text(json.dumps(old), encoding="utf-8")

    excluded = generate_daily.recent_pick_symbols(30, date.fromisoformat("2026-07-05"))
    assert "STALE.KS" not in excluded


def test_recent_pick_symbols_excludes_later_picks_for_backfill(content_dirs, monkeypatch):
    daily_dir, _ = content_dirs
    later = {
        "date": "2026-10-12",
        "status": "pick",
        "stock": {"symbol": "EVER"},
    }
    (daily_dir / "2026-10-12.json").write_text(json.dumps(later), encoding="utf-8")

    excluded = generate_daily.recent_pick_symbols(30, date.fromisoformat("2026-10-10"))
    assert "EVER" in excluded


def test_recent_pick_symbols_ignores_own_date_on_rerun(content_dirs, monkeypatch):
    daily_dir, _ = content_dirs
    same = {
        "date": "2026-10-12",
        "status": "pick",
        "stock": {"symbol": "EVER"},
    }
    (daily_dir / "2026-10-12.json").write_text(json.dumps(same), encoding="utf-8")

    excluded = generate_daily.recent_pick_symbols(30, date.fromisoformat("2026-10-12"))
    assert "EVER" not in excluded


def test_generate_daily_rejects_weekend_target(content_dirs, monkeypatch):
    daily_dir, _ = content_dirs
    monkeypatch.setattr(sys, "argv", ["generate_daily.py", "2026-10-10"])

    with pytest.raises(SystemExit, match="weekend"):
        generate_daily.main()
    assert not (daily_dir / "2026-10-10.json").exists()


@pytest.mark.parametrize(("today", "captured"), [("2026-07-09", True), ("2026-07-13", False)])
def test_pit_snapshot_only_for_same_day_run(content_dirs, monkeypatch, today, captured):
    calls = []
    monkeypatch.setattr(
        generate_daily,
        "write_daily_pit_snapshots",
        lambda *a, **_k: calls.append(a) or PitWriteResult(skipped=True, reason="test"),
    )
    monkeypatch.setattr(
        generate_daily,
        "now_kst",
        lambda: datetime.fromisoformat(f"{today}T06:00:00+09:00"),
    )
    monkeypatch.setattr(
        generate_daily, "screen_market", lambda _m, _ex, **_k: ([], _fake_stats(passed_threshold=0))
    )
    monkeypatch.setattr(sys, "argv", ["generate_daily.py", "2026-07-09"])

    assert generate_daily.main() == 0
    assert bool(calls) is captured


def test_generate_daily_refuses_publish_when_provider_error_rate_is_high(content_dirs, monkeypatch):
    daily_dir, manifest_path = content_dirs
    stats = _fake_stats(screened=10, errors=2, no_data=1, passed_threshold=0)

    monkeypatch.setattr(generate_daily, "screen_market", lambda _m, _ex, **_k: ([], stats))
    monkeypatch.setattr(sys, "argv", ["generate_daily.py", "2026-07-09"])

    assert generate_daily.main() != 0
    assert not (daily_dir / "2026-07-09.json").exists()
    assert not manifest_path.exists()


def test_generate_daily_writes_no_pick_when_provider_error_rate_is_at_threshold(
    content_dirs, monkeypatch
):
    daily_dir, manifest_path = content_dirs
    stats = _fake_stats(screened=10, errors=2, no_data=0, passed_threshold=0)

    monkeypatch.setattr(generate_daily, "screen_market", lambda _m, _ex, **_k: ([], stats))
    monkeypatch.setattr(sys, "argv", ["generate_daily.py", "2026-07-09"])

    assert generate_daily.main() == 0
    entry = json.loads((daily_dir / "2026-07-09.json").read_text(encoding="utf-8"))
    assert entry["status"] == "no_pick"
    assert entry["meta"]["errors"] == 2
    assert entry["meta"]["noData"] == 0
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["dates"] == ["2026-07-09"]


def test_recent_pick_symbols_raises_on_corrupt_daily_json(content_dirs):
    daily_dir, _ = content_dirs
    bad = daily_dir / "2026-07-01.json"
    bad.write_text("{not-json", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError, match="2026-07-01.json"):
        generate_daily.recent_pick_symbols(30, date.fromisoformat("2026-07-05"))
