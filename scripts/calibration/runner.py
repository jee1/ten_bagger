"""Orchestrate calibration search / baseline-only runs."""

from __future__ import annotations

import io
import sys
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any

from config import CALIBRATION_SCHEMA_PATH
from performance.write_atomic import atomic_replace
from validate_content import load_validator
from walk_forward.config import RunConfig
from walk_forward.config import config_hash as wf_config_hash
from walk_forward.execute import execute_run, generated_at_from_config
from walk_forward.folds import build_decision_sessions, generate_rolling_folds

from calibration.candidates import CandidateSpec
from calibration.config import CalibrationRunConfig, config_hash
from calibration.is_rank import rank_candidates, select_promotees
from calibration.report import build_report, serialize_report
from calibration.verdict import overall_verdict, verdict_from_oos_report

# Guard: never use the snapshot screen comparator for GO evidence (FR-017 / FR-026).

LIVE_BASELINE_CANDIDATE_ID = "score-v2-baseline"


def _candidate_to_wf_config(
    cal_config: CalibrationRunConfig,
    candidate: CandidateSpec | None,
    *,
    fold_spec: dict[str, Any],
    run_intent: str,
    measurement_source: str,
) -> RunConfig:
    cid = candidate.candidateId if candidate else LIVE_BASELINE_CANDIDATE_ID
    return RunConfig(
        runIntent=run_intent,
        measurementSource=measurement_source,
        candidateId=cid,
        markets=list(cal_config.markets),
        foldSpec=dict(fold_spec),
        weightOverrides=dict(candidate.weights) if candidate and candidate.weights else None,
        thresholdOverride=candidate.threshold if candidate else None,
        ledgerDir=cal_config.ledgerDir,
        performanceDir=cal_config.performanceDir,
        outputDir=cal_config.walkForwardOutputDir,
    )


def _run_walk_forward_for_candidate(
    cal_config: CalibrationRunConfig,
    candidate: CandidateSpec | None,
    *,
    fold_spec: dict[str, Any],
    run_intent: str,
    measurement_source: str,
    label: str,
    write: bool = True,
) -> tuple[dict[str, Any], str, str]:
    try:
        import walk_forward  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "walk-forward harness (#66) is required for calibration; "
            "try: npm run walk-forward -- --help"
        ) from exc

    wf_cfg = _candidate_to_wf_config(
        cal_config,
        candidate,
        fold_spec=fold_spec,
        run_intent=run_intent,
        measurement_source=measurement_source,
    )
    sessions = build_decision_sessions(
        fold_spec["startDate"],
        fold_spec["endDate"],
        cal_config.markets,
    )
    folds = generate_rolling_folds(fold_spec, sessions)
    with redirect_stdout(io.StringIO()):
        report = execute_run(
            wf_cfg,
            folds,
            output_dir=cal_config.walkForwardOutputDir,
            json_only=False,
            generated_at=generated_at_from_config(wf_cfg),
            write=write,
        )
    cfg_hash = wf_config_hash(wf_cfg)
    rel_path = f"{cal_config.walkForwardOutputDir.name}/{cfg_hash[:16]}.json"
    return report, rel_path, cfg_hash


def _should_append_live_baseline(
    compare_to_live_baseline: bool,
    promotee_evaluations: list[dict[str, Any]],
) -> bool:
    """True when side-by-side baseline OOS is requested and not already evaluated."""
    if not compare_to_live_baseline:
        return False
    return not any(e.get("candidateId") == LIVE_BASELINE_CANDIDATE_ID for e in promotee_evaluations)


def _print_pr_hint(
    report: dict[str, Any],
    *,
    go: bool,
    mode: str,
    package_intent: str,
    compare_to_live_baseline: bool = False,
) -> None:
    if go and mode == "search" and package_intent == "go_evidence":
        if compare_to_live_baseline:
            # Issue #69 growth-reallocation adoption path
            print(
                "GO: do not auto-edit scripts/config.py. "
                "Open an explicit PR with SCORE_VERSION=3 and approved weights, "
                "linking this calibration report and "
                "walk-forward go_evidence artifacts; cite "
                "docs/architecture/threshold-weight-merge-criteria.md"
            )
        else:
            # Issue #67 threshold/weight calibration — version bump not implied
            print(
                "GO: do not auto-edit scripts/config.py. "
                "Open an explicit PR linking this calibration report and "
                "walk-forward go_evidence artifacts; cite "
                "docs/architecture/threshold-weight-merge-criteria.md"
            )
        print(f"calibration report runId={report.get('runId')}")
    elif go and mode == "baseline-only":
        print(
            "baseline GO supports freeze evidence only; "
            "no config-change PR (live COMPOSITE_THRESHOLD / WEIGHT_* stay frozen)"
        )
    else:
        print(
            "NO-GO or exploratory: live COMPOSITE_THRESHOLD / WEIGHT_* stay frozen; "
            "no config-change PR implied"
        )


def execute_calibration(
    cal_config: CalibrationRunConfig,
    *,
    output_dir: Path | None = None,
    json_only: bool = False,
    write: bool = True,
) -> int:
    out_dir = output_dir or cal_config.outputDir
    incomplete = False
    is_ranking: list[dict[str, Any]] = []
    selection_rationale = "baseline-only: no IS search; OOS evaluates frozen live constants"
    promotee_specs: list[CandidateSpec | None] = []

    if cal_config.mode == "search":

        def _wf_runner(candidate, *, fold_spec, run_intent, measurement_source, label):
            return _run_walk_forward_for_candidate(
                cal_config,
                candidate,
                fold_spec=fold_spec,
                run_intent=run_intent,
                measurement_source=measurement_source,
                label=label,
                write=write,
            )

        is_ranking, selection_rationale = rank_candidates(cal_config, run_walk_forward=_wf_runner)
        promotee_specs = select_promotees(is_ranking, cal_config.candidates, cal_config.promoteTopN)
        if not promotee_specs:
            incomplete = True
    else:
        promotee_specs = [None]

    oos_intent = "go_evidence" if cal_config.packageIntent == "go_evidence" else "exploratory"
    oos_source = cal_config.measurementSourceOos
    oos_evaluations: list[dict[str, Any]] = []

    for candidate in promotee_specs:
        try:
            wf_report, path, cfg_hash = _run_walk_forward_for_candidate(
                cal_config,
                candidate,
                fold_spec=cal_config.oosFoldSpec,
                run_intent=oos_intent if oos_source == "ledger" else "exploratory",
                measurement_source=oos_source,
                label="oos",
                write=write,
            )
        except ImportError:
            raise
        except Exception as exc:
            incomplete = True
            cid = candidate.candidateId if candidate else LIVE_BASELINE_CANDIDATE_ID
            msg = str(exc)
            if "ledger" in msg.lower() or "missing" in msg.lower():
                raise ValueError(
                    f"{msg}; regenerate with: "
                    "npm run regenerate:ledger -- --as-of-date <YYYY-MM-DD>"
                ) from exc
            oos_evaluations.append(
                {
                    "candidateId": cid,
                    "walkForwardReportPath": "",
                    "walkForwardConfigHash": "0" * 64,
                    "oosPickDays": 0,
                    "noPickRatio": 0.0,
                    "h20ExcessReturnMean": None,
                    "h60ExcessReturnMean": None,
                    "insufficientCoverage": True,
                    "contaminationFindings": [f"evaluation_failed:{exc}"],
                    "verdict": "NO-GO",
                    "failedBullets": ["evaluation_failed"],
                }
            )
            continue

        cid = candidate.candidateId if candidate else LIVE_BASELINE_CANDIDATE_ID
        entry = verdict_from_oos_report(
            wf_report,
            candidate_id=cid,
            walk_forward_report_path=path,
            walk_forward_config_hash=cfg_hash,
            package_intent=cal_config.packageIntent,
        )
        oos_evaluations.append(entry)

    # Overall GO/NO-GO from promotees only; baseline row is side-by-side comparison.
    overall, failed = overall_verdict(
        oos_evaluations,
        package_intent=cal_config.packageIntent,
        incomplete=incomplete,
    )

    if _should_append_live_baseline(cal_config.compareToLiveBaseline, oos_evaluations):
        try:
            wf_report, path, cfg_hash = _run_walk_forward_for_candidate(
                cal_config,
                None,
                fold_spec=cal_config.oosFoldSpec,
                run_intent=oos_intent if oos_source == "ledger" else "exploratory",
                measurement_source=oos_source,
                label="oos-baseline",
                write=write,
            )
        except ImportError:
            raise
        except Exception as exc:
            msg = str(exc)
            if "ledger" in msg.lower() or "missing" in msg.lower():
                raise ValueError(
                    f"{msg}; regenerate with: "
                    "npm run regenerate:ledger -- --as-of-date <YYYY-MM-DD>"
                ) from exc
            oos_evaluations.append(
                {
                    "candidateId": LIVE_BASELINE_CANDIDATE_ID,
                    "walkForwardReportPath": "",
                    "walkForwardConfigHash": "0" * 64,
                    "oosPickDays": 0,
                    "noPickRatio": 0.0,
                    "h20ExcessReturnMean": None,
                    "h60ExcessReturnMean": None,
                    "insufficientCoverage": True,
                    "contaminationFindings": [f"evaluation_failed:{exc}"],
                    "verdict": "NO-GO",
                    "failedBullets": ["evaluation_failed"],
                }
            )
        else:
            oos_evaluations.append(
                verdict_from_oos_report(
                    wf_report,
                    candidate_id=LIVE_BASELINE_CANDIDATE_ID,
                    walk_forward_report_path=path,
                    walk_forward_config_hash=cfg_hash,
                    package_intent=cal_config.packageIntent,
                )
            )

    run_id = config_hash(cal_config)[:16]
    generated_at = f"{cal_config.oosFoldSpec['endDate']}T23:59:59Z"
    report = build_report(
        cal_config=cal_config,
        run_id=run_id,
        generated_at=generated_at,
        is_ranking=is_ranking,
        selection_rationale=selection_rationale,
        oos_evaluations=oos_evaluations,
        overall=overall,
        failed_bullets=failed,
    )

    if write:
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{run_id}.json"
        atomic_replace({out_path: report}, [load_validator(CALIBRATION_SCHEMA_PATH)])

    if json_only:
        sys.stdout.write(serialize_report(report).decode("utf-8"))
        sys.stdout.write("\n")
    else:
        print(
            f"calibration runId={run_id} mode={cal_config.mode} "
            f"packageIntent={cal_config.packageIntent} overallVerdict={overall}"
        )
        if write:
            print(f"report written: {out_dir / run_id}.json")
        if cal_config.mode == "baseline-only":
            print(
                "baseline-only: GO/NO-GO applies to frozen live constants only; "
                "does not authorize COMPOSITE_THRESHOLD / WEIGHT_* changes"
            )
        _print_pr_hint(
            report,
            go=(overall == "GO"),
            mode=cal_config.mode,
            package_intent=cal_config.packageIntent,
            compare_to_live_baseline=cal_config.compareToLiveBaseline,
        )

    if cal_config.packageIntent == "go_evidence" and overall == "NO-GO":
        return 3
    return 0
