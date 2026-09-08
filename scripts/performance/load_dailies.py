"""Load eligible daily pick records for ledger regenerate."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import jsonschema
from config import SCHEMA_PATH


@lru_cache(maxsize=1)
def _daily_validator() -> jsonschema.Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return jsonschema.Draft202012Validator(schema)


def _require_ledger_contract(data: object, path_name: str) -> dict:
    """Fail-fast via daily-entry schema (FR-018 + site fields writers already emit)."""
    if not isinstance(data, dict):
        raise ValueError(f"invalid daily JSON: {path_name}: root must be object")
    errors = sorted(_daily_validator().iter_errors(data), key=lambda e: list(e.absolute_path))
    if errors:
        err = errors[0]
        loc = ".".join(str(p) for p in err.absolute_path) or "(root)"
        raise ValueError(f"invalid daily JSON: {path_name}: {loc}: {err.message}")
    return data


def load_eligible_dailies(daily_dir: Path, as_of_date: str) -> list[dict]:
    """Return daily records with date <= asOfDate; corrupt/invalid JSON raises."""
    if not daily_dir.exists():
        return []
    records: list[dict] = []
    for path in sorted(daily_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"corrupt daily JSON: {path.name}") from exc
        data = _require_ledger_contract(data, path.name)
        date = data["date"]
        if date > as_of_date:
            continue
        records.append(data)
    records.sort(key=lambda r: r["date"])
    return records
