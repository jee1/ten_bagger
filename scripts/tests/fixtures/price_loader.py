"""Load frozen OHLCV fixtures for offline ledger tests."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

FIXTURES_DIR = Path(__file__).resolve().parent / "prices"


def load_price_fixture(name: str) -> pd.DataFrame:
    path = FIXTURES_DIR / f"{name}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    return pd.DataFrame(payload["bars"])


def bars_from_list(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)
