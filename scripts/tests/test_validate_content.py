"""Tests for schema-backed validation."""

from __future__ import annotations

from validate_content import load_validator


def test_schema_validator_loads():
    validator = load_validator()
    sample = {
        "date": "2026-07-01",
        "market": "KR",
        "status": "no_pick",
        "scores": {
            "composite": 0,
            "growth": 0,
            "valuation": 0,
            "momentum": 0,
            "quality": 0,
            "threshold": 70,
        },
        "meta": {
            "generatedAt": "2026-07-01T00:00:00+09:00",
            "candidatesScreened": 1,
            "excludedRecent": 0,
        },
    }
    errors = list(validator.iter_errors(sample))
    assert errors == []
