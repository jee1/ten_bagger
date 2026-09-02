"""Load performance bundle measurements for ledger-backed walk-forward runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MeasurementKey = tuple[str, str, str]


def load_performance_index(performance_dir: Path | str) -> dict[MeasurementKey, dict[str, Any]]:
    """Index measurements from ``content/performance/*.json`` by pickDate+symbol+horizon."""
    root = Path(performance_dir)
    index: dict[MeasurementKey, dict[str, Any]] = {}
    if not root.is_dir():
        return index

    for path in sorted(root.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"corrupt performance bundle {path}: {exc}; "
                f"fix JSON or run: npm run validate:content"
            ) from exc
        for measurement in payload.get("measurements") or []:
            key = (
                measurement["pickDate"],
                measurement["symbol"],
                measurement["horizonId"],
            )
            index[key] = measurement
    return index


def lookup_measurement(
    index: dict[MeasurementKey, dict[str, Any]],
    *,
    pick_date: str,
    symbol: str,
    horizon_id: str,
    run_intent: str,
) -> dict[str, Any] | None:
    key = (pick_date, symbol, horizon_id)
    if key in index:
        return index[key]
    if run_intent == "go_evidence":
        raise ValueError(
            f"missing ledger measurement for pickDate={pick_date} symbol={symbol} "
            f"horizonId={horizon_id}; regenerate with: "
            f"npm run regenerate:ledger -- --as-of-date <YYYY-MM-DD>"
        )
    return None
