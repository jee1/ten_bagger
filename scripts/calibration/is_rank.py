"""IS candidate ranking via walk-forward metrics."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, overload

from calibration.candidates import CandidateSpec, validate_weights
from calibration.config import CalibrationRunConfig

RunWfDictFn = Callable[[CandidateSpec], dict[str, Any]]
RunWalkForwardFn = Callable[..., tuple[dict[str, Any], str, str]]


def h20_excess_mean(report: dict[str, Any]) -> float | None:
    horizons = (report.get("aggregate") or {}).get("horizons") or []
    values = [
        float(h["excessReturnMean"])
        for h in horizons
        if h.get("horizonId") == "H20" and h.get("excessReturnMean") is not None
    ]
    if not values:
        return None
    return sum(values) / len(values)


def _sort_key(entry: dict[str, Any]) -> tuple:
    excess = entry.get("isMetricH20ExcessMean")
    excess_key = float("-inf") if excess is None else float(excess)
    return (-excess_key, -int(entry.get("isPickDays") or 0), entry["candidateId"])


def rank_candidates_is(
    candidates: list[CandidateSpec],
    *,
    run_wf: RunWfDictFn,
) -> list[dict[str, Any]]:
    """Evaluate each candidate on IS walk-forward; return ranking entries."""
    ranked: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for candidate in candidates:
        if candidate.weights is not None:
            try:
                validate_weights(candidate.weights)
            except ValueError:
                rejected.append(
                    {
                        "candidateId": candidate.candidateId,
                        "rank": 0,
                        "isMetricH20ExcessMean": None,
                        "isPickDays": 0,
                        "walkForwardReportPath": "",
                        "walkForwardConfigHash": "0" * 64,
                        "status": "rejected_invalid",
                    }
                )
                continue

        try:
            result = run_wf(candidate)
            report = result["report"]
            ranked.append(
                {
                    "candidateId": candidate.candidateId,
                    "rank": 0,
                    "isMetricH20ExcessMean": h20_excess_mean(report),
                    "isPickDays": int((report.get("coverage") or {}).get("oosPickDays") or 0),
                    "walkForwardReportPath": result.get("path") or "",
                    "walkForwardConfigHash": result.get("configHash") or ("0" * 64),
                    "status": "ranked",
                }
            )
        except Exception:
            rejected.append(
                {
                    "candidateId": candidate.candidateId,
                    "rank": 0,
                    "isMetricH20ExcessMean": None,
                    "isPickDays": 0,
                    "walkForwardReportPath": "",
                    "walkForwardConfigHash": "0" * 64,
                    "status": "failed",
                }
            )

    ranked.sort(key=_sort_key)
    out: list[dict[str, Any]] = []
    for i, entry in enumerate(ranked, start=1):
        out.append({**entry, "rank": i})
    next_rank = len(out) + 1
    for entry in rejected:
        out.append({**entry, "rank": next_rank})
        next_rank += 1
    return out


def rank_candidates(
    cal_config: CalibrationRunConfig,
    *,
    run_walk_forward: RunWalkForwardFn,
) -> tuple[list[dict[str, Any]], str]:
    """IS ranking for a full CalibrationRunConfig (used by runner)."""

    def _wf(candidate: CandidateSpec) -> dict[str, Any]:
        report, path, cfg_hash = run_walk_forward(
            candidate,
            fold_spec=cal_config.isFoldSpec,
            run_intent="exploratory",
            measurement_source=cal_config.measurementSourceIs,
            label="is",
        )
        return {"report": report, "path": path, "configHash": cfg_hash}

    ranking = rank_candidates_is(cal_config.candidates, run_wf=_wf)
    rationale = (
        "IS ranking by H20 excess return mean (desc), "
        "tie-break isPickDays then candidateId"
    )
    return ranking, rationale


@overload
def select_promotees(
    ranking: list[dict[str, Any]],
    *,
    promote_top_n: int = 1,
) -> tuple[list[dict[str, Any]], str]: ...


@overload
def select_promotees(
    ranking: list[dict[str, Any]],
    candidates: list[CandidateSpec],
    promote_top_n: int,
) -> list[CandidateSpec]: ...


def select_promotees(ranking, candidates=None, promote_top_n=None, **kwargs):
    """Select top-N promotees.

    - ``select_promotees(ranking, promote_top_n=1)`` → ``(rows, rationale)``
    - ``select_promotees(ranking, candidates, n)`` → ``list[CandidateSpec]``
    """
    if kwargs.get("promote_top_n") is not None and candidates is None:
        promote_top_n = kwargs["promote_top_n"]

    if isinstance(candidates, list) and isinstance(promote_top_n, int):
        by_id = {c.candidateId: c for c in candidates}
        ranked_ids = [r["candidateId"] for r in ranking if r.get("status") == "ranked"]
        return [by_id[cid] for cid in ranked_ids[:promote_top_n] if cid in by_id]

    n = 1 if promote_top_n is None else int(promote_top_n)
    rows = [r for r in ranking if r.get("status") == "ranked"][:n]
    ids = ", ".join(r["candidateId"] for r in rows) or "(none)"
    rationale = (
        f"Selected top {n} by IS H20 excess return mean (desc), "
        f"tie-break isPickDays then candidateId: {ids}"
    )
    return rows, rationale
