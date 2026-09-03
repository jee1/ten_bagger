"""Pure GO/NO-GO verdict from walk-forward OOS report aggregates."""

from __future__ import annotations

from typing import Any

GO_EVIDENCE_MIN_PICK_DAYS = 20


def _mean_excess(report: dict[str, Any], horizon_id: str) -> float | None:
    horizons = (report.get("aggregate") or {}).get("horizons") or []
    values = [
        float(h["excessReturnMean"])
        for h in horizons
        if h.get("horizonId") == horizon_id and h.get("excessReturnMean") is not None
    ]
    if not values:
        return None
    return sum(values) / len(values)


def _contamination(report: dict[str, Any]) -> list[str]:
    findings = report.get("contaminationFindings")
    if isinstance(findings, list):
        return [str(f) for f in findings]
    return []


def _folds_incomplete(report: dict[str, Any]) -> bool:
    folds = report.get("folds") or []
    if not folds:
        return False
    return any(f.get("status") not in ("complete", "skipped_empty_train") for f in folds)


def verdict_from_oos_report(
    report: dict[str, Any],
    *,
    candidate_id: str,
    walk_forward_report_path: str,
    walk_forward_config_hash: str,
    package_intent: str | None = None,
) -> dict[str, Any]:
    """Map WF OOS report → OosEvaluationEntry with GO/NO-GO.

    Hard bullets: coverage ≥20, H20 excess > 0, no contamination, complete folds.
    ``no_pick`` ratio is informational only.
    """
    intent = package_intent or report.get("runIntent") or "go_evidence"
    coverage = report.get("coverage") or {}
    oos_pick_days = int(coverage.get("oosPickDays") or 0)
    no_pick_ratio = float(coverage.get("noPickRatio") or 0.0)
    insufficient = bool(coverage.get("insufficientCoverage"))
    if oos_pick_days < GO_EVIDENCE_MIN_PICK_DAYS:
        insufficient = True

    h20 = _mean_excess(report, "H20")
    h60 = _mean_excess(report, "H60")
    contamination = _contamination(report)
    failed: list[str] = []

    if insufficient:
        failed.append("insufficient_coverage")
    if h20 is None or h20 <= 0:
        failed.append("h20_excess_not_positive")
    if contamination:
        failed.append("contamination")
    if _folds_incomplete(report):
        failed.append("incomplete_horizons")

    # Soft: no_pick never added as hard failure
    _ = intent  # reserved for future intent-scoped soft rules
    verdict = "GO" if not failed else "NO-GO"
    return {
        "candidateId": candidate_id,
        "walkForwardReportPath": walk_forward_report_path,
        "walkForwardConfigHash": walk_forward_config_hash,
        "oosPickDays": oos_pick_days,
        "noPickRatio": no_pick_ratio,
        "h20ExcessReturnMean": h20,
        "h60ExcessReturnMean": h60,
        "insufficientCoverage": insufficient,
        "contaminationFindings": contamination,
        "verdict": verdict,
        "failedBullets": failed,
    }


def overall_verdict(
    entries: list[dict[str, Any]],
    *,
    package_intent: str,
    incomplete: bool = False,
) -> tuple[str, list[str]]:
    """Combine per-candidate OOS entries into package overall verdict."""
    if package_intent != "go_evidence":
        return "N/A", []

    bullets: list[str] = []
    if incomplete:
        bullets.append("incomplete_required_evaluations")
        return "NO-GO", bullets

    if not entries:
        bullets.append("no_oos_evaluations")
        return "NO-GO", bullets

    if any(e.get("verdict") != "GO" for e in entries):
        for e in entries:
            if e.get("verdict") != "GO":
                bullets.extend(e.get("failedBullets") or ["NO-GO"])
        return "NO-GO", bullets

    return "GO", []
