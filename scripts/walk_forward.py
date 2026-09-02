#!/usr/bin/env python3
"""Point-in-time walk-forward harness CLI (#66)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from config import WALK_FORWARD_DIR
from walk_forward.config import load_run_config
from walk_forward.execute import execute_run
from walk_forward.folds import build_decision_sessions, generate_rolling_folds


def _run(args: argparse.Namespace) -> int:
    config_path = Path(args.config)
    if not config_path.is_file():
        print(f"error: config not found: {config_path}", file=sys.stderr)
        return 2

    try:
        run_config = load_run_config(config_path)
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    fold_spec = run_config.foldSpec
    try:
        sessions = build_decision_sessions(
            fold_spec["startDate"],
            fold_spec["endDate"],
            run_config.markets,
        )
        folds = generate_rolling_folds(fold_spec, sessions)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"error: fold calendar failed: {exc}", file=sys.stderr)
        return 1

    output_dir = Path(args.output_dir) if args.output_dir else run_config.outputDir

    if args.dry_run:
        print(
            f"dry-run ok runIntent={run_config.runIntent} "
            f"measurementSource={run_config.measurementSource} "
            f"folds={len(folds)} sessions={len(sessions)}"
        )
        return 0

    try:
        execute_run(
            run_config,
            folds,
            output_dir=output_dir,
            json_only=args.json_only,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"error: run failed: {exc}", file=sys.stderr)
        return 1

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="walk_forward.py")
    sub = parser.add_subparsers(dest="command")

    run_parser = sub.add_parser("run", help="Execute walk-forward evaluation")
    run_parser.add_argument("--config", required=True, help="Path to run-config.json")
    run_parser.add_argument(
        "--output-dir",
        default=None,
        help=f"Override output directory (default: {WALK_FORWARD_DIR})",
    )
    run_parser.add_argument(
        "--json-only",
        action="store_true",
        help="Print report JSON to stdout; skip human summary",
    )
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate config and fold calendar; no write",
    )

    args = parser.parse_args(argv)
    if args.command != "run":
        parser.print_help()
        return 2

    return _run(args)


if __name__ == "__main__":
    raise SystemExit(main())
