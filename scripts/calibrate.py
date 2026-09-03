#!/usr/bin/env python3
"""Threshold·weight GO/NO-GO calibration CLI (#67)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _run(args: argparse.Namespace) -> int:
    config_path = Path(args.config)
    if not config_path.is_file():
        print(f"error: config not found: {config_path}", file=sys.stderr)
        return 2

    try:
        from calibration.config import load_calibration_config
        from calibration.runner import execute_calibration
    except ImportError as exc:
        print(
            f"error: calibration package unavailable ({exc}); "
            "ensure scripts/calibration is present and walk-forward harness (#66) is installed",
            file=sys.stderr,
        )
        return 2

    try:
        cal_config = load_calibration_config(config_path)
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.dry_run:
        n = len(cal_config.candidates)
        print(
            f"dry-run ok packageIntent={cal_config.packageIntent} "
            f"mode={cal_config.mode} candidates={n} "
            f"isFold={cal_config.isFoldSpec.get('startDate')}.."
            f"{cal_config.isFoldSpec.get('endDate')} "
            f"oosFold={cal_config.oosFoldSpec.get('startDate')}.."
            f"{cal_config.oosFoldSpec.get('endDate')}"
        )
        return 0

    output_dir = Path(args.output_dir) if args.output_dir else None
    try:
        return execute_calibration(
            cal_config,
            output_dir=output_dir,
            json_only=args.json_only,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except ImportError as exc:
        print(
            f"error: walk-forward harness required ({exc}); try: npm run walk-forward -- --help",
            file=sys.stderr,
        )
        return 2
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Threshold·weight calibration (#67)")
    sub = parser.add_subparsers(dest="command", required=True)
    run_parser = sub.add_parser("run", help="Execute calibration search / baseline-only")
    run_parser.add_argument("--config", required=True, help="calibration-config.json path")
    run_parser.add_argument("--output-dir", default=None, help="Override calibration output dir")
    run_parser.add_argument("--json-only", action="store_true", help="Print report JSON only")
    run_parser.add_argument("--dry-run", action="store_true", help="Validate config only")
    run_parser.set_defaults(func=_run)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
