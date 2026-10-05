"""Walk-forward run orchestration (shared by CLI and tests)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from config import WALK_FORWARD_DIR, WALK_FORWARD_SCHEMA_PATH
from performance.prices_live import default_benchmark_provider, default_price_provider
from performance.write_atomic import atomic_replace
from validate_content import load_validator

from walk_forward.config import RunConfig, config_hash, effective_measurement_as_of
from walk_forward.ledger_picks import ledger_pick_day
from walk_forward.measure import (
    fixture_benchmark_provider,
    fixture_price_provider,
    measure_oos_picks,
)
from walk_forward.pit_screen import bind_pit_fn
from walk_forward.report import build_report, serialize_report
from walk_forward.runner import run_folds


def run_id(run_config: RunConfig) -> str:
    return config_hash(run_config)[:16]


def generated_at_from_config(run_config: RunConfig) -> str:
    """Deterministic stamp from measurement cutoff (falls back to fold end)."""
    return f"{effective_measurement_as_of(run_config)}T23:59:59Z"


def _measurement_providers(run_config: RunConfig, as_of: str):
    if run_config.measurementSource == "fixture-recompute":
        return fixture_price_provider(as_of), fixture_benchmark_provider(as_of)
    return default_price_provider(as_of), default_benchmark_provider(as_of)


def make_measure_fn(run_config: RunConfig):
    as_of = effective_measurement_as_of(run_config)
    price_provider, benchmark_provider = _measurement_providers(run_config, as_of)

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
    as_of = effective_measurement_as_of(run_config)
    measure_fn = make_measure_fn(run_config)
    pit_fn = None
    if run_config.thresholdOverride is not None or run_config.weightOverrides:
        # Counterfactual policy: live PIT re-screen (ledger rows may be missing).
        pit_fn = bind_pit_fn(
            threshold_override=run_config.thresholdOverride,
            weight_overrides=run_config.weightOverrides,
        )
    elif run_config.measurementSource == "ledger":
        # Published policy: committed daily picks + performance ledger returns.
        pit_fn = ledger_pick_day
    fold_results = run_folds(
        run_config,
        folds,
        measure_fn,
        pit_fn=pit_fn,
        as_of_date=as_of,
    )
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
