"""Calibration report builder and canonical serialization."""

from __future__ import annotations

import json
from typing import Any

from calibration.candidates import WEIGHT_KEYS
from calibration.config import CalibrationRunConfig, config_hash

SCHEMA_VERSION = "0.1.0"
MERGE_CRITERIA_REF = "docs/architecture/threshold-weight-merge-criteria.md"


def live_constants_snapshot() -> dict[str, Any]:
    import config as live_config

    weights = {key: float(getattr(live_config, key)) for key in WEIGHT_KEYS}
    return {
        "compositeThreshold": float(live_config.COMPOSITE_THRESHOLD),
        "weights": weights,
    }


def build_report(
    *,
    cal_config: CalibrationRunConfig,
    run_id: str,
    generated_at: str,
    is_ranking: list[dict[str, Any]],
    selection_rationale: str,
    oos_evaluations: list[dict[str, Any]],
    overall: str,
    failed_bullets: list[str],
    merge_criteria_ref: str = MERGE_CRITERIA_REF,
) -> dict[str, Any]:
    """Assemble a schema-compliant calibration report dict."""
    return {
        "schemaVersion": SCHEMA_VERSION,
        "runId": run_id,
        "packageIntent": cal_config.packageIntent,
        "mode": cal_config.mode,
        "configHash": config_hash(cal_config),
        "generatedAt": generated_at,
        "liveConstantsSnapshot": live_constants_snapshot(),
        "isRanking": list(is_ranking),
        "selectionRationale": selection_rationale,
        "oosEvaluations": list(oos_evaluations),
        "overallVerdict": overall,
        "failedBullets": list(failed_bullets),
        "mergeCriteriaRef": merge_criteria_ref,
    }


def serialize_report(report: dict[str, Any]) -> bytes:
    """Deterministic UTF-8 JSON bytes for report persistence."""
    return json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )
