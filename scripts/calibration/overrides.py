"""Process-local analysis overrides for threshold / Score v2 weights."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any
from unittest.mock import patch

import scoring.composite as scoring_composite
import screening.core as screening_core

from calibration.candidates import WEIGHT_KEYS, validate_weights


@contextmanager
def apply_candidate_overrides(
    threshold: float | None = None,
    weights: dict[str, float] | None = None,
) -> Iterator[None]:
    """Patch screening/scoring module globals for the duration of a candidate run.

    Does not modify ``scripts/config.py`` source or import-time constants on the
    ``config`` module object used for publication.
    """
    patches: list[Any] = []
    if threshold is not None:
        patches.append(patch.object(screening_core, "COMPOSITE_THRESHOLD", float(threshold)))
    if weights is not None:
        validated = validate_weights(weights)
        for key in WEIGHT_KEYS:
            patches.append(patch.object(scoring_composite, key, validated[key]))

    if not patches:
        yield
        return

    # Enter nested patches
    stack: list[Any] = []
    try:
        for p in patches:
            stack.append(p)
            p.start()
        yield
    finally:
        for p in reversed(stack):
            p.stop()
