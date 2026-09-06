"""Eligibility check for Score v3 search go_evidence (#91)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from config import PERFORMANCE_DIR

from walk_forward.ledger_loader import load_performance_index

# Issue #91 blocker language: carve IS + OOS both ≥20 H20-complete pick days.
_MIN_SIDE_PICK_DAYS = 20
_MIN_TOTAL_FOR_CARVE = _MIN_SIDE_PICK_DAYS * 2


def _h20_complete_pick_dates(
    performance_dir: Path,
    markets: list[str],
    *,
    as_of_date: str,
) -> list[str]:
    index = load_performance_index(performance_dir)
    dates: set[str] = set()
    market_set = set(markets)
    for (pick_date, _symbol, horizon_id), row in index.items():
        if horizon_id != "H20":
            continue
        if row.get("completionStatus") != "complete":
            continue
        if row.get("market") not in market_set:
            continue
        if pick_date > as_of_date:
            continue
        dates.add(pick_date)
    return sorted(dates)


def assess_search_go_evidence_readiness(
    *,
    as_of_date: str,
    markets: list[str],
    performance_dir: Path | str | None = None,
) -> dict[str, Any]:
    """Return deterministic readiness report for search go_evidence IS/OOS carve."""
    perf = Path(performance_dir) if performance_dir is not None else PERFORMANCE_DIR
    dates = _h20_complete_pick_dates(perf, markets, as_of_date=as_of_date)
    n = len(dates)
    base: dict[str, Any] = {
        "asOfDate": as_of_date,
        "markets": list(markets),
        "h20CompletePickDays": n,
        "proposedIs": None,
        "proposedOos": None,
        "projectedOosPickDays": None,
        "reasons": [],
    }
    if n < _MIN_TOTAL_FOR_CARVE:
        return {
            **base,
            "status": "not_ready",
            "reasons": [
                f"need ≥{_MIN_TOTAL_FOR_CARVE} H20-complete pick days to carve IS+OOS "
                f"both ≥{_MIN_SIDE_PICK_DAYS}; have {n}"
            ],
        }

    is_dates = dates[: n - _MIN_SIDE_PICK_DAYS]
    oos_dates = dates[n - _MIN_SIDE_PICK_DAYS :]
    return {
        **base,
        "status": "ready",
        "proposedIs": {"startDate": is_dates[0], "endDate": is_dates[-1]},
        "proposedOos": {"startDate": oos_dates[0], "endDate": oos_dates[-1]},
        "projectedOosPickDays": len(oos_dates),
        "reasons": [
            f"carve IS={len(is_dates)} OOS={len(oos_dates)} H20-complete pick days"
        ],
    }
