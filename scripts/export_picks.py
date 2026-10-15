#!/usr/bin/env python3
"""Export immature picks (H20/H60 not yet matured) for finnaut-ohlc.

Reads content/ledger/{KR,US}.json and content/performance/{KR,US}.json
to produce tenbagger-picks-{kr,us}.json for external price collection.

Issue #174: https://github.com/jee1/ten_bagger/issues/174
Consumer: https://github.com/jee1/finnaut-ohlc/issues/4
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    """Load and return JSON file."""
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: dict[str, Any]) -> None:
    """Write JSON with trailing newline."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def get_immature_picks(
    ledger: dict[str, Any],
    performance: dict[str, Any],
    market: str,
) -> list[dict[str, Any]]:
    """Extract picks where H20 or H60 haven't matured yet.

    Returns list of picks with symbol, pickDate, and latest horizon end date.
    Only includes picks with status='pick' (skip no_pick entries).
    """
    immature: list[dict[str, Any]] = []

    # Build index: (pickDate, symbol, horizonId) -> measurement
    perf_index: dict[tuple[str, str, str], dict[str, Any]] = {}
    for m in performance.get("measurements", []):
        key = (m["pickDate"], m["symbol"], m["horizonId"])
        perf_index[key] = m

    for entry in ledger.get("entries", []):
        # Skip no_pick entries
        if entry.get("status") != "pick":
            continue

        pick_date = entry["pickDate"]
        symbol = entry["symbol"]

        # Check H20 and H60 completion status
        h20_key = (pick_date, symbol, "H20")
        h60_key = (pick_date, symbol, "H60")

        h20 = perf_index.get(h20_key)
        h60 = perf_index.get(h60_key)

        # If either H20 or H60 is incomplete, this pick is immature
        h20_incomplete = h20 is None or h20.get("completionStatus") != "complete"
        h60_incomplete = h60 is None or h60.get("completionStatus") != "complete"

        if h20_incomplete or h60_incomplete:
            # Determine the latest horizon end date needed
            # H20 = entry + 20 sessions, H60 = entry + 60 sessions
            # We report which horizon is still pending
            horizons_needed = []
            if h20_incomplete:
                horizons_needed.append("H20")
            if h60_incomplete:
                horizons_needed.append("H60")

            immature.append(
                {
                    "symbol": symbol,
                    "pickDate": pick_date,
                    "horizonsNeeded": horizons_needed,
                    "latestHorizon": "H60" if h60_incomplete else "H20",
                }
            )

    return immature


def main() -> None:
    """Generate tenbagger-picks-{kr,us}.json for finnaut-ohlc."""
    root = Path(__file__).parent.parent

    for market_code in ["KR", "US"]:
        ledger_path = root / "content" / "ledger" / f"{market_code}.json"
        perf_path = root / "content" / "performance" / f"{market_code}.json"

        if not ledger_path.exists() or not perf_path.exists():
            print(f"⚠️  Skipping {market_code}: missing ledger or performance file")
            continue

        ledger = load_json(ledger_path)
        performance = load_json(perf_path)

        immature = get_immature_picks(ledger, performance, market_code)

        # Build export
        as_of_date = ledger.get("asOfDate", "unknown")
        export_data = {
            "schemaVersion": "0.1.0",
            "market": market_code,
            "asOfDate": as_of_date,
            "generatedAt": datetime.now(UTC).isoformat(),
            "count": len(immature),
            "picks": immature,
        }

        # Write to content/exports/
        output_path = root / "content" / "exports" / f"tenbagger-picks-{market_code.lower()}.json"
        write_json(output_path, export_data)

        print(f"✓ {market_code}: {len(immature)} immature picks → {output_path}")


if __name__ == "__main__":
    main()
