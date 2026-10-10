"""Tests for PIT snapshot capture (issue #175 stage 1)."""

from __future__ import annotations

import json
import time

import pit_snapshot
import pytest
import yf_cache
from config import PIT_MANIFEST_PATH
from pit_snapshot import (
    PitFundamentalsCollector,
    PitManifestShaMismatchError,
    PitSnapshotExistsError,
    extract_fundamental_row,
    load_pending_manifest_entry,
    push_and_record_manifest,
    push_staging_to_pit_repo,
    sha256_file,
    verify_file_sha256,
    write_daily_pit_snapshots,
    write_fundamentals_snapshot,
)
from pit_snapshot import (
    main as pit_snapshot_main,
)
from yf_cache import InfoProvenance


def _sample_info(symbol: str = "TEST") -> dict:
    return {
        "symbol": symbol,
        "shortName": "Test",
        "marketCap": 1_000_000,
        "trailingPE": 12.5,
    }


def test_extract_fundamental_row_includes_scoring_fields_only():
    prov = InfoProvenance(known_at="2026-01-01T00:00:00+09:00", cache_hit=True)
    row = extract_fundamental_row("AAA", "KR", _sample_info(), prov)
    assert row["symbol"] == "AAA"
    assert row["knownAt"] == "2026-01-01T00:00:00+09:00"
    assert row["cacheHit"] is True
    assert row["marketCap"] == 1_000_000
    assert "longBusinessSummary" not in row


def test_get_ticker_info_provenance_uses_cached_fetched_at_not_mtime(monkeypatch, tmp_path):
    path = tmp_path / "TEST_info.json"
    fetched = "2020-06-15T08:30:00+09:00"
    path.write_text(
        json.dumps({"info": {"longName": "Cached"}, "fetchedAt": fetched}),
        encoding="utf-8",
    )
    old_time = time.time() - 10_000
    import os

    os.utime(path, (old_time, old_time))

    class RateLimitedTicker:
        @property
        def info(self) -> dict[str, str]:
            raise RuntimeError("429 Too Many Requests")

    monkeypatch.setattr(yf_cache, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(yf_cache, "CACHE_TTL_SECONDS", 1)
    monkeypatch.setattr(yf_cache, "YF_MAX_RETRIES", 1)
    monkeypatch.setattr(yf_cache.yf, "Ticker", lambda _symbol: RateLimitedTicker())

    info, prov = yf_cache.get_ticker_info_with_provenance("TEST")
    assert info["longName"] == "Cached"
    assert prov.known_at == fetched
    assert prov.cache_hit is False


def test_write_fundamentals_refuses_overwrite(tmp_path):
    collector = PitFundamentalsCollector(market="KR")
    prov = InfoProvenance(known_at="2026-01-01T00:00:00+09:00", cache_hit=False)
    collector.record("AAA", _sample_info(), prov)
    rows = list(collector.rows.values())
    write_fundamentals_snapshot(rows, tmp_path, "KR", "2026-01-02")
    with pytest.raises(PitSnapshotExistsError):
        write_fundamentals_snapshot(rows, tmp_path, "KR", "2026-01-02")


def test_verify_file_sha256_mismatch(tmp_path):
    path = tmp_path / "blob.gz"
    path.write_bytes(b"abc")
    with pytest.raises(PitManifestShaMismatchError):
        verify_file_sha256(path, "0" * 64)


def test_content_pit_manifest_has_valid_structure():
    manifest = json.loads(PIT_MANIFEST_PATH.read_text(encoding="utf-8"))
    entries = manifest.get("entries", [])
    
    assert isinstance(entries, list)
    assert "schemaVersion" in manifest
    
    for entry in entries:
        assert "date" in entry
        assert "market" in entry
        assert "fundamentals" in entry
        assert "universe" in entry
        
        fund = entry["fundamentals"]
        assert "path" in fund
        assert "sha256" in fund
        assert "bytes" in fund
        assert "rowCount" in fund
        assert "knownAtMin" in fund
        assert "knownAtMax" in fund
        
        univ = entry["universe"]
        assert "path" in univ
        assert "sha256" in univ
        assert "bytes" in univ
        assert "symbolCount" in univ
        assert "builtAt" in univ


def test_write_daily_pit_snapshots_staging_only_not_public_manifest(tmp_path, monkeypatch):
    pit_manifest = tmp_path / "manifest.json"
    staging = tmp_path / "staging"
    universe_dir = tmp_path / "universe"
    universe_dir.mkdir()
    (universe_dir / "kr.json").write_text(
        json.dumps([{"symbol": "AAA.KS"}]),
        encoding="utf-8",
    )
    monkeypatch.setattr("pit_snapshot.PIT_MANIFEST_PATH", pit_manifest)
    monkeypatch.setattr("pit_snapshot.UNIVERSE_DIR", universe_dir)

    collector = PitFundamentalsCollector(market="KR")
    prov = InfoProvenance(known_at="2026-01-01T00:00:00+09:00", cache_hit=True)
    collector.record("AAA.KS", _sample_info("AAA.KS"), prov)

    result = write_daily_pit_snapshots("2026-01-02", "KR", collector, staging_dir=staging)
    assert not result.skipped
    assert result.manifest_entry is not None
    f_path = staging / result.manifest_entry["fundamentals"]["path"]
    assert f_path.exists()
    assert sha256_file(f_path) == result.manifest_entry["fundamentals"]["sha256"]

    assert not pit_manifest.exists()
    pending = load_pending_manifest_entry("KR", "2026-01-02", staging_dir=staging)
    assert pending is not None
    assert pending["fundamentals"]["sha256"] == result.manifest_entry["fundamentals"]["sha256"]

    again = write_daily_pit_snapshots("2026-01-02", "KR", collector, staging_dir=staging)
    assert again.skipped


def test_manifest_updated_only_after_successful_push(tmp_path, monkeypatch):
    pit_manifest = tmp_path / "manifest.json"
    staging = tmp_path / "staging"
    universe_dir = tmp_path / "universe"
    universe_dir.mkdir()
    (universe_dir / "kr.json").write_text(json.dumps([{"symbol": "AAA.KS"}]), encoding="utf-8")
    monkeypatch.setattr(pit_snapshot, "PIT_MANIFEST_PATH", pit_manifest)
    monkeypatch.setattr(pit_snapshot, "UNIVERSE_DIR", universe_dir)

    collector = PitFundamentalsCollector(market="KR")
    prov = InfoProvenance(known_at="2026-01-01T00:00:00+09:00", cache_hit=True)
    collector.record("AAA.KS", _sample_info("AAA.KS"), prov)
    write_daily_pit_snapshots("2026-01-03", "KR", collector, staging_dir=staging)
    assert not pit_manifest.exists()

    assert not push_and_record_manifest("2026-01-03", "KR", token=None, staging_dir=staging)
    assert not pit_manifest.exists()

    monkeypatch.setattr(
        pit_snapshot,
        "push_staging_to_pit_repo",
        lambda *_a, **_k: True,
    )
    assert push_and_record_manifest("2026-01-03", "KR", token="fake-token", staging_dir=staging)
    manifest = json.loads(pit_manifest.read_text(encoding="utf-8"))
    assert len(manifest["entries"]) == 1
    assert manifest["entries"][0]["date"] == "2026-01-03"


def test_push_failure_does_not_update_manifest(tmp_path, monkeypatch):
    pit_manifest = tmp_path / "manifest.json"
    staging = tmp_path / "staging"
    universe_dir = tmp_path / "universe"
    universe_dir.mkdir()
    (universe_dir / "kr.json").write_text(json.dumps([{"symbol": "AAA.KS"}]), encoding="utf-8")
    monkeypatch.setattr(pit_snapshot, "PIT_MANIFEST_PATH", pit_manifest)
    monkeypatch.setattr(pit_snapshot, "UNIVERSE_DIR", universe_dir)

    collector = PitFundamentalsCollector(market="KR")
    prov = InfoProvenance(known_at="2026-01-01T00:00:00+09:00", cache_hit=True)
    collector.record("AAA.KS", _sample_info("AAA.KS"), prov)
    write_daily_pit_snapshots("2026-01-04", "KR", collector, staging_dir=staging)

    def boom(*_a, **_k):
        raise RuntimeError("git push failed (exit 1): denied")

    monkeypatch.setattr(pit_snapshot, "push_staging_to_pit_repo", boom)
    assert not push_and_record_manifest("2026-01-04", "KR", token="fake-token", staging_dir=staging)
    assert not pit_manifest.exists()


def test_pit_snapshot_main_survives_push_failure(monkeypatch):
    monkeypatch.setenv("PIT_TARGET_DATE", "2026-07-08")
    monkeypatch.setenv("PIT_DATA_TOKEN", "fake-token")

    def boom(*_a, **_k):
        raise RuntimeError("simulated push failure")

    monkeypatch.setattr(pit_snapshot, "push_and_record_manifest", boom)
    assert pit_snapshot_main() == 0


def test_push_staging_without_token_returns_false(tmp_path):
    assert push_staging_to_pit_repo(tmp_path, token=None) is False
