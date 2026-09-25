"""Eligibility check for Score v3 search go_evidence (#91)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from config import PERFORMANCE_DIR
from walk_forward.folds import (
    build_decision_sessions,
    project_go_evidence_oos_sessions,
)
from walk_forward.ledger_loader import load_performance_index

# Issue #91 blocker language: carve IS + OOS both ≥20 H20-complete pick days.
_MIN_SIDE_PICK_DAYS = 20
_MIN_TOTAL_FOR_CARVE = _MIN_SIDE_PICK_DAYS * 2


def _is_decision_session(day: str, markets: list[str]) -> bool:
    sessions = build_decision_sessions(day, day, markets)
    return bool(sessions) and day in sessions


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


def _aligned_pick_dates(pick_dates: list[str], markets: list[str]) -> list[str]:
    return [day for day in pick_dates if _is_decision_session(day, markets)]


def _default_oos_fold_spec(oos_start: str, oos_end: str) -> dict[str, Any]:
    return {
        "mode": "rolling",
        "trainSessions": 6,
        "oosSessions": 2,
        "stepSessions": 2,
        "startDate": oos_start,
        "endDate": oos_end,
    }


def assess_search_go_evidence_readiness(
    *,
    as_of_date: str,
    markets: list[str],
    performance_dir: Path | str | None = None,
    oos_fold_spec: dict[str, Any] | None = None,
    is_fold_spec: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return deterministic readiness report for search go_evidence IS/OOS carve."""
    perf = Path(performance_dir) if performance_dir is not None else PERFORMANCE_DIR
    ledger_dates = _h20_complete_pick_dates(perf, markets, as_of_date=as_of_date)
    aligned_dates = _aligned_pick_dates(ledger_dates, markets)
    n_aligned = len(aligned_dates)
    base: dict[str, Any] = {
        "asOfDate": as_of_date,
        "markets": list(markets),
        "h20CompletePickDays": len(ledger_dates),
        "h20CompleteAlignedPickDays": n_aligned,
        "proposedIs": None,
        "proposedOos": None,
        "projectedOosPickDays": None,
        "reasons": [],
    }
    if n_aligned < _MIN_TOTAL_FOR_CARVE:
        weekend_only = len(ledger_dates) - n_aligned
        return {
            **base,
            "status": "not_ready",
            "reasons": [
                f"need ≥{_MIN_TOTAL_FOR_CARVE} H20-complete pick days on walk-forward "
                f"decision sessions to carve IS+OOS both ≥{_MIN_SIDE_PICK_DAYS}; "
                f"have {n_aligned} aligned ({len(ledger_dates)} ledger rows, "
                f"{weekend_only} off-session)"
            ],
        }

    is_dates = aligned_dates[: n_aligned - _MIN_SIDE_PICK_DAYS]
    oos_dates = aligned_dates[n_aligned - _MIN_SIDE_PICK_DAYS :]
    oos_spec = (
        {**oos_fold_spec, "startDate": oos_dates[0], "endDate": oos_dates[-1]}
        if oos_fold_spec
        else _default_oos_fold_spec(oos_dates[0], oos_dates[-1])
    )
    is_spec = (
        {**is_fold_spec, "startDate": is_dates[0], "endDate": is_dates[-1]}
        if is_fold_spec
        else {
            "mode": "rolling",
            "trainSessions": oos_spec["trainSessions"],
            "oosSessions": oos_spec["oosSessions"],
            "stepSessions": oos_spec["stepSessions"],
            "startDate": is_dates[0],
            "endDate": is_dates[-1],
        }
    )
    projected = project_go_evidence_oos_sessions(is_spec, oos_spec, markets)
    oos_sessions_in_range = len(build_decision_sessions(oos_dates[0], oos_dates[-1], markets))
    base.update(
        {
            "proposedIs": {"startDate": is_dates[0], "endDate": is_dates[-1]},
            "proposedOos": {"startDate": oos_dates[0], "endDate": oos_dates[-1]},
            "projectedOosPickDays": projected,
        }
    )
    if projected < _MIN_SIDE_PICK_DAYS:
        return {
            **base,
            "status": "not_ready",
            "reasons": [
                f"walk-forward oosFoldSpec projects {projected} independent OOS "
                f"decision sessions (<{_MIN_SIDE_PICK_DAYS}); OOS carve has "
                f"{len(oos_dates)} aligned ledger pick days across "
                f"{oos_sessions_in_range} decision sessions"
            ],
        }

    return {
        **base,
        "status": "ready",
        "reasons": [
            f"carve IS={len(is_dates)} OOS={len(oos_dates)} aligned H20-complete pick days; "
            f"walk-forward projects {projected} independent OOS sessions"
        ],
    }
