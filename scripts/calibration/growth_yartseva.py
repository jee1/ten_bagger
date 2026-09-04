"""Issue #69 growth-weight reallocation (Yartseva) — analysis-only grid validators.

Default grid shrinks WEIGHT_GROWTH below the live Score v2 baseline and
redistributes freed mass to Valuation / Quality / Size only. Entry and
Momentum stay frozen at live weights. Live SCORE_VERSION / WEIGHT_* are not
modified here; GO promotion is an explicit follow-up PR.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from calibration.candidates import WEIGHT_SUM_TOLERANCE, validate_weights

# Live Score v2 COMPOSITE weights (must match scripts/config.py; freeze-tested).
LIVE_WEIGHT_SIZE = 0.15
LIVE_WEIGHT_VALUATION = 0.25
LIVE_WEIGHT_GROWTH = 0.20
LIVE_WEIGHT_QUALITY = 0.20
LIVE_WEIGHT_ENTRY = 0.10
LIVE_WEIGHT_MOMENTUM = 0.10

MIN_WEIGHT_GROWTH = 0.05

LIVE_WEIGHTS: dict[str, float] = {
    "WEIGHT_SIZE": LIVE_WEIGHT_SIZE,
    "WEIGHT_VALUATION": LIVE_WEIGHT_VALUATION,
    "WEIGHT_GROWTH": LIVE_WEIGHT_GROWTH,
    "WEIGHT_QUALITY": LIVE_WEIGHT_QUALITY,
    "WEIGHT_ENTRY": LIVE_WEIGHT_ENTRY,
    "WEIGHT_MOMENTUM": LIVE_WEIGHT_MOMENTUM,
}

_REALLOC_TARGETS = ("WEIGHT_SIZE", "WEIGHT_VALUATION", "WEIGHT_QUALITY")
_FROZEN = ("WEIGHT_ENTRY", "WEIGHT_MOMENTUM")

ISSUE69_CANDIDATE_IDS = (
    "growth_shrink_05_vq",
    "growth_shrink_10_vq",
    "growth_shrink_10_vqs",
    "growth_shrink_15_vq",
)

# Exact Issue #69 default search grid (committed growth-yartseva-issue69.json).
DEFAULT_CANDIDATES: list[dict[str, Any]] = [
    {
        "candidateId": "growth_shrink_05_vq",
        "threshold": None,
        "notes": "GROWTH 0.15 (-0.05); +0.025 Valuation, +0.025 Quality",
        "weights": {
            "WEIGHT_SIZE": 0.15,
            "WEIGHT_VALUATION": 0.275,
            "WEIGHT_GROWTH": 0.15,
            "WEIGHT_QUALITY": 0.225,
            "WEIGHT_ENTRY": 0.1,
            "WEIGHT_MOMENTUM": 0.1,
        },
    },
    {
        "candidateId": "growth_shrink_10_vq",
        "threshold": None,
        "notes": "GROWTH 0.10 (-0.10); +0.05 Valuation, +0.05 Quality",
        "weights": {
            "WEIGHT_SIZE": 0.15,
            "WEIGHT_VALUATION": 0.3,
            "WEIGHT_GROWTH": 0.1,
            "WEIGHT_QUALITY": 0.25,
            "WEIGHT_ENTRY": 0.1,
            "WEIGHT_MOMENTUM": 0.1,
        },
    },
    {
        "candidateId": "growth_shrink_10_vqs",
        "threshold": None,
        "notes": "GROWTH 0.10 (-0.10); +0.04 V, +0.04 Q, +0.02 Size",
        "weights": {
            "WEIGHT_SIZE": 0.17,
            "WEIGHT_VALUATION": 0.29,
            "WEIGHT_GROWTH": 0.1,
            "WEIGHT_QUALITY": 0.24,
            "WEIGHT_ENTRY": 0.1,
            "WEIGHT_MOMENTUM": 0.1,
        },
    },
    {
        "candidateId": "growth_shrink_15_vq",
        "threshold": None,
        "notes": "GROWTH 0.05 (-0.15); +0.075 Valuation, +0.075 Quality",
        "weights": {
            "WEIGHT_SIZE": 0.15,
            "WEIGHT_VALUATION": 0.325,
            "WEIGHT_GROWTH": 0.05,
            "WEIGHT_QUALITY": 0.275,
            "WEIGHT_ENTRY": 0.1,
            "WEIGHT_MOMENTUM": 0.1,
        },
    },
]


def validate_growth_reallocation_candidate(weights: dict[str, Any]) -> dict[str, float]:
    """Validate an Issue #69 growth-reallocation weight vector; return floats."""
    out = validate_weights(weights)
    growth = out["WEIGHT_GROWTH"]
    if growth >= LIVE_WEIGHT_GROWTH:
        raise ValueError(
            f"WEIGHT_GROWTH must be < live {LIVE_WEIGHT_GROWTH} for growth "
            f"reallocation; got {growth}"
        )
    if growth < MIN_WEIGHT_GROWTH:
        raise ValueError(
            f"WEIGHT_GROWTH must be >= {MIN_WEIGHT_GROWTH} floor; got {growth}"
        )
    for key in _FROZEN:
        if abs(out[key] - LIVE_WEIGHTS[key]) > WEIGHT_SUM_TOLERANCE:
            raise ValueError(
                f"{key} must remain at live {LIVE_WEIGHTS[key]} "
                f"(no Entry/Momentum redistribution); got {out[key]}"
            )
    for key in _REALLOC_TARGETS:
        if out[key] + WEIGHT_SUM_TOLERANCE < LIVE_WEIGHTS[key]:
            raise ValueError(
                f"{key} must not fall below live {LIVE_WEIGHTS[key]}; "
                "freed Growth mass may only increase Valuation/Quality/Size"
            )
    return out


def _candidate_id(item: Any) -> str:
    if isinstance(item, dict):
        return str(item.get("candidateId") or "")
    return str(getattr(item, "candidateId", "") or "")


def _candidate_weights(item: Any) -> dict[str, Any]:
    if isinstance(item, dict):
        weights = item.get("weights")
    else:
        weights = getattr(item, "weights", None)
    if not isinstance(weights, dict):
        raise ValueError(f"candidate {_candidate_id(item)!r} missing weights object")
    return weights


def assert_issue69_grid(candidates: list[Any]) -> list[dict[str, float]]:
    """Assert candidates are the four Issue #69 IDs with valid weight vectors."""
    if not isinstance(candidates, list):
        raise ValueError("candidates must be a list")
    if len(candidates) != len(ISSUE69_CANDIDATE_IDS):
        raise ValueError(
            f"Issue #69 grid requires exactly {len(ISSUE69_CANDIDATE_IDS)} "
            f"candidates; got {len(candidates)}"
        )
    ids = [_candidate_id(c) for c in candidates]
    if ids != list(ISSUE69_CANDIDATE_IDS):
        raise ValueError(
            f"Issue #69 candidate IDs must be {list(ISSUE69_CANDIDATE_IDS)}; got {ids}"
        )
    validated: list[dict[str, float]] = []
    for item, expected in zip(candidates, DEFAULT_CANDIDATES, strict=True):
        got = validate_growth_reallocation_candidate(_candidate_weights(item))
        exp = validate_weights(expected["weights"])
        for key, exp_val in exp.items():
            if abs(got[key] - exp_val) > WEIGHT_SUM_TOLERANCE:
                raise ValueError(
                    f"{expected['candidateId']} {key} must be {exp_val}; got {got[key]}"
                )
        validated.append(got)
    return validated


def load_issue69_config(path: Path | str) -> dict[str, Any]:
    """Load a calibration JSON and assert its candidates match the Issue #69 grid."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    assert_issue69_grid(data.get("candidates") or [])
    return data
