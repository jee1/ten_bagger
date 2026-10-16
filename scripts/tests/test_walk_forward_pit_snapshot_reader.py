"""Stage 2 (#175): override re-screen reads PIT fundamentals snapshots."""

from __future__ import annotations

import json

import pandas as pd
import pit_snapshot
import pytest
from config import WALK_FORWARD_SCHEMA_PATH, UniverseSymbol
from pit_snapshot import (
    PitManifestShaMismatchError,
    build_manifest_entry,
    extract_fundamental_row,
    upsert_manifest_entry,
    write_fundamentals_snapshot,
    write_universe_snapshot,
)
from validate_content import load_validator
from walk_forward import fundamentals_pit
from walk_forward.config import RunConfig
from walk_forward.fundamentals_pit import fundamentals_pit_audit, fundamentals_pit_status
from walk_forward.pit_screen import pit_screen_day
from walk_forward.report import build_report
from yf_cache import InfoProvenance

KNOWN = "2025-01-03T08:00:00+09:00"

FOLD_SPEC = {
    "mode": "rolling",
    "trainSessions": 2,
    "oosSessions": 1,
    "stepSessions": 1,
    "startDate": "2025-01-03",
    "endDate": "2025-01-09",
}

FOLDS = [
    {
        "foldIndex": 0,
        "trainRange": {"start": "2025-01-03", "end": "2025-01-07"},
        "oosRange": {"start": "2025-01-09", "end": "2025-01-09"},
        "trainSessions": ["2025-01-03", "2025-01-07"],
        "oosSessions": ["2025-01-09"],
        "status": "complete",
        "pickDays": 0,
        "noPickDays": 1,
        "picks": [],
        "measurements": [],
        "horizons": [],
    },
]


def _good_info(symbol: str) -> dict:
    return {
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


@pytest.fixture
def pit_store(tmp_path, monkeypatch):
    """Write snapshots as the daily run does; return a writer for (date, {symbol: info})."""
    data_dir = tmp_path / "pit-data"
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps({"schemaVersion": 1, "entries": []}), encoding="utf-8")
    universe_dir = tmp_path / "universe"
    universe_dir.mkdir()
    (universe_dir / "kr.json").write_text("[]", encoding="utf-8")
    monkeypatch.setattr(pit_snapshot, "UNIVERSE_DIR", universe_dir)
    monkeypatch.setattr(fundamentals_pit, "PIT_MANIFEST_PATH", manifest_path)
    monkeypatch.setenv("PIT_DATA_DIR", str(data_dir))
    fundamentals_pit._load.cache_clear()

    def write(date: str, infos: dict[str, dict], known_at: str = KNOWN) -> dict:
        prov = InfoProvenance(known_at=known_at, cache_hit=False)
        rows = [extract_fundamental_row(s, "KR", i, prov) for s, i in sorted(infos.items())]
        write_fundamentals_snapshot(rows, data_dir, "KR", date)
        write_universe_snapshot(
            {"date": date, "market": "KR", "builtAt": known_at, "symbols": sorted(infos)},
            data_dir,
            "KR",
            date,
        )
        entry = build_manifest_entry("KR", date, data_dir)
        manifest = upsert_manifest_entry(json.loads(manifest_path.read_text()), entry)
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        fundamentals_pit._load.cache_clear()
        return entry

    yield write
    fundamentals_pit._load.cache_clear()


def _override_config() -> RunConfig:
    return RunConfig(
        runIntent="exploratory",
        measurementSource="fixture-recompute",
        candidateId="growth-candidate",
        markets=["KR"],
        foldSpec=FOLD_SPEC,
        thresholdOverride=75.0,
    )


def test_covered_sessions_are_clean_and_report_provenance(pit_store):
    entries = [
        pit_store(d, {s: _good_info(s)})
        for d, s in [("2025-01-03", "A.KS"), ("2025-01-07", "B.KS")]
    ]

    report = build_report(
        run_config=_override_config(),
        fold_results=FOLDS,
        run_id="pit-stage2",
        generated_at="2025-01-31T23:59:59Z",
    )

    assert report["contaminationFindings"] == ["fundamentals_not_pit:1"]
    assert report["fundamentalsSnapshot"] == {
        "from": "2025-01-03",
        "to": "2025-01-07",
        "sha256": sorted(e["fundamentals"]["sha256"] for e in entries),
    }
    load_validator(WALK_FORWARD_SCHEMA_PATH).validate(report)


def test_all_sessions_covered_has_no_contamination(pit_store):
    for d in ("2025-01-03", "2025-01-07", "2025-01-09"):
        pit_store(d, {"AAA.KS": _good_info("AAA.KS")})
    findings, provenance = fundamentals_pit_audit(_override_config(), FOLDS)
    assert findings == []
    assert provenance is not None
    assert provenance["to"] == "2025-01-09"


def test_mostly_empty_snapshot_is_low_coverage(pit_store):
    infos = {f"S{i:02d}.KS": {} for i in range(19)}
    infos["AAA.KS"] = _good_info("AAA.KS")
    pit_store("2025-01-03", infos)
    assert fundamentals_pit_status("KR", "2025-01-03") == "low_coverage"


def test_rows_known_after_as_of_are_dropped(pit_store):
    pit_store("2025-01-03", {"AAA.KS": _good_info("AAA.KS")}, known_at="2025-01-04T00:00:01+09:00")
    snapshot = fundamentals_pit.load_fundamentals_snapshot("KR", "2025-01-03")
    assert snapshot is not None
    assert snapshot.infos == {}
    assert fundamentals_pit_status("KR", "2025-01-03") == "low_coverage"


def test_altered_local_snapshot_raises(pit_store, tmp_path):
    entry = pit_store("2025-01-03", {"AAA.KS": _good_info("AAA.KS")})
    path = tmp_path / "pit-data" / entry["fundamentals"]["path"]
    path.write_bytes(path.read_bytes() + b"x")
    fundamentals_pit._load.cache_clear()
    with pytest.raises(PitManifestShaMismatchError):
        fundamentals_pit_status("KR", "2025-01-03")


def test_pit_screen_uses_snapshot_info_and_universe(pit_store, monkeypatch):
    bad = {**_good_info("LIVE.KS"), "bookValue": -1}
    pit_store("2025-01-03", {"LIVE.KS": bad, "GONE.KS": _good_info("GONE.KS")})

    live_universe = [
        UniverseSymbol("LIVE.KS", "LIVE", "LIVE", "KOSPI", "KRW", 500_000_000_000),
        UniverseSymbol("NEW.KS", "NEW", "NEW", "KOSPI", "KRW", 500_000_000_000),
    ]
    dates = pd.date_range("2024-06-01", periods=200, freq="B")
    flat = pd.DataFrame({"Close": [100.0] * 74 + [80.0] * 52 + [92.0] * 74}, index=dates)
    monkeypatch.setattr("screening.core.load_universe", lambda _m: live_universe)
    monkeypatch.setattr("screening.core.get_ticker_info", lambda s: {"symbol": s, **_good_info(s)})
    monkeypatch.setattr("screening.core.get_ticker_history", lambda s, period="1y": flat)

    symbol, no_pick = pit_screen_day("KR", "2025-01-03", set())
    assert (symbol, no_pick) == ("GONE.KS", False)

    live_symbol, _ = pit_screen_day("KR", "2025-01-02", set())
    assert live_symbol in {"LIVE.KS", "NEW.KS"}
