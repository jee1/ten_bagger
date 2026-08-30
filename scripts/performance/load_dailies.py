"""Load eligible daily pick records for ledger regenerate."""

from __future__ import annotations

import json
from pathlib import Path


def _require_ledger_contract(data: object, path_name: str) -> dict:
    """Fail-fast on missing identity fields (FR-018). Not full daily-entry schema.

    ponytail: regenerate only needs date/market/status/symbol; site fields
    (reasoning, meta, …) stay out of scope — upgrade if writers need stricter gate.
    """
    if not isinstance(data, dict):
        raise ValueError(f"invalid daily JSON: {path_name}: root must be object")
    for key in ("date", "market", "status"):
        if key not in data or data[key] in (None, ""):
            raise ValueError(f"invalid daily JSON: {path_name}: missing required '{key}'")
    status = data["status"]
    if status not in ("pick", "no_pick"):
        raise ValueError(f"invalid daily JSON: {path_name}: bad status {status!r}")
    if status == "pick":
        stock = data.get("stock")
        if not isinstance(stock, dict) or not stock.get("symbol"):
            raise ValueError(
                f"invalid daily JSON: {path_name}: pick requires stock.symbol"
            )
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
