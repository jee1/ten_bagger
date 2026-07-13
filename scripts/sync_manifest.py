"""Sync manifest.json from content/daily/*.json (single source of truth)."""

from __future__ import annotations

import json
import re

from config import DAILY_DIR, MANIFEST_PATH
from time_utils import now_kst

_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def collect_daily_dates() -> list[str]:
    if not DAILY_DIR.exists():
        return []
    dates = [path.stem for path in DAILY_DIR.glob("*.json") if _DATE_PATTERN.match(path.stem)]
    return sorted(dates, reverse=True)


def build_manifest() -> dict:
    return {
        "dates": collect_daily_dates(),
        "lastUpdated": now_kst().isoformat(timespec="seconds"),
    }


def sync_manifest() -> dict:
    manifest = build_manifest()
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> int:
    manifest = sync_manifest()
    print(f"Synced {MANIFEST_PATH} ({len(manifest['dates'])} dates)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
