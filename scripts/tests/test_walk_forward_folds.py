"""Rolling fold calendar tests."""

from __future__ import annotations

import pytest
from walk_forward.folds import build_decision_sessions, generate_rolling_folds

VALID_FOLD_SPEC = {
    "mode": "rolling",
    "trainSessions": 4,
    "oosSessions": 2,
    "stepSessions": 2,
    "startDate": "2025-01-01",
    "endDate": "2025-01-31",
}


def test_build_decision_sessions_weekday_and_market_filter():
    # 2025-01-01 Wed KR (odd day), 2025-01-02 Thu US (even day)
    kr_only = build_decision_sessions("2025-01-01", "2025-01-10", ["KR"])
    assert "2025-01-01" in kr_only  # Wed, odd -> KR
    assert "2025-01-02" not in kr_only  # US day
    assert "2025-01-04" not in kr_only  # Sat
    assert kr_only == sorted(kr_only)


def test_generate_rolling_folds_returns_at_least_two():
    sessions = build_decision_sessions(
        VALID_FOLD_SPEC["startDate"],
        VALID_FOLD_SPEC["endDate"],
        ["KR", "US"],
    )
    folds = generate_rolling_folds(VALID_FOLD_SPEC, sessions)
    assert len(folds) >= 2
    assert folds[0]["foldIndex"] == 0
    assert folds[1]["foldIndex"] == 1


def test_generate_rolling_folds_train_oos_disjoint():
    sessions = build_decision_sessions(
        VALID_FOLD_SPEC["startDate"],
        VALID_FOLD_SPEC["endDate"],
        ["KR", "US"],
    )
    folds = generate_rolling_folds(VALID_FOLD_SPEC, sessions)
    for fold in folds:
        train = set(fold["trainSessions"])
        oos = set(fold["oosSessions"])
        assert train.isdisjoint(oos)
        assert fold["trainRange"]["start"] == fold["trainSessions"][0]
        assert fold["trainRange"]["end"] == fold["trainSessions"][-1]
        assert fold["oosRange"]["start"] == fold["oosSessions"][0]
        assert fold["oosRange"]["end"] == fold["oosSessions"][-1]


def test_generate_rolling_folds_step_advances_calendar():
    sessions = build_decision_sessions(
        VALID_FOLD_SPEC["startDate"],
        VALID_FOLD_SPEC["endDate"],
        ["KR", "US"],
    )
    folds = generate_rolling_folds(VALID_FOLD_SPEC, sessions)
    assert folds[0]["trainSessions"][0] != folds[1]["trainSessions"][0]
    assert folds[1]["trainSessions"][0] == folds[0]["trainSessions"][VALID_FOLD_SPEC["stepSessions"]]


def test_generate_rolling_folds_fails_when_less_than_two():
    short_spec = {
        **VALID_FOLD_SPEC,
        "endDate": "2025-01-05",
    }
    sessions = build_decision_sessions(
        short_spec["startDate"],
        short_spec["endDate"],
        ["KR", "US"],
    )
    with pytest.raises(ValueError, match="at least 2"):
        generate_rolling_folds(short_spec, sessions)
