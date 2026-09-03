"""Calibration report serialization tests."""

from __future__ import annotations

from calibration.config import load_calibration_config
from calibration.report import build_report, serialize_report
from pathlib import Path

FIX = Path(__file__).resolve().parent / "fixtures" / "calibration"


def test_serialize_report_deterministic():
    cfg = load_calibration_config(FIX / "smoke-baseline-only-config.json")
    report = build_report(
        cal_config=cfg,
        run_id="abcd1234abcd1234",
        generated_at="2026-04-30T23:59:59Z",
        is_ranking=[],
        selection_rationale="baseline-only",
        oos_evaluations=[],
        overall="N/A",
        failed_bullets=[],
    )
    a = serialize_report(report)
    b = serialize_report(report)
    assert a == b
    assert b"packageIntent" in a
