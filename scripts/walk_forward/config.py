"""Walk-forward run configuration loading and validation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from config import LEDGER_DIR, PERFORMANCE_DIR, WALK_FORWARD_DIR

MAX_CANDIDATES = 4


@dataclass(frozen=True)
class RunConfig:
    runIntent: str
    measurementSource: str
    candidateId: str
    markets: list[str]
    foldSpec: dict[str, Any]
    weightOverrides: dict[str, Any] | None = None
    ledgerDir: Path | None = None
    performanceDir: Path | None = None
    outputDir: Path | None = None


def _validate_run_config(data: dict[str, Any]) -> None:
    if (
        data.get("runIntent") == "go_evidence"
        and data.get("measurementSource") == "fixture-recompute"
    ):
        raise ValueError(
            "go_evidence requires measurementSource=ledger; fixture-recompute is not allowed"
        )

    candidate_ids = data.get("candidateIds")
    if candidate_ids is not None and len(candidate_ids) > MAX_CANDIDATES:
        raise ValueError(f"at most {MAX_CANDIDATES} candidates allowed; got {len(candidate_ids)}")

    fold_spec = data.get("foldSpec") or {}
    if fold_spec.get("mode") != "rolling":
        raise ValueError('foldSpec.mode must be "rolling"')

    if not data.get("candidateId"):
        raise ValueError("candidateId is required")

    overrides = data.get("weightOverrides")
    if overrides not in (None, {}):
        raise ValueError(
            "weightOverrides are not supported in v1; use candidateId score-v2-baseline only"
        )


def load_run_config(path: Path | str) -> RunConfig:
    """Load and validate run-config.json."""
    config_path = Path(path)
    data = json.loads(config_path.read_text(encoding="utf-8"))
    _validate_run_config(data)

    return RunConfig(
        runIntent=data["runIntent"],
        measurementSource=data["measurementSource"],
        candidateId=data["candidateId"],
        markets=list(data["markets"]),
        foldSpec=dict(data["foldSpec"]),
        weightOverrides=data.get("weightOverrides"),
        ledgerDir=Path(data["ledgerDir"]) if data.get("ledgerDir") else LEDGER_DIR,
        performanceDir=(
            Path(data["performanceDir"]) if data.get("performanceDir") else PERFORMANCE_DIR
        ),
        outputDir=Path(data["outputDir"]) if data.get("outputDir") else WALK_FORWARD_DIR,
    )


def config_hash(cfg: RunConfig) -> str:
    """SHA-256 of canonical run config JSON (no secrets or extra file keys)."""
    payload: dict[str, Any] = {
        "candidateId": cfg.candidateId,
        "foldSpec": cfg.foldSpec,
        "markets": sorted(cfg.markets),
        "measurementSource": cfg.measurementSource,
        "runIntent": cfg.runIntent,
        "weightOverrides": cfg.weightOverrides,
    }
    if cfg.ledgerDir is not None:
        payload["ledgerDir"] = str(cfg.ledgerDir)
    if cfg.performanceDir is not None:
        payload["performanceDir"] = str(cfg.performanceDir)
    if cfg.outputDir is not None:
        payload["outputDir"] = str(cfg.outputDir)

    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
