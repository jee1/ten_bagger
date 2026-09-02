"""Walk-forward OOS report builder and canonical serialization."""

from __future__ import annotations

import json
from typing import Any

from walk_forward.aggregate import aggregate_report, enrich_fold_results
from walk_forward.config import RunConfig, config_hash

SCHEMA_VERSION = "0.1.0"


def _report_fold(fold: dict[str, Any]) -> dict[str, Any]:
    return {
        "foldIndex": fold["foldIndex"],
        "trainRange": dict(fold["trainRange"]),
        "oosRange": dict(fold["oosRange"]),
        "status": fold.get("status", "complete"),
        "pickDays": fold.get("pickDays", 0),
        "noPickDays": fold.get("noPickDays", 0),
        "horizons": list(fold.get("horizons") or []),
    }


def build_report(
    *,
    run_config: RunConfig,
    fold_results: list[dict[str, Any]],
    run_id: str,
    generated_at: str,
) -> dict[str, Any]:
    """Assemble a schema-compliant walk-forward report dict."""
    enriched = enrich_fold_results(fold_results)
    report_folds = [_report_fold(f) for f in enriched]
    aggregate_horizons, coverage = aggregate_report(enriched, run_config.runIntent)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "runId": run_id,
        "runIntent": run_config.runIntent,
        "measurementSource": run_config.measurementSource,
        "configHash": config_hash(run_config),
        "generatedAt": generated_at,
        "candidateId": run_config.candidateId,
        "foldSpec": dict(run_config.foldSpec),
        "folds": report_folds,
        "aggregate": {"horizons": aggregate_horizons},
        "coverage": coverage,
    }


def serialize_report(report: dict[str, Any]) -> bytes:
    """Deterministic UTF-8 JSON bytes for report persistence."""
    return json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )
