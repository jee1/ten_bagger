#!/usr/bin/env python3
"""Validate content/daily JSON files against the daily-entry schema."""

from __future__ import annotations

import json

import jsonschema

from config import DAILY_DIR, MANIFEST_PATH, SCHEMA_PATH
from sync_manifest import collect_daily_dates


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


def main() -> int:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)

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

    if errors_found:
        print(f"Validation failed: {errors_found} error(s)")
        return 1

    count = len(list(DAILY_DIR.glob("*.json")))
    print(f"Validated {count} daily file(s) and manifest")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
