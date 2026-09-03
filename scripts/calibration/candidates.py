"""Candidate / weight-vector validation for calibration (#67)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

WEIGHT_KEYS = (
    "WEIGHT_SIZE",
    "WEIGHT_VALUATION",
    "WEIGHT_GROWTH",
    "WEIGHT_QUALITY",
    "WEIGHT_ENTRY",
    "WEIGHT_MOMENTUM",
)

WEIGHT_SUM_TOLERANCE = 1e-6
MAX_CANDIDATES = 10


@dataclass(frozen=True)
class CandidateSpec:
    candidateId: str
    threshold: float | None
    weights: dict[str, float] | None
    notes: str | None = None


def validate_weights(weights: dict[str, Any]) -> dict[str, float]:
    """Validate top-level COMPOSITE weights; return normalized float dict."""
    if not isinstance(weights, dict):
        raise ValueError("weights must be an object")
    unknown = set(weights) - set(WEIGHT_KEYS)
    if unknown:
        raise ValueError(f"unknown or nested weight keys forbidden: {sorted(unknown)}")
    missing = [k for k in WEIGHT_KEYS if k not in weights]
    if missing:
        raise ValueError(f"missing weight keys: {missing}")
    out: dict[str, float] = {}
    for key in WEIGHT_KEYS:
        val = weights[key]
        if not isinstance(val, int | float) or isinstance(val, bool):
            raise ValueError(f"{key} must be a finite number")
        fval = float(val)
        if fval != fval:  # NaN
            raise ValueError(f"{key} must be finite")
        out[key] = fval
    total = sum(out.values())
    if abs(total - 1.0) > WEIGHT_SUM_TOLERANCE:
        raise ValueError(f"weight sum must be 1.0±{WEIGHT_SUM_TOLERANCE}; got {total}")
    return out


def parse_candidate(raw: dict[str, Any]) -> CandidateSpec:
    if not raw.get("candidateId"):
        raise ValueError("candidateId is required")
    threshold = raw.get("threshold")
    if threshold is not None and (
        not isinstance(threshold, int | float) or isinstance(threshold, bool)
    ):
        raise ValueError(f"threshold must be a number or null for {raw.get('candidateId')}")
    weights_raw = raw.get("weights")
    weights = validate_weights(weights_raw) if weights_raw is not None else None
    return CandidateSpec(
        candidateId=str(raw["candidateId"]),
        threshold=float(threshold) if threshold is not None else None,
        weights=weights,
        notes=raw.get("notes"),
    )


def parse_candidates(raw_list: list[Any] | None, *, mode: str) -> list[CandidateSpec]:
    if mode == "baseline-only":
        if raw_list:
            raise ValueError("baseline-only mode must not include a search candidate grid")
        return []
    if not raw_list:
        raise ValueError("search mode requires at least one candidate")
    if len(raw_list) > MAX_CANDIDATES:
        raise ValueError(f"at most {MAX_CANDIDATES} candidates allowed; got {len(raw_list)}")
    candidates = [parse_candidate(item) for item in raw_list]
    ids = [c.candidateId for c in candidates]
    if len(ids) != len(set(ids)):
        raise ValueError("candidateId values must be unique within a run")
    return candidates
