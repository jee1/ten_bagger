"""Score v3 candidate: investment dummy (asset growth vs EBITDA).

Default-OFF gated module (ENABLE_INVESTMENT_DUMMY_CANDIDATE). Soft penalty +
label only on the candidate path — never folded into passes_red_flags.
Measurement-gated until ADR 0004 GO (Issue #68 / Epic #74).
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from scoring.models import ScoreResult

MetricStatus = Literal["available", "unavailable"]

_ASSET_KEYS = ("Total Assets", "totalAssets", "TotalAssets")
_EBITDA_KEYS = ("EBITDA", "Ebitda", "ebitda")


@dataclass(frozen=True)
class InvestmentDummyMetric:
    """YoY total-asset growth vs YoY EBITDA growth for one symbol/decision."""

    status: MetricStatus
    asset_growth_pct: float | None = None
    ebitda_growth_pct: float | None = None
    spread_pct: float | None = None
    investment_dummy: bool | None = None
    prior_total_assets: float | None = None
    current_total_assets: float | None = None
    prior_ebitda: float | None = None
    current_ebitda: float | None = None
    reason: str | None = None


@dataclass(frozen=True)
class CandidateAdjustment:
    """Result of applying investment-dummy soft penalty on the candidate path."""

    enabled: bool
    applied: bool
    soft_penalty: float
    label: str | None
    composite_before: float
    composite_after: float
    metric: InvestmentDummyMetric


def _is_finite_number(value: object) -> bool:
    if value is None or isinstance(value, bool):
        return False
    try:
        return math.isfinite(float(value))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return False


def compute_investment_dummy_metric(
    *,
    prior_total_assets: float | None,
    current_total_assets: float | None,
    prior_ebitda: float | None,
    current_ebitda: float | None,
) -> InvestmentDummyMetric:
    """Compute investment-dummy metric from period fundamentals.

    Growth: (current - prior) / abs(prior) * 100 when prior ≠ 0.
    Dummy true iff available and asset_growth_pct > ebitda_growth_pct (strict).
    """

    def _unavailable(reason: str) -> InvestmentDummyMetric:
        return InvestmentDummyMetric(
            status="unavailable",
            investment_dummy=False,
            reason=reason,
        )

    values = (
        prior_total_assets,
        current_total_assets,
        prior_ebitda,
        current_ebitda,
    )
    if any(not _is_finite_number(v) for v in values):
        return _unavailable("missing_inputs")

    p_assets = float(prior_total_assets)  # type: ignore[arg-type]
    c_assets = float(current_total_assets)  # type: ignore[arg-type]
    p_ebitda = float(prior_ebitda)  # type: ignore[arg-type]
    c_ebitda = float(current_ebitda)  # type: ignore[arg-type]

    if p_assets == 0.0:
        return _unavailable("zero_prior_assets")
    if p_ebitda <= 0.0 or c_ebitda <= 0.0:
        return _unavailable("non_positive_ebitda")

    asset_growth_pct = (c_assets - p_assets) / abs(p_assets) * 100.0
    ebitda_growth_pct = (c_ebitda - p_ebitda) / abs(p_ebitda) * 100.0
    spread_pct = asset_growth_pct - ebitda_growth_pct

    return InvestmentDummyMetric(
        status="available",
        asset_growth_pct=asset_growth_pct,
        ebitda_growth_pct=ebitda_growth_pct,
        spread_pct=spread_pct,
        investment_dummy=asset_growth_pct > ebitda_growth_pct,
        prior_total_assets=p_assets,
        current_total_assets=c_assets,
        prior_ebitda=p_ebitda,
        current_ebitda=c_ebitda,
    )


def _pick_line(row: Mapping[str, Any], keys: tuple[str, ...]) -> float | None:
    for key in keys:
        if key not in row:
            continue
        raw = row[key]
        if not _is_finite_number(raw):
            continue
        return float(raw)
    return None


def extract_period_fundamentals_from_statement_dicts(
    balance_sheet: Mapping[str, Mapping[str, Any]],
    income_stmt: Mapping[str, Mapping[str, Any]],
) -> dict[str, float | None]:
    """Map two most recent annual columns → four period floats (analysis-only).

    Expects period_key → {line_item: value}. Not called from the live daily path
    (research R1 / FR-009 PIT: caller must pass statements known at decision t).
    Missing or unmapped columns yield None values (caller treats as unavailable).
    """
    periods = sorted(
        set(balance_sheet) & set(income_stmt),
        reverse=True,
    )
    if len(periods) < 2:
        return {
            "prior_total_assets": None,
            "current_total_assets": None,
            "prior_ebitda": None,
            "current_ebitda": None,
        }

    current_key, prior_key = periods[0], periods[1]
    return {
        "prior_total_assets": _pick_line(balance_sheet[prior_key], _ASSET_KEYS),
        "current_total_assets": _pick_line(balance_sheet[current_key], _ASSET_KEYS),
        "prior_ebitda": _pick_line(income_stmt[prior_key], _EBITDA_KEYS),
        "current_ebitda": _pick_line(income_stmt[current_key], _EBITDA_KEYS),
    }


def apply_investment_dummy_adjustment(
    result: ScoreResult,
    metric: InvestmentDummyMetric,
    *,
    enabled: bool | None = None,
) -> CandidateAdjustment:
    """Apply soft penalty + label when candidate flag is ON and dummy hits.

    Composite is not clamped below 0 (analysis visibility). Does not touch
    hard red-flag gating — candidate path only.
    """
    from config import (
        ENABLE_INVESTMENT_DUMMY_CANDIDATE,
        INVESTMENT_DUMMY_SOFT_PENALTY,
    )

    if enabled is None:
        enabled = ENABLE_INVESTMENT_DUMMY_CANDIDATE

    composite_before = float(result.composite)
    applied = bool(enabled and metric.status == "available" and metric.investment_dummy is True)
    soft_penalty = float(INVESTMENT_DUMMY_SOFT_PENALTY) if applied else 0.0
    label = "investment_dummy" if applied else None
    composite_after = composite_before - soft_penalty

    result.metrics["investment_dummy_status"] = metric.status
    result.metrics["asset_growth_pct"] = metric.asset_growth_pct
    result.metrics["ebitda_growth_pct"] = metric.ebitda_growth_pct
    result.metrics["spread_pct"] = metric.spread_pct
    result.metrics["investment_dummy"] = metric.investment_dummy

    labels = list(result.metrics.get("red_flag_labels") or [])
    if applied and "investment_dummy" not in labels:
        labels.append("investment_dummy")
    result.metrics["red_flag_labels"] = labels

    if applied:
        result.composite = composite_after

    return CandidateAdjustment(
        enabled=bool(enabled),
        applied=applied,
        soft_penalty=soft_penalty,
        label=label,
        composite_before=composite_before,
        composite_after=composite_after,
        metric=metric,
    )


def maybe_apply_investment_dummy(
    result: ScoreResult,
    period_inputs: Mapping[str, float | None] | None = None,
    *,
    metric: InvestmentDummyMetric | None = None,
    enabled: bool | None = None,
) -> CandidateAdjustment:
    """Candidate-only hook: compute (optional) then apply. Live path must not call."""
    if metric is None:
        if period_inputs is None:
            raise ValueError("period_inputs or metric required")
        metric = compute_investment_dummy_metric(
            prior_total_assets=period_inputs.get("prior_total_assets"),
            current_total_assets=period_inputs.get("current_total_assets"),
            prior_ebitda=period_inputs.get("prior_ebitda"),
            current_ebitda=period_inputs.get("current_ebitda"),
        )
    return apply_investment_dummy_adjustment(result, metric, enabled=enabled)
