"""Integration tests for generate_daily pipeline."""

from __future__ import annotations

import json
import sys
from datetime import date

import pytest

import generate_daily
from config import COMPOSITE_THRESHOLD, SCORE_VERSION, UniverseSymbol
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

    return daily_dir, manifest_path


def test_generate_daily_writes_pick_and_syncs_manifest(content_dirs, monkeypatch):
    daily_dir, manifest_path = content_dirs
    stats = _fake_stats()
    pick = _fake_pick("AAPL")

    monkeypatch.setattr(generate_daily, "screen_market", lambda _m, _ex: ([pick], stats))
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

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "2026-07-08" in manifest["dates"]


def test_generate_daily_writes_no_pick(content_dirs, monkeypatch):
    daily_dir, manifest_path = content_dirs
    stats = _fake_stats(passed_threshold=0)

    monkeypatch.setattr(generate_daily, "screen_market", lambda _m, _ex: ([], stats))
    monkeypatch.setattr(sys, "argv", ["generate_daily.py", "2026-07-09"])

    assert generate_daily.main() == 0

    entry = json.loads((daily_dir / "2026-07-09.json").read_text(encoding="utf-8"))
    assert entry["status"] == "no_pick"
    assert entry["market"] == "KR"  # odd day (9th)
    assert entry["scores"]["composite"] == 0
    assert entry["meta"]["candidatesScreened"] == 10

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["dates"] == ["2026-07-09"]


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
