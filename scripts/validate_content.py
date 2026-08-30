#!/usr/bin/env python3
"""Validate content JSON files against schemas (daily + optional ledger/performance)."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
from config import (
    DAILY_DIR,
    LEDGER_DIR,
    LEDGER_SCHEMA_PATH,
    MANIFEST_PATH,
    PERFORMANCE_BUNDLE_SCHEMA_PATH,
    PERFORMANCE_DIR,
    SCHEMA_PATH,
)
from sync_manifest import collect_daily_dates


def load_validator(
    schema_path: Path = SCHEMA_PATH,
) -> jsonschema.Draft202012Validator:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    return jsonschema.Draft202012Validator(schema)


def validate_manifest() -> list[str]:
    errors: list[str] = []
    if not MANIFEST_PATH.exists():
        errors.append("manifest.json is missing")
        return errors

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    manifest_dates = manifest.get("dates", [])
    file_dates = collect_daily_dates()
    if manifest_dates != file_dates:
        errors.append(
            f"manifest dates mismatch: manifest={len(manifest_dates)} files={len(file_dates)}"
        )
    return errors


def _validate_dir(
    directory: Path,
    validator: jsonschema.Draft202012Validator,
    label: str,
) -> tuple[int, int]:
    """Validate-if-present: skip missing dirs. Returns (file_count, error_count)."""
    if not directory.exists():
        return 0, 0
    errors_found = 0
    paths = sorted(directory.glob("*.json"))
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
        if errors:
            errors_found += len(errors)
            print(f"{label}/{path.name}:")
            for err in errors:
                loc = ".".join(str(p) for p in err.path) or "(root)"
                print(f"  - {loc}: {err.message}")
    return len(paths), errors_found


def main() -> int:
    validator = load_validator()

    if not DAILY_DIR.exists():
        print("No daily content directory; skipping validation.")
        return 0

    errors_found = 0
    for path in sorted(DAILY_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
        if errors:
            errors_found += len(errors)
            print(f"{path.name}:")
            for err in errors:
                loc = ".".join(str(p) for p in err.path) or "(root)"
                print(f"  - {loc}: {err.message}")

    for err in validate_manifest():
        errors_found += 1
        print(f"manifest: {err}")

    ledger_n, ledger_err = _validate_dir(
        LEDGER_DIR, load_validator(LEDGER_SCHEMA_PATH), "ledger"
    )
    perf_n, perf_err = _validate_dir(
        PERFORMANCE_DIR,
        load_validator(PERFORMANCE_BUNDLE_SCHEMA_PATH),
        "performance",
    )
    errors_found += ledger_err + perf_err

    if errors_found:
        print(f"Validation failed: {errors_found} error(s)")
        return 1

    count = len(list(DAILY_DIR.glob("*.json")))
    extras = []
    if ledger_n:
        extras.append(f"{ledger_n} ledger")
    if perf_n:
        extras.append(f"{perf_n} performance")
    extra_msg = f" + {', '.join(extras)}" if extras else ""
    print(f"Validated {count} daily file(s) and manifest{extra_msg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
