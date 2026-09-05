"""Tests for Top-N helpers and semantic validation (Issue #72)."""

from __future__ import annotations

from config import COMPOSITE_THRESHOLD, SCORE_VERSION, TOP_N, UniverseSymbol
from scoring.models import ScoreResult
from top_n import build_top_candidates, rank_key, select_pick
from top_n_validate import validate_top_candidates


def _result(symbol: str, composite: float, *, name_en: str = "Co") -> ScoreResult:
    meta = UniverseSymbol(symbol, "이름", name_en, "NASDAQ", "USD")
    return ScoreResult(
        symbol=symbol,
        meta=meta,
        size=80.0,
        growth=75.0,
        valuation=78.0,
        entry=70.0,
        momentum=65.0,
        quality=72.0,
        composite=composite,
        metrics={},
        score_version=SCORE_VERSION,
    )


def test_select_pick_returns_first_above_threshold():
    ranked = [
        _result("LOW", COMPOSITE_THRESHOLD - 1),
        _result("HIT", COMPOSITE_THRESHOLD + 5),
        _result("HIGHER", COMPOSITE_THRESHOLD + 10),
    ]
    # list already sorted high→low in real pipeline; test filter order as given
    ranked.sort(key=rank_key)
    pick = select_pick(ranked)
    assert pick is not None
    assert pick.symbol == "HIGHER"


def test_select_pick_none_when_all_below():
    ranked = [_result("A", 10.0), _result("B", 20.0)]
    ranked.sort(key=rank_key)
    assert select_pick(ranked) is None


def test_rank_key_tie_breaks_on_symbol():
    a = _result("AAA", 80.0)
    b = _result("BBB", 80.0)
    rows = [b, a]
    rows.sort(key=rank_key)
    assert [r.symbol for r in rows] == ["AAA", "BBB"]


def test_build_top_candidates_limits_and_omit_empty():
    assert build_top_candidates([]) is None
    rows = [_result(f"S{i}", 90.0 - i) for i in range(7)]
    rows.sort(key=rank_key)
    top = build_top_candidates(rows)
    assert top is not None
    assert len(top) == TOP_N
    assert top[0]["rank"] == 1
    assert top[0]["symbol"] == "S0"
    assert "composite" in top[0]["scores"]


def test_validate_accepts_omit_and_valid_pick():
    assert validate_top_candidates({"status": "no_pick"}) == []
    entry = {
        "status": "pick",
        "stock": {"symbol": "AAA"},
        "topCandidates": [
            {
                "rank": 1,
                "symbol": "AAA",
                "name": {"ko": "가", "en": "A"},
                "exchange": "NASDAQ",
                "currency": "USD",
                "scores": {
                    "composite": 80,
                    "size": 1,
                    "growth": 1,
                    "valuation": 1,
                    "entry": 1,
                    "momentum": 1,
                    "quality": 1,
                },
            }
        ],
    }
    assert validate_top_candidates(entry) == []


def test_validate_rejects_duplicate_and_pick_mismatch():
    bad_dup = {
        "status": "no_pick",
        "topCandidates": [
            {
                "rank": 1,
                "symbol": "AAA",
                "name": {"ko": "가", "en": "A"},
                "exchange": "NASDAQ",
                "currency": "USD",
                "scores": {
                    "composite": 80,
                    "size": 1,
                    "growth": 1,
                    "valuation": 1,
                    "entry": 1,
                    "momentum": 1,
                    "quality": 1,
                },
            },
            {
                "rank": 2,
                "symbol": "AAA",
                "name": {"ko": "가", "en": "A"},
                "exchange": "NASDAQ",
                "currency": "USD",
                "scores": {
                    "composite": 70,
                    "size": 1,
                    "growth": 1,
                    "valuation": 1,
                    "entry": 1,
                    "momentum": 1,
                    "quality": 1,
                },
            },
        ],
    }
    errs = validate_top_candidates(bad_dup)
    assert any("duplicate" in e for e in errs)

    bad_pick = {
        "status": "pick",
        "stock": {"symbol": "PICK"},
        "topCandidates": [
            {
                "rank": 1,
                "symbol": "OTHER",
                "name": {"ko": "가", "en": "A"},
                "exchange": "NASDAQ",
                "currency": "USD",
                "scores": {
                    "composite": 80,
                    "size": 1,
                    "growth": 1,
                    "valuation": 1,
                    "entry": 1,
                    "momentum": 1,
                    "quality": 1,
                },
            }
        ],
    }
    errs2 = validate_top_candidates(bad_pick)
    assert any("must equal topCandidates rank1" in e for e in errs2)


def test_validate_rejects_empty_array():
    errs = validate_top_candidates({"status": "no_pick", "topCandidates": []})
    assert any("omitted" in e for e in errs)
