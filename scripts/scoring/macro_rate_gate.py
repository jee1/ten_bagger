"""Score v3 candidate: rate/macro gate (Fed hike-regime dummy).

Default-OFF gated module (ENABLE_MACRO_RATE_GATE_CANDIDATE). When enabled and
hike_regime is true, applies named variants threshold_raise or size_tighten on
the candidate path only — never mutates live COMPOSITE_THRESHOLD /
MIN_MARKET_CAP_* / WEIGHT_* / SCORE_VERSION.
Measurement-gated until ADR 0004 GO (Issue #70 / Epic #74).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Literal

GateVariant = Literal["threshold_raise", "size_tighten"]
MetricStatus = Literal["available", "unavailable"]

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SOURCE_LABEL = "fed_hike_regime_committed_json"

# Cached interval list after first successful load (path → intervals).
_INTERVAL_CACHE: dict[str, list[tuple[date, date]]] = {}


@dataclass(frozen=True)
class HikeRegimeSignal:
    """Binary Fed hiking-phase signal for one decision date."""

    as_of_date: str
    status: MetricStatus
    hike_regime: bool
    source: str
    reason: str | None = None


@dataclass(frozen=True)
class EffectiveSelectionKnobs:
    """Effective selection knobs on the candidate path (never writes live config)."""

    enabled: bool
    variant: GateVariant | None
    hike_regime: bool
    regime_status: MetricStatus
    gate_applied: bool
    composite_threshold: float
    min_market_cap_kr: int
    min_market_cap_us: int
    signal: HikeRegimeSignal


def _parse_iso_date(value: str, *, field: str) -> date:
    if not isinstance(value, str) or not _DATE_RE.match(value):
        raise ValueError(f"malformed regime {field}: expected YYYY-MM-DD, got {value!r}")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"malformed regime {field}: {value!r}") from exc


def _validate_and_load_intervals(payload: Any, *, path: Path) -> list[tuple[date, date]]:
    if not isinstance(payload, dict):
        raise ValueError(f"malformed regime file {path}: root must be object")
    intervals_raw = payload.get("intervals")
    if not isinstance(intervals_raw, list) or not intervals_raw:
        raise ValueError(f"malformed regime file {path}: intervals must be non-empty list")
    out: list[tuple[date, date]] = []
    for i, row in enumerate(intervals_raw):
        if not isinstance(row, dict):
            raise ValueError(f"malformed regime intervals[{i}]: expected object")
        if "start" not in row or "end" not in row:
            raise ValueError(f"malformed regime intervals[{i}]: missing start/end")
        start = _parse_iso_date(row["start"], field=f"intervals[{i}].start")
        end = _parse_iso_date(row["end"], field=f"intervals[{i}].end")
        if end < start:
            raise ValueError(f"malformed regime intervals[{i}]: end before start")
        out.append((start, end))
    return out


def load_fed_hike_regime(
    path: Path | None = None,
    *,
    force_reload: bool = False,
) -> list[tuple[date, date]]:
    """Load committed Fed hike intervals. Hard-fails on malformed JSON/rows."""
    from config import FED_HIKE_REGIME_PATH

    resolved = Path(path) if path is not None else Path(FED_HIKE_REGIME_PATH)
    key = str(resolved.resolve())
    if not force_reload and key in _INTERVAL_CACHE:
        return _INTERVAL_CACHE[key]
    if not resolved.is_file():
        raise FileNotFoundError(f"regime series not found: {resolved}")
    with resolved.open(encoding="utf-8") as fh:
        payload = json.load(fh)
    intervals = _validate_and_load_intervals(payload, path=resolved)
    _INTERVAL_CACHE[key] = intervals
    return intervals


def resolve_hike_regime(
    as_of_date: str,
    *,
    path: Path | None = None,
    force_reload: bool = False,
) -> HikeRegimeSignal:
    """Resolve hike_regime for asOfDate (YYYY-MM-DD). Gaps → unavailable (fail-open)."""
    if not isinstance(as_of_date, str) or not _DATE_RE.match(as_of_date):
        raise ValueError(f"malformed as_of_date: expected YYYY-MM-DD, got {as_of_date!r}")
    try:
        day = date.fromisoformat(as_of_date)
    except ValueError as exc:
        raise ValueError(f"malformed as_of_date: {as_of_date!r}") from exc

    intervals = load_fed_hike_regime(path, force_reload=force_reload)
    # Covered span: first start .. last end. Outside → unavailable (do not invent).
    span_start = min(s for s, _ in intervals)
    span_end = max(e for _, e in intervals)
    if day < span_start or day > span_end:
        return HikeRegimeSignal(
            as_of_date=as_of_date,
            status="unavailable",
            hike_regime=False,
            source=_SOURCE_LABEL,
            reason="outside_series_span",
        )

    for start, end in intervals:
        if start <= day <= end:
            return HikeRegimeSignal(
                as_of_date=as_of_date,
                status="available",
                hike_regime=True,
                source=_SOURCE_LABEL,
            )

    # Inside span but not in any hike interval → available non-hike (not a gap).
    # True gaps would require an explicit coverage map; v1 treats between-cycle
    # dates as available hike_regime=false (known non-hike), only outside-span
    # or missing file as unavailable. Explicit gap markers are unsupported.
    return HikeRegimeSignal(
        as_of_date=as_of_date,
        status="available",
        hike_regime=False,
        source=_SOURCE_LABEL,
    )


def effective_selection_knobs(
    *,
    as_of_date: str,
    market: str,
    variant: GateVariant = "threshold_raise",
    enabled: bool | None = None,
    path: Path | None = None,
) -> EffectiveSelectionKnobs:
    """Return effective knobs for candidate evaluation; never mutates live config.

    KR and US share the same global Fed hike dummy. ``market`` is accepted for
    API symmetry / future BOK series but does not change the v1 signal.
    """
    from config import (
        COMPOSITE_THRESHOLD,
        ENABLE_MACRO_RATE_GATE_CANDIDATE,
        MIN_MARKET_CAP_KR,
        MIN_MARKET_CAP_US,
        SIZE_TIGHTEN_MIN_MCAP_MULT,
        THRESHOLD_HIKE_DELTA,
    )

    if enabled is None:
        enabled = bool(ENABLE_MACRO_RATE_GATE_CANDIDATE)
    if variant not in ("threshold_raise", "size_tighten"):
        raise ValueError(f"unknown gate variant: {variant!r}")

    _ = market  # v1: same global Fed dummy for KR and US
    signal = resolve_hike_regime(as_of_date, path=path)

    threshold = float(COMPOSITE_THRESHOLD)
    min_kr = int(MIN_MARKET_CAP_KR)
    min_us = int(MIN_MARKET_CAP_US)
    gate_applied = False

    if (
        enabled
        and signal.status == "available"
        and signal.hike_regime
    ):
        gate_applied = True
        if variant == "threshold_raise":
            threshold = float(COMPOSITE_THRESHOLD) + float(THRESHOLD_HIKE_DELTA)
        else:
            mult = float(SIZE_TIGHTEN_MIN_MCAP_MULT)
            min_kr = int(round(MIN_MARKET_CAP_KR * mult))
            min_us = int(round(MIN_MARKET_CAP_US * mult))

    return EffectiveSelectionKnobs(
        enabled=enabled,
        variant=variant if enabled else None,
        hike_regime=bool(signal.hike_regime),
        regime_status=signal.status,
        gate_applied=gate_applied,
        composite_threshold=threshold,
        min_market_cap_kr=min_kr,
        min_market_cap_us=min_us,
        signal=signal,
    )


def clear_regime_cache() -> None:
    """Test helper: drop loaded interval cache."""
    _INTERVAL_CACHE.clear()
