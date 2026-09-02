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
