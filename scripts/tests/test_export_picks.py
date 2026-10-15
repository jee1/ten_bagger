"""Tests for export_picks script (Issue #174)."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

# Add parent to sys.path for import
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_export_picks_schema_kr(tmp_path: Path):
    """KR export has required schema fields."""
    from export_picks import get_immature_picks, write_json
    
    ledger = {
        "market": "KR",
        "asOfDate": "2026-10-15",
        "entries": [
            {"pickDate": "2026-09-15", "symbol": "005930.KS", "status": "pick"},
            {"pickDate": "2026-08-01", "symbol": "000660.KS", "status": "pick"},
        ],
    }
    
    performance = {
        "measurements": [
            # H20 complete, H60 incomplete → immature
            {
                "pickDate": "2026-09-15",
                "symbol": "005930.KS",
                "horizonId": "H20",
                "completionStatus": "complete",
            },
            {
                "pickDate": "2026-09-15",
                "symbol": "005930.KS",
                "horizonId": "H60",
                "completionStatus": "incomplete",
            },
            # Both complete → mature (exclude)
            {
                "pickDate": "2026-08-01",
                "symbol": "000660.KS",
                "horizonId": "H20",
                "completionStatus": "complete",
            },
            {
                "pickDate": "2026-08-01",
                "symbol": "000660.KS",
                "horizonId": "H60",
                "completionStatus": "complete",
            },
        ]
    }
    
    immature = get_immature_picks(ledger, performance, "KR")
    
    assert len(immature) == 1
    pick = immature[0]
    assert pick["symbol"] == "005930.KS"
    assert pick["pickDate"] == "2026-09-15"
    assert "horizonsNeeded" in pick
    assert "H60" in pick["horizonsNeeded"]
    assert pick["latestHorizon"] == "H60"
    
    # Write and verify JSON structure
    export_data = {
        "schemaVersion": "0.1.0",
        "market": "KR",
        "asOfDate": "2026-10-15",
        "generatedAt": datetime.now(UTC).isoformat(),
        "count": len(immature),
        "picks": immature,
    }
    
    output = tmp_path / "test-kr.json"
    write_json(output, export_data)
    
    with output.open("r") as f:
        loaded = json.load(f)
    
    assert loaded["schemaVersion"] == "0.1.0"
    assert loaded["market"] == "KR"
    assert loaded["count"] == 1
    assert len(loaded["picks"]) == 1


def test_h20_incomplete_h60_complete():
    """Pick with only H20 incomplete is still immature."""
    from export_picks import get_immature_picks
    
    ledger = {
        "entries": [
            {"pickDate": "2026-10-10", "symbol": "123456.KS", "status": "pick"},
        ]
    }
    
    performance = {
        "measurements": [
            {
                "pickDate": "2026-10-10",
                "symbol": "123456.KS",
                "horizonId": "H20",
                "completionStatus": "incomplete",
            },
            {
                "pickDate": "2026-10-10",
                "symbol": "123456.KS",
                "horizonId": "H60",
                "completionStatus": "complete",
            },
        ]
    }
    
    immature = get_immature_picks(ledger, performance, "KR")
    
    assert len(immature) == 1
    assert "H20" in immature[0]["horizonsNeeded"]
    assert "H60" not in immature[0]["horizonsNeeded"]


def test_both_incomplete():
    """Pick with both H20 and H60 incomplete reports both."""
    from export_picks import get_immature_picks
    
    ledger = {
        "entries": [
            {"pickDate": "2026-10-14", "symbol": "AAPL", "status": "pick"},
        ]
    }
    
    performance = {
        "measurements": [
            {
                "pickDate": "2026-10-14",
                "symbol": "AAPL",
                "horizonId": "H20",
                "completionStatus": "incomplete",
            },
            {
                "pickDate": "2026-10-14",
                "symbol": "AAPL",
                "horizonId": "H60",
                "completionStatus": "incomplete",
            },
        ]
    }
    
    immature = get_immature_picks(ledger, performance, "US")
    
    assert len(immature) == 1
    assert set(immature[0]["horizonsNeeded"]) == {"H20", "H60"}
    assert immature[0]["latestHorizon"] == "H60"


def test_no_pick_excluded():
    """Entries with status='no_pick' are excluded."""
    from export_picks import get_immature_picks
    
    ledger = {
        "entries": [
            {"pickDate": "2026-10-12", "symbol": "", "status": "no_pick"},
            {"pickDate": "2026-10-13", "symbol": "MSFT", "status": "pick"},
        ]
    }
    
    performance = {
        "measurements": [
            {
                "pickDate": "2026-10-13",
                "symbol": "MSFT",
                "horizonId": "H20",
                "completionStatus": "incomplete",
            },
            {
                "pickDate": "2026-10-13",
                "symbol": "MSFT",
                "horizonId": "H60",
                "completionStatus": "incomplete",
            },
        ]
    }
    
    immature = get_immature_picks(ledger, performance, "US")
    
    assert len(immature) == 1
    assert immature[0]["symbol"] == "MSFT"


def test_missing_performance_data():
    """Pick without performance measurements is considered immature."""
    from export_picks import get_immature_picks
    
    ledger = {
        "entries": [
            {"pickDate": "2026-10-15", "symbol": "NEW.KS", "status": "pick"},
        ]
    }
    
    performance = {"measurements": []}
    
    immature = get_immature_picks(ledger, performance, "KR")
    
    assert len(immature) == 1
    assert immature[0]["symbol"] == "NEW.KS"


def test_us_market_symbols():
    """US market uses plain symbols without suffix."""
    from export_picks import get_immature_picks
    
    ledger = {
        "entries": [
            {"pickDate": "2026-09-20", "symbol": "TSLA", "status": "pick"},
        ]
    }
    
    performance = {
        "measurements": [
            {
                "pickDate": "2026-09-20",
                "symbol": "TSLA",
                "horizonId": "H20",
                "completionStatus": "complete",
            },
            {
                "pickDate": "2026-09-20",
                "symbol": "TSLA",
                "horizonId": "H60",
                "completionStatus": "incomplete",
            },
        ]
    }
    
    immature = get_immature_picks(ledger, performance, "US")
    
    assert len(immature) == 1
    assert immature[0]["symbol"] == "TSLA"
