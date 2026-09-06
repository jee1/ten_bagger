"""Tests for ledger pick source and H20-primary fold completeness."""

from __future__ import annotations

import json
from pathlib import Path

from walk_forward.config import RunConfig
from walk_forward.ledger_picks import ledger_pick_day
from walk_forward.runner import run_folds


def test_ledger_pick_day_reads_published_daily(tmp_path: Path):
    daily = tmp_path / "2026-07-03.json"
    daily.write_text(
        json.dumps(
            {
                "date": "2026-07-03",
                "market": "KR",
                "status": "pick",
                "stock": {"symbol": "005930.KS"},
            }
        ),
        encoding="utf-8",
    )
    symbol, no_pick = ledger_pick_day("KR", "2026-07-03", {"OTHER"}, daily_dir=tmp_path)
    assert no_pick is False
    assert symbol == "005930.KS"


def test_fold_complete_when_only_h60_incomplete():
    """ADR 0003: H60 incomplete must not force fold incomplete_horizon."""
    cfg = RunConfig(
        runIntent="go_evidence",
        measurementSource="ledger",
        candidateId="score-v2-baseline",
        markets=["KR"],
        foldSpec={
            "mode": "rolling",
            "trainSessions": 1,
            "oosSessions": 1,
            "stepSessions": 1,
            "startDate": "2026-07-03",
            "endDate": "2026-07-03",
        },
    )
    folds = [
        {
            "foldIndex": 0,
            "trainRange": {"start": "2026-07-01", "end": "2026-07-01"},
            "oosRange": {"start": "2026-07-03", "end": "2026-07-03"},
            "trainSessions": ["2026-07-01"],
            "oosSessions": ["2026-07-03"],
        }
    ]

    def pit(market: str, as_of: str, _ex: set[str]):
        if as_of == "2026-07-01":
            return "TRAIN.KS", False
        return "005930.KS", False

    def measure(picks, _cfg, _as_of):
        out = []
        for p in picks:
            out.append(
                {
                    "market": p["market"],
                    "pickDate": p["pickDate"],
                    "symbol": p["symbol"],
                    "horizonId": "H20",
                    "completionStatus": "complete",
                    "benchmarkCompletionStatus": "complete",
                    "forwardReturn": 0.1,
                    "benchmarkReturn": 0.0,
                }
            )
            out.append(
                {
                    "market": p["market"],
                    "pickDate": p["pickDate"],
                    "symbol": p["symbol"],
                    "horizonId": "H60",
                    "completionStatus": "incomplete",
                    "benchmarkCompletionStatus": "incomplete",
                    "forwardReturn": None,
                    "benchmarkReturn": None,
                }
            )
        return out

    results = run_folds(cfg, folds, measure, pit_fn=pit, as_of_date="2026-07-03")
    assert results[0]["status"] == "complete"
