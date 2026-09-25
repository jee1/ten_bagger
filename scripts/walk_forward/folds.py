"""Rolling walk-forward fold calendar generation."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from config import market_for_date


def build_decision_sessions(start_date: str, end_date: str, markets: list[str]) -> list[str]:
    """Return weekday decision sessions whose market is in *markets*."""
    market_set = set(markets)
    current = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    sessions: list[str] = []

    while current <= end:
        if current.weekday() < 5:
            day_str = current.isoformat()
            if market_for_date(day_str) in market_set:
                sessions.append(day_str)
        current += timedelta(days=1)

    return sessions


def generate_rolling_folds(fold_spec: dict[str, Any], sessions: list[str]) -> list[dict[str, Any]]:
    """Build rolling train/OOS folds from a decision-session calendar."""
    train_n = int(fold_spec["trainSessions"])
    oos_n = int(fold_spec["oosSessions"])
    step = int(fold_spec["stepSessions"])
    window = train_n + oos_n

    folds: list[dict[str, Any]] = []
    offset = 0
    fold_index = 0

    while offset + window <= len(sessions):
        train_sessions = sessions[offset : offset + train_n]
        oos_sessions = sessions[offset + train_n : offset + window]

        train_set = set(train_sessions)
        oos_set = set(oos_sessions)
        if train_set & oos_set:
            raise ValueError("train and OOS session sets must be disjoint")

        folds.append(
            {
                "foldIndex": fold_index,
                "trainRange": {"start": train_sessions[0], "end": train_sessions[-1]},
                "oosRange": {"start": oos_sessions[0], "end": oos_sessions[-1]},
                "trainSessions": train_sessions,
                "oosSessions": oos_sessions,
            }
        )
        offset += step
        fold_index += 1

    if len(folds) < 2:
        raise ValueError(
            f"foldSpec produced {len(folds)} fold(s); need at least 2. "
            "Adjust trainSessions, oosSessions, stepSessions, startDate, endDate"
        )

    return folds


def project_unique_oos_sessions(fold_spec: dict[str, Any], markets: list[str]) -> int:
    """Count disjoint OOS decision sessions a rolling foldSpec can evaluate."""
    sessions = build_decision_sessions(
        fold_spec["startDate"],
        fold_spec["endDate"],
        markets,
    )
    try:
        folds = generate_rolling_folds(fold_spec, sessions)
    except ValueError:
        return 0
    unique: set[str] = set()
    for fold in folds:
        unique.update(fold["oosSessions"])
    return len(unique)


def _dedupe_preserve_order(sessions: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for session in sessions:
        if session in seen:
            continue
        seen.add(session)
        ordered.append(session)
    return ordered


def generate_go_evidence_oos_folds(
    is_fold_spec: dict[str, Any],
    oos_fold_spec: dict[str, Any],
    markets: list[str],
) -> list[dict[str, Any]]:
    """Rolling OOS folds with train context from IS (and prior OOS for duplicate-ban only).

    go_evidence OOS evaluation must not spend OOS calendar sessions on in-window
    train blocks; IS history seeds duplicate-ban state before each OOS segment.
    """
    is_sessions = build_decision_sessions(
        is_fold_spec["startDate"],
        is_fold_spec["endDate"],
        markets,
    )
    oos_sessions = build_decision_sessions(
        oos_fold_spec["startDate"],
        oos_fold_spec["endDate"],
        markets,
    )
    train_tail = int(oos_fold_spec["trainSessions"])
    oos_n = int(oos_fold_spec["oosSessions"])
    step = int(oos_fold_spec["stepSessions"])

    if train_tail > len(is_sessions):
        raise ValueError(
            f"trainSessions={train_tail} exceeds IS decision sessions ({len(is_sessions)})"
        )

    folds: list[dict[str, Any]] = []
    offset = 0
    fold_index = 0

    while offset + oos_n <= len(oos_sessions):
        is_tail = is_sessions[-train_tail:] if train_tail else []
        prior_oos = oos_sessions[:offset]
        train_sessions = _dedupe_preserve_order(is_tail + prior_oos)
        oos_block = oos_sessions[offset : offset + oos_n]

        train_set = set(train_sessions)
        oos_set = set(oos_block)
        if train_set & oos_set:
            raise ValueError("train and OOS session sets must be disjoint")

        folds.append(
            {
                "foldIndex": fold_index,
                "trainRange": {"start": train_sessions[0], "end": train_sessions[-1]}
                if train_sessions
                else {"start": oos_block[0], "end": oos_block[0]},
                "oosRange": {"start": oos_block[0], "end": oos_block[-1]},
                "trainSessions": train_sessions,
                "oosSessions": oos_block,
            }
        )
        offset += step
        fold_index += 1

    if len(folds) < 2:
        raise ValueError(
            f"go_evidence OOS foldSpec produced {len(folds)} fold(s); need at least 2. "
            "Adjust trainSessions, oosSessions, stepSessions, or widen the OOS calendar"
        )

    return folds


def project_go_evidence_oos_sessions(
    is_fold_spec: dict[str, Any],
    oos_fold_spec: dict[str, Any],
    markets: list[str],
) -> int:
    """Count disjoint OOS sessions for go_evidence IS-seeded rolling folds."""
    try:
        folds = generate_go_evidence_oos_folds(is_fold_spec, oos_fold_spec, markets)
    except ValueError:
        return 0
    unique: set[str] = set()
    for fold in folds:
        unique.update(fold["oosSessions"])
    return len(unique)
