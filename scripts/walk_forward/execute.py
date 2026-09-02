"""Walk-forward run orchestration (shared by CLI and tests)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from config import WALK_FORWARD_DIR, WALK_FORWARD_SCHEMA_PATH
from performance.write_atomic import atomic_replace
from validate_content import load_validator
from walk_forward.config import RunConfig, config_hash
from walk_forward.measure import (
    fixture_benchmark_provider,
    fixture_price_provider,
    measure_oos_picks,
)
from walk_forward.report import build_report, serialize_report
from walk_forward.runner import run_folds


def run_id(run_config: RunConfig) -> str:
    return config_hash(run_config)[:16]


def generated_at_from_config(run_config: RunConfig) -> str:
    """Deterministic stamp from fold end date (SC-005 / FR-011)."""
    return f"{run_config.foldSpec['endDate']}T23:59:59Z"


def make_measure_fn(run_config: RunConfig):
    as_of = run_config.foldSpec["endDate"]
    price_provider = fixture_price_provider(as_of)
    benchmark_provider = fixture_benchmark_provider(as_of)

    def measure_fn(picks, cfg, as_of_date):
        return measure_oos_picks(
            picks,
            cfg,
            as_of_date,
            price_provider,
            benchmark_provider,
        )

    return measure_fn


def human_summary(report: dict[str, Any]) -> str:
    folds = report["folds"]
    cov = report["coverage"]
    return (
        f"walk-forward runId={report['runId']} "
        f"folds={len(folds)} "
        f"oosPickDays={cov['oosPickDays']} "
        f"noPickDays={cov['noPickDays']} "
        f"insufficientCoverage={cov['insufficientCoverage']}"
    )


def execute_run(
    run_config: RunConfig,
    folds: list[dict[str, Any]],
    *,
    output_dir: Path | None = None,
    json_only: bool = False,
    generated_at: str | None = None,
    write: bool = True,
) -> dict[str, Any]:
    as_of = run_config.foldSpec["endDate"]
    measure_fn = make_measure_fn(run_config)
    fold_results = run_folds(run_config, folds, measure_fn, as_of_date=as_of)
    rid = run_id(run_config)
    report = build_report(
        run_config=run_config,
        fold_results=fold_results,
        run_id=rid,
        generated_at=generated_at or generated_at_from_config(run_config),
    )

    out = output_dir or run_config.outputDir or WALK_FORWARD_DIR
    if write:
        out.mkdir(parents=True, exist_ok=True)
        out_path = out / f"{rid}.json"
        atomic_replace(
            {out_path: report},
            [load_validator(WALK_FORWARD_SCHEMA_PATH)],
        )

    if json_only:
        sys.stdout.write(serialize_report(report).decode("utf-8"))
        sys.stdout.write("\n")
    else:
        print(human_summary(report))
        if write:
            print(f"report written: {out / rid}.json")

    return report
