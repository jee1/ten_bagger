"""Point-in-time fundamentals snapshots for walk-forward re-screening (#175 stage 2).

Snapshots live in the private ``jee1/ten_bagger-pit`` repo; ``content/pit/manifest.json``
pins each file's sha256. Point ``PIT_DATA_DIR`` at a local clone of that repo.
"""

from __future__ import annotations

import gzip
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, time
from functools import cache
from pathlib import Path
from typing import Any, Literal

from config import PIT_DATA_DIR, PIT_MANIFEST_PATH, market_for_date
from pit_snapshot import SCORING_INFO_FIELDS, verify_file_sha256
from time_utils import KST

from walk_forward.config import RunConfig

logger = logging.getLogger(__name__)

PIT_MIN_COVERAGE = 0.95

PitStatus = Literal["ok", "missing", "low_coverage"]


@dataclass(frozen=True)
class FundamentalsSnapshot:
    market: str
    date: str
    sha256: str
    # symbol -> scoring info fields only (provenance keys stripped)
    infos: dict[str, dict[str, Any]]
    coverage: float


def pit_data_dir() -> Path:
    return Path(os.environ.get("PIT_DATA_DIR") or PIT_DATA_DIR)


def _known_by(row: dict[str, Any], as_of_date: str) -> bool:
    known_at = row.get("knownAt")
    if not known_at:
        return False
    cutoff = datetime.combine(datetime.fromisoformat(as_of_date).date(), time.max, tzinfo=KST)
    return datetime.fromisoformat(str(known_at)) <= cutoff


@cache
def _load(market: str, as_of_date: str, data_dir: Path, manifest_path: Path):
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entry = next(
        (
            e
            for e in manifest.get("entries") or []
            if e.get("date") == as_of_date and e.get("market") == market
        ),
        None,
    )
    if entry is None:
        return None
    if not data_dir.is_dir():
        logger.warning(
            "PIT_DATA_DIR %s missing; %s %s treated as non-PIT", data_dir, market, as_of_date
        )
        return None
    block = entry["fundamentals"]
    path = data_dir / block["path"]
    # Manifest says the file exists: a missing or altered local copy is an error, not non-PIT.
    verify_file_sha256(path, block["sha256"])
    rows = [json.loads(line) for line in gzip.decompress(path.read_bytes()).splitlines()]
    infos: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not _known_by(row, as_of_date):
            continue
        infos[row["symbol"]] = {k: row[k] for k in SCORING_INFO_FIELDS if k in row}
    usable = sum(1 for info in infos.values() if info)
    return FundamentalsSnapshot(
        market=market,
        date=as_of_date,
        sha256=block["sha256"],
        infos=infos,
        coverage=usable / len(rows) if rows else 0.0,
    )


def load_fundamentals_snapshot(market: str, as_of_date: str) -> FundamentalsSnapshot | None:
    """Snapshot captured by the daily run for *as_of_date*, or None when absent."""
    if not PIT_MANIFEST_PATH.exists():
        return None
    return _load(market, as_of_date, pit_data_dir(), PIT_MANIFEST_PATH)


def fundamentals_pit_status(market: str, as_of_date: str) -> PitStatus:
    snapshot = load_fundamentals_snapshot(market, as_of_date)
    if snapshot is None:
        return "missing"
    if snapshot.coverage < PIT_MIN_COVERAGE:
        return "low_coverage"
    return "ok"


def _uses_override_rescreen(run_config: RunConfig) -> bool:
    return run_config.thresholdOverride is not None or bool(run_config.weightOverrides)


def fundamentals_pit_audit(
    run_config: RunConfig,
    fold_results: list[dict[str, Any]],
) -> tuple[list[str], dict[str, Any] | None]:
    """Contamination tags and snapshot provenance for live override re-screen.

    Ledger pick replay is not re-screened, so it gets neither.
    """
    if not _uses_override_rescreen(run_config):
        return [], None

    markets = set(run_config.markets)
    # Rolling folds overlap; judge each session once (#178).
    sessions = {
        s
        for fold in fold_results
        for s in [*(fold.get("trainSessions") or []), *(fold.get("oosSessions") or [])]
        if market_for_date(s) in markets
    }
    status = {s: fundamentals_pit_status(market_for_date(s), s) for s in sorted(sessions)}

    findings: list[str] = []
    missing = sum(1 for v in status.values() if v == "missing")
    low = sum(1 for v in status.values() if v == "low_coverage")
    if missing:
        findings.append(f"fundamentals_not_pit:{missing}")
    if low:
        findings.append(f"fundamentals_low_coverage:{low}")

    used = [
        snap
        for s, v in status.items()
        if v != "missing" and (snap := load_fundamentals_snapshot(market_for_date(s), s))
    ]
    provenance = None
    if used:
        provenance = {
            "from": used[0].date,
            "to": used[-1].date,
            "sha256": sorted({snap.sha256 for snap in used}),
        }
    return findings, provenance
