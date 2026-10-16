"""Point-in-time fundamentals/universe snapshot capture (issue #175 stage 1)."""

from __future__ import annotations

import gzip
import hashlib
import json
import logging
import subprocess
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from config import PIT_MANIFEST_PATH, PIT_STAGING_DIR, UNIVERSE_DIR
from time_utils import KST, now_kst
from yf_cache import InfoProvenance

logger = logging.getLogger(__name__)

PIT_SCHEMA_VERSION = 1
PIT_DATA_REPO = "jee1/ten_bagger-pit"

# Scoring reads only (excludes longBusinessSummary — reasoning-only, too large).
SCORING_INFO_FIELDS: tuple[str, ...] = (
    "marketCap",
    "trailingPE",
    "forwardPE",
    "pegRatio",
    "priceToBook",
    "bookValue",
    "revenueGrowth",
    "earningsGrowth",
    "quarterlyRevenueGrowthYOY",
    "quarterlyEarningsGrowthYOY",
    "operatingMargins",
    "returnOnEquity",
    "returnOnAssets",
    "debtToEquity",
    "freeCashflow",
    "operatingCashflow",
    "netIncomeToCommon",
    "numberOfAnalystOpinions",
    "sector",
    "industry",
    "longName",
    "shortName",
)


class PitSnapshotExistsError(Exception):
    """Refuse to overwrite an immutable snapshot file."""


class PitManifestShaMismatchError(Exception):
    """Manifest sha256 does not match file bytes."""


@dataclass
class PitFundamentalsCollector:
    market: str
    rows: dict[str, dict[str, Any]] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def record(self, symbol: str, info: dict[str, Any], provenance: InfoProvenance) -> None:
        row = extract_fundamental_row(symbol, self.market, info, provenance)
        with self._lock:
            self.rows[symbol] = row


def extract_fundamental_row(
    symbol: str,
    market: str,
    info: dict[str, Any],
    provenance: InfoProvenance,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "symbol": symbol,
        "market": market,
        "knownAt": provenance.known_at,
        "provider": provenance.provider,
        "cacheHit": provenance.cache_hit,
    }
    for key in SCORING_INFO_FIELDS:
        if key in info:
            row[key] = info[key]
    return row


def _universe_symbols(market: str) -> list[str]:
    rel = "kr.json" if market == "KR" else "us.json"
    path = UNIVERSE_DIR / rel
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [str(item["symbol"]) for item in raw]


def build_universe_snapshot(market: str, target_date: str) -> dict[str, Any]:
    symbols = _universe_symbols(market)
    rel = "kr.json" if market == "KR" else "us.json"
    path = UNIVERSE_DIR / rel
    if path.exists():
        mtime = path.stat().st_mtime
        built_at = datetime.fromtimestamp(mtime, tz=KST).isoformat(timespec="seconds")
    else:
        built_at = now_kst().isoformat(timespec="seconds")
    return {
        "date": target_date,
        "market": market,
        "builtAt": built_at,
        "symbols": symbols,
    }


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def verify_file_sha256(path: Path, expected_sha256: str) -> None:
    if not path.exists():
        raise PitManifestShaMismatchError(f"missing snapshot file: {path}")
    actual = sha256_file(path)
    if actual != expected_sha256:
        raise PitManifestShaMismatchError(
            f"sha256 mismatch for {path}: expected={expected_sha256} actual={actual}"
        )


def _fundamentals_rel(market: str, target_date: str) -> str:
    return f"fundamentals/{market}/{target_date}.jsonl.gz"


def _universe_rel(market: str, target_date: str) -> str:
    return f"universe/{market}/{target_date}.json.gz"


def _write_gz_atomic(path: Path, data: bytes, *, allow_existing: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not allow_existing:
        logger.warning("PIT snapshot already exists; refusing overwrite: %s", path)
        raise PitSnapshotExistsError(str(path))
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)


def write_fundamentals_snapshot(
    rows: list[dict[str, Any]],
    staging_dir: Path,
    market: str,
    target_date: str,
    *,
    allow_existing: bool = False,
) -> tuple[Path, str, int, int]:
    rel = _fundamentals_rel(market, target_date)
    path = staging_dir / rel
    lines = [json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows]
    body = ("\n".join(lines) + ("\n" if lines else "")).encode("utf-8")
    compressed = gzip.compress(body, mtime=0)
    _write_gz_atomic(path, compressed, allow_existing=allow_existing)
    digest = sha256_bytes(compressed)
    known_ats = [str(r.get("knownAt") or "") for r in rows if r.get("knownAt")]
    logger.info(
        "PIT fundamentals %s %s: bytes=%d rows=%d sha256=%s knownAt=[%s..%s]",
        market,
        target_date,
        len(compressed),
        len(rows),
        digest,
        min(known_ats) if known_ats else "",
        max(known_ats) if known_ats else "",
    )
    return path, digest, len(compressed), len(rows)


def write_universe_snapshot(
    payload: dict[str, Any],
    staging_dir: Path,
    market: str,
    target_date: str,
    *,
    allow_existing: bool = False,
) -> tuple[Path, str, int, int]:
    rel = _universe_rel(market, target_date)
    path = staging_dir / rel
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    compressed = gzip.compress(raw, mtime=0)
    _write_gz_atomic(path, compressed, allow_existing=allow_existing)
    digest = sha256_bytes(compressed)
    symbol_count = len(payload.get("symbols") or [])
    logger.info(
        "PIT universe %s %s: bytes=%d symbols=%d sha256=%s",
        market,
        target_date,
        len(compressed),
        symbol_count,
        digest,
    )
    return path, digest, len(compressed), symbol_count


def build_manifest_entry(market: str, target_date: str, root: Path) -> dict[str, Any]:
    """Manifest entry describing the snapshot files under *root* as they are on disk."""
    f_rel = _fundamentals_rel(market, target_date)
    u_rel = _universe_rel(market, target_date)
    f_bytes = (root / f_rel).read_bytes()
    u_bytes = (root / u_rel).read_bytes()
    rows = [json.loads(line) for line in gzip.decompress(f_bytes).decode("utf-8").splitlines()]
    universe = json.loads(gzip.decompress(u_bytes))
    known_ats = [str(r["knownAt"]) for r in rows if r.get("knownAt")]
    return {
        "date": target_date,
        "market": market,
        "fundamentals": {
            "path": f_rel,
            "sha256": sha256_bytes(f_bytes),
            "bytes": len(f_bytes),
            "rowCount": len(rows),
            "knownAtMin": min(known_ats) if known_ats else None,
            "knownAtMax": max(known_ats) if known_ats else None,
        },
        "universe": {
            "path": u_rel,
            "sha256": sha256_bytes(u_bytes),
            "bytes": len(u_bytes),
            "symbolCount": len(universe.get("symbols") or []),
            "builtAt": universe["builtAt"],
        },
    }


def load_pit_manifest(path: Path | None = None) -> dict[str, Any]:
    manifest_path = path or PIT_MANIFEST_PATH
    if not manifest_path.exists():
        return {"schemaVersion": PIT_SCHEMA_VERSION, "entries": []}
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def _entry_key(date: str, market: str) -> tuple[str, str]:
    return date, market


def upsert_manifest_entry(manifest: dict[str, Any], entry: dict[str, Any]) -> dict[str, Any]:
    entries = list(manifest.get("entries") or [])
    key = _entry_key(entry["date"], entry["market"])
    filtered = [e for e in entries if _entry_key(e.get("date", ""), e.get("market", "")) != key]
    filtered.append(entry)
    filtered.sort(key=lambda e: (e.get("date", ""), e.get("market", "")), reverse=True)
    return {
        "schemaVersion": manifest.get("schemaVersion", PIT_SCHEMA_VERSION),
        "lastUpdated": now_kst().isoformat(timespec="seconds"),
        "entries": filtered,
    }


def _pending_entry_path(staging_dir: Path, market: str, target_date: str) -> Path:
    return staging_dir / "_pending" / f"{market}_{target_date}.json"


def write_pending_manifest_entry(
    entry: dict[str, Any],
    *,
    staging_dir: Path = PIT_STAGING_DIR,
) -> Path:
    path = _pending_entry_path(staging_dir, entry["market"], entry["date"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def load_pending_manifest_entry(
    market: str,
    target_date: str,
    *,
    staging_dir: Path = PIT_STAGING_DIR,
) -> dict[str, Any] | None:
    path = _pending_entry_path(staging_dir, market, target_date)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def clear_pending_manifest_entry(
    market: str,
    target_date: str,
    *,
    staging_dir: Path = PIT_STAGING_DIR,
) -> None:
    path = _pending_entry_path(staging_dir, market, target_date)
    if path.exists():
        path.unlink()


def record_manifest_entry_after_push(entry: dict[str, Any]) -> None:
    """Upsert public manifest only after ten_bagger-pit push succeeded."""
    manifest = load_pit_manifest()
    manifest = upsert_manifest_entry(manifest, entry)
    write_pit_manifest(manifest)


def write_pit_manifest(manifest: dict[str, Any], path: Path | None = None) -> None:
    manifest_path = path or PIT_MANIFEST_PATH
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


@dataclass
class PitWriteResult:
    skipped: bool = False
    reason: str = ""
    manifest_entry: dict[str, Any] | None = None


def write_daily_pit_snapshots(
    target_date: str,
    market: str,
    collector: PitFundamentalsCollector,
    *,
    staging_dir: Path = PIT_STAGING_DIR,
) -> PitWriteResult:
    manifest = load_pit_manifest()
    existing = {
        _entry_key(e.get("date", ""), e.get("market", "")) for e in (manifest.get("entries") or [])
    }
    if _entry_key(target_date, market) in existing:
        logger.warning("PIT manifest already has %s %s; skip snapshot write", market, target_date)
        return PitWriteResult(skipped=True, reason="manifest_entry_exists")

    rows = sorted(collector.rows.values(), key=lambda r: r["symbol"])
    universe_payload = build_universe_snapshot(market, target_date)

    try:
        write_fundamentals_snapshot(rows, staging_dir, market, target_date, allow_existing=False)
        write_universe_snapshot(
            universe_payload, staging_dir, market, target_date, allow_existing=False
        )
    except PitSnapshotExistsError as exc:
        logger.warning("PIT snapshot write skipped: %s", exc)
        return PitWriteResult(skipped=True, reason="file_exists")

    entry = build_manifest_entry(market, target_date, staging_dir)
    write_pending_manifest_entry(entry, staging_dir=staging_dir)
    return PitWriteResult(skipped=False, manifest_entry=entry)


def _run_git_step(label: str, args: list[str]) -> None:
    try:
        subprocess.run(args, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        raise RuntimeError(f"{label} failed (exit {exc.returncode}): {stderr}") from exc


def _pit_clone_url(repo: str, token: str) -> str:
    return f"https://x-access-token:{token}@github.com/{repo}.git"


def _pit_work_dir(staging_dir: Path) -> Path:
    return staging_dir.parent / ".pit-repo-clone"


def push_staging_to_pit_repo(
    staging_dir: Path,
    *,
    token: str | None,
    repo: str = PIT_DATA_REPO,
    work_dir: Path | None = None,
) -> bool:
    """Push new snapshot files to private pit data repo.

    Returns True when the remote holds every staged path afterwards. A path that
    already exists remotely is left untouched (immutable), so a same-day rerun
    after an earlier successful push still converges (#178).
    """
    if not token:
        logger.warning("PIT_DATA_TOKEN not set; skipping push to %s", repo)
        return False

    if work_dir is None:
        work_dir = _pit_work_dir(staging_dir)
    if work_dir.exists():
        subprocess.run(["rm", "-rf", str(work_dir)], check=True)

    _run_git_step(
        "git clone",
        ["git", "clone", "--depth", "1", _pit_clone_url(repo, token), str(work_dir)],
    )

    copied = 0
    existing = 0
    for sub in ("fundamentals", "universe"):
        src_root = staging_dir / sub
        if not src_root.exists():
            continue
        for src in src_root.rglob("*"):
            if not src.is_file():
                continue
            rel = src.relative_to(staging_dir)
            dest = work_dir / rel
            if dest.exists():
                if dest.read_bytes() != src.read_bytes():
                    logger.warning("PIT remote file differs from staging; keeping remote: %s", rel)
                existing += 1
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(src.read_bytes())
            copied += 1

    if copied == 0:
        logger.info("No new PIT files to push (%d already on remote)", existing)
        return existing > 0

    bot_email = "41898282+github-actions[bot]@users.noreply.github.com"
    git_c = ["git", "-C", str(work_dir)]
    _run_git_step("git config email", [*git_c, "config", "user.email", bot_email])
    _run_git_step("git config name", [*git_c, "config", "user.name", "github-actions[bot]"])
    _run_git_step("git add", [*git_c, "add", "fundamentals", "universe"])
    _run_git_step(
        "git commit",
        [*git_c, "commit", "-m", f"chore(pit): snapshot files ({copied} new)"],
    )
    _run_git_step("git push", [*git_c, "push", "origin", "HEAD"])
    logger.info("Pushed %d PIT file(s) to %s", copied, repo)
    return True


def push_and_record_manifest(
    target_date: str,
    market: str,
    *,
    token: str | None,
    staging_dir: Path = PIT_STAGING_DIR,
) -> bool:
    """Push staging to pit repo; on success upsert content/pit/manifest.json.

    The entry is rebuilt from the pushed clone, so it describes the remote bytes
    even when an earlier run already stored different bytes for this date.
    """
    pending = load_pending_manifest_entry(market, target_date, staging_dir=staging_dir)
    if pending is None:
        logger.info("No pending PIT manifest entry for %s %s", market, target_date)
        return False
    if not token:
        logger.warning("PIT_DATA_TOKEN not set; manifest unchanged")
        return False
    work_dir = _pit_work_dir(staging_dir)
    try:
        pushed = push_staging_to_pit_repo(staging_dir, token=token, work_dir=work_dir)
        entry = build_manifest_entry(market, target_date, work_dir) if pushed else None
    except Exception as exc:
        logger.warning("PIT push failed; manifest unchanged: %s", exc)
        return False
    if entry is None:
        logger.warning("PIT remote has no snapshot files; manifest unchanged")
        return False
    record_manifest_entry_after_push(entry)
    clear_pending_manifest_entry(market, target_date, staging_dir=staging_dir)
    logger.info("PIT manifest updated for %s %s after successful push", market, target_date)
    return True


def main() -> int:
    import os

    from config import market_for_date

    token = os.environ.get("PIT_DATA_TOKEN")
    target = os.environ.get("PIT_TARGET_DATE")
    if not target:
        logger.warning("PIT_TARGET_DATE not set; skipping pit push/manifest")
        return 0
    market = market_for_date(target)
    try:
        push_and_record_manifest(target, market, token=token)
    except Exception as exc:
        logger.warning("PIT finalize failed (daily continues): %s", exc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
