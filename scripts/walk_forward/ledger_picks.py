"""Published-daily pick source for ledger-backed walk-forward runs."""

from __future__ import annotations

import json
from pathlib import Path

from config import DAILY_DIR


def ledger_pick_day(
    market: str,
    as_of_date: str,
    exclude_symbols: set[str],
    *,
    daily_dir: Path | None = None,
) -> tuple[str | None, bool]:
    """Return the committed daily pick for *as_of_date* / *market*.

    Used when ``measurementSource=ledger`` without analysis overrides so
    go_evidence measures the published policy (not a live re-screen).
    Duplicate-ban ``exclude_symbols`` is ignored — the daily already applied it.
    """
    _ = exclude_symbols
    path = (daily_dir or DAILY_DIR) / f"{as_of_date}.json"
    if not path.is_file():
        return None, True
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("market") != market:
        return None, True
    if data.get("status") != "pick":
        return None, True
    symbol = (data.get("stock") or {}).get("symbol")
    if not symbol:
        return None, True
    return str(symbol), False
