"""Calibration run configuration loading and validation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from config import CALIBRATION_DIR, LEDGER_DIR, PERFORMANCE_DIR, WALK_FORWARD_DIR
from walk_forward.folds import build_decision_sessions, generate_rolling_folds

from calibration.candidates import CandidateSpec, parse_candidates


@dataclass(frozen=True)
class CalibrationRunConfig:
    packageIntent: str
    mode: str
    candidates: list[CandidateSpec]
    isFoldSpec: dict[str, Any]
    oosFoldSpec: dict[str, Any]
    markets: list[str]
    promoteTopN: int
    measurementSourceIs: str
    measurementSourceOos: str
    ledgerDir: Path
    performanceDir: Path
    outputDir: Path
    walkForwardOutputDir: Path


def _validate_fold_spec(name: str, fold_spec: dict[str, Any]) -> None:
    if not fold_spec or fold_spec.get("mode") != "rolling":
        raise ValueError(f'{name}.mode must be "rolling"')
    for key in ("trainSessions", "oosSessions", "stepSessions", "startDate", "endDate"):
        if key not in fold_spec:
            raise ValueError(f"{name} missing required field {key}")


def _decision_dates(fold_spec: dict[str, Any], markets: list[str]) -> set[str]:
    sessions = build_decision_sessions(
        fold_spec["startDate"],
        fold_spec["endDate"],
        markets,
    )
    folds = generate_rolling_folds(fold_spec, sessions)
    dates: set[str] = set()
    for fold in folds:
        dates.update(fold.get("oosSessions") or [])
        dates.update(fold.get("trainSessions") or [])
    return dates


def _validate_is_oos_disjoint(
    is_spec: dict[str, Any],
    oos_spec: dict[str, Any],
    markets: list[str],
    *,
    package_intent: str,
) -> None:
    if package_intent != "go_evidence" and is_spec.get("endDate") < oos_spec.get("startDate"):
        # Still check overlap when calendars might intersect
        pass
    try:
        is_dates = _decision_dates(is_spec, markets)
        oos_dates = _decision_dates(oos_spec, markets)
    except ValueError:
        # Fold generation may fail for tiny windows in dry validation of bad fixtures;
        # fall back to range overlap on calendar endpoints.
        if not (
            is_spec["endDate"] < oos_spec["startDate"]
            or oos_spec["endDate"] < is_spec["startDate"]
        ):
            raise ValueError(
                "IS and OOS fold calendars overlap; decision dates must be disjoint"
            )
        return
    overlap = sorted(is_dates & oos_dates)
    if overlap:
        raise ValueError(
            "IS/OOS decision-date overlap forbidden for calibration: "
            + ", ".join(overlap[:8])
            + ("..." if len(overlap) > 8 else "")
        )


def _validate_payload(data: dict[str, Any]) -> None:
    package_intent = data.get("packageIntent")
    if package_intent not in ("exploratory", "go_evidence"):
        raise ValueError('packageIntent must be "exploratory" or "go_evidence"')
    mode = data.get("mode")
    if mode not in ("search", "baseline-only"):
        raise ValueError('mode must be "search" or "baseline-only"')

    if (
        package_intent == "go_evidence"
        and data.get("measurementSourceOos") != "ledger"
    ):
        raise ValueError(
            "go_evidence requires measurementSourceOos=ledger; "
            "fixture-recompute is not allowed for OOS GO packages"
        )

    markets = data.get("markets")
    if not markets or not isinstance(markets, list):
        raise ValueError("markets must be a non-empty list")

    _validate_fold_spec("oosFoldSpec", data.get("oosFoldSpec") or {})
    if mode == "search":
        _validate_fold_spec("isFoldSpec", data.get("isFoldSpec") or {})
        _validate_is_oos_disjoint(
            data["isFoldSpec"],
            data["oosFoldSpec"],
            list(markets),
            package_intent=package_intent,
        )
    else:
        # baseline-only still needs a placeholder isFoldSpec for schema symmetry optional
        if data.get("isFoldSpec"):
            _validate_fold_spec("isFoldSpec", data["isFoldSpec"])
            _validate_is_oos_disjoint(
                data["isFoldSpec"],
                data["oosFoldSpec"],
                list(markets),
                package_intent=package_intent,
            )


def load_calibration_config(path: Path | str) -> CalibrationRunConfig:
    config_path = Path(path)
    data = json.loads(config_path.read_text(encoding="utf-8"))
    _validate_payload(data)
    mode = data["mode"]
    candidates = parse_candidates(data.get("candidates"), mode=mode)
    promote = int(data.get("promoteTopN", 1))
    if promote < 1:
        raise ValueError("promoteTopN must be >= 1")

    is_spec = dict(data.get("isFoldSpec") or data["oosFoldSpec"])
    return CalibrationRunConfig(
        packageIntent=data["packageIntent"],
        mode=mode,
        candidates=candidates,
        isFoldSpec=is_spec,
        oosFoldSpec=dict(data["oosFoldSpec"]),
        markets=list(data["markets"]),
        promoteTopN=promote,
        measurementSourceIs=data.get("measurementSourceIs", "ledger"),
        measurementSourceOos=data["measurementSourceOos"]
        if "measurementSourceOos" in data
        else data.get("measurementSourceIs", "ledger"),
        ledgerDir=Path(data["ledgerDir"]) if data.get("ledgerDir") else LEDGER_DIR,
        performanceDir=Path(data["performanceDir"])
        if data.get("performanceDir")
        else PERFORMANCE_DIR,
        outputDir=Path(data["outputDir"]) if data.get("outputDir") else CALIBRATION_DIR,
        walkForwardOutputDir=Path(data["walkForwardOutputDir"])
        if data.get("walkForwardOutputDir")
        else WALK_FORWARD_DIR,
    )


def config_hash(cfg: CalibrationRunConfig) -> str:
    payload: dict[str, Any] = {
        "candidates": [
            {
                "candidateId": c.candidateId,
                "threshold": c.threshold,
                "weights": c.weights,
            }
            for c in cfg.candidates
        ],
        "isFoldSpec": cfg.isFoldSpec,
        "markets": sorted(cfg.markets),
        "measurementSourceIs": cfg.measurementSourceIs,
        "measurementSourceOos": cfg.measurementSourceOos,
        "mode": cfg.mode,
        "oosFoldSpec": cfg.oosFoldSpec,
        "packageIntent": cfg.packageIntent,
        "promoteTopN": cfg.promoteTopN,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
