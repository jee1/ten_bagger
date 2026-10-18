# Point-in-Time Walk-Forward Assumptions

**Feature**: [#66](https://github.com/jee1/ten_bagger/issues/66) · **Spec**: `specs/022-walk-forward-harness/`  
**Authority**: Engineering (Epic #74 Performance Loop)

## Decision cut at `t`

At each OOS decision session `t`, screening uses only information knowable on or before `t`:

- Price history passed to scoring is filtered with `performance.pit_prices.filter_session_bars(bars, as_of_date=t)` before momentum/entry inputs. Offline folds use the default `as_of_session_closed=True`; live fetch infers closed vs open via market TZ regular close (not host `date.today()` — see #99).
- Fundamentals (`get_ticker_info`) in override re-screening come from the daily run's PIT snapshot for `t` (#175 stage 2, `walk_forward/fundamentals_pit.py`). Snapshots live in private `jee1/ten_bagger-pit`; set `PIT_DATA_DIR` to a local clone (default `scripts/pit-data/`). Each file is sha256-checked against `content/pit/manifest.json`; a missing or altered local file raises. Rows whose `knownAt` is after the end of `t` (KST) are dropped. The re-screen universe is the symbol set the daily run screened on `t`, so symbols that run excluded as recent picks cannot be selected. Per session: no snapshot → `fundamentals_not_pit:<count>`; usable rows below 95% → `fundamentals_low_coverage:<count>`. Either is a hard `contamination` failure in calibration GO/NO-GO. Reports carry `fundamentalsSnapshot: {from, to, sha256[]}`. **Ledger path** (committed `content/daily/` picks, no overrides) is not tagged. Backfilled daily runs (target date ≠ KST today) write no snapshot, since their info postdates `t`. New IS/OOS windows for override evidence must start on or after the first snapshot date S = 2026-10-09.
- Calibration run `9d8e0780dd115837` (Score v3 search, IS 2026-07-03..07-31 / OOS 2026-08-03..09-02) used override live re-screen with non-PIT fundamentals — classify that search as **exploratory-level evidence** only. **NO-GO overall verdict and `SCORE_VERSION=2` remain unchanged.**
- No bar, feature, or return observation dated after `t` may influence pick selection for that session.

## Horizons (ADR 0003)

| Horizon | Definition | Benchmark |
|---------|------------|-----------|
| H20 | 20 **trading sessions** after entry session | KR-KOSPI (KR) / US-SPX (US) |
| H60 | 60 trading sessions after entry | same |

Entry/exit price basis follows [ADR 0002](./adr/0002-forward-return-price-basis.md): entry at next session open after pick date; exit at horizon session close (adjusted preferred).

## Rolling vs anchored

**v1 implements rolling folds only** (`foldSpec.mode = "rolling"`):

- Each fold declares explicit `trainRange` and `oosRange` decision sessions.
- Train and OOS session sets are disjoint per fold.
- `stepSessions` advances the rolling window.

**Anchored mode is deferred** to a follow-up release. Semantics will be documented before implementation; no anchored CLI flag in v1.

## Distinction from the old snapshot comparator

| Tool | Purpose |
|------|---------|
| removed `backtest_screen.py` | Was a snapshot comparator, not PIT walk-forward |
| `walk_forward_cli.py` | PIT rolling OOS evaluation with a reproducible report |

Do not treat a snapshot comparator as walk-forward evidence (FR-031).

## Calendar & markets

- Decision sessions are weekdays whose market (`config.market_for_date`) is listed in run config `markets`.
- KR/US alternation follows odd/even calendar day rule in `config.market_for_date`.
- Partial windows (KR-only or US-only) evaluate only matching sessions.

## Duplicate pick ban

Symbols picked within the prior `DUPLICATE_BAN_DAYS` (30 calendar days) are excluded from subsequent screening in the same run, mirroring daily publication policy.

## Measurement sources

| `runIntent` | `measurementSource` | Behavior |
|-------------|---------------------|------|
| `go_evidence` | `ledger` (required) | Pick source = committed `content/daily/` (no live re-screen unless analysis overrides); returns from `content/performance/`. Missing rows fail with regenerate hint. Fold `complete` requires **H20** measurements complete; H60 may remain incomplete and is reported only (ADR 0003). |
| `exploratory` | `fixture-recompute` or `ledger` | Offline fixtures or ledger lookup; overrides use PIT re-screen |

## Artifacts

Walk-forward reports write to `content/walk-forward/{runId}.json` only. **No writes to `content/daily/`** (SC-006).

## Forward fundamentals & universe snapshots (issue #175 stage 1)

Daily production runs capture immutable point-in-time inputs without extra yfinance calls:

| Artifact | Private data repo (`jee1/ten_bagger-pit`) | Public manifest (`content/pit/manifest.json`) |
|----------|-------------------------------------------|-----------------------------------------------|
| Fundamentals | `fundamentals/{market}/{YYYY-MM-DD}.jsonl.gz` | `sha256`, `bytes`, `rowCount`, `knownAtMin`/`knownAtMax` |
| Universe | `universe/{market}/{YYYY-MM-DD}.json.gz` | `sha256`, `bytes`, `symbolCount`, `builtAt` |

- **Target date** matches `generate_daily.py` KST session date (`YYYY-MM-DD`).
- **Fundamentals row**: `symbol`, `market`, `knownAt`, `provider`, `cacheHit`, plus scoring `info` fields only (same set as `scripts/pit_snapshot.SCORING_INFO_FIELDS`; `longBusinessSummary` excluded).
- **`knownAt`**: timestamp of the yfinance info fetch stored in disk cache (`fetchedAt`). TTL cache hits and stale fallbacks use the cached fetch time, not the daily job clock.
- **Universe**: full screening symbol list from `scripts/universe/{kr,us}.json` plus `builtAt` (universe file mtime).
- **Immutability**: existing `date`+`market` files are never overwritten (skip + warning). Manifest `sha256` must match gzip bytes (`pit_snapshot.verify_file_sha256` / `verify_manifest_entry_files`).
- **Stage 2** will patch `get_ticker_info` to read these snapshots for walk-forward re-screening; until then live daily screening behavior is unchanged aside from capture.

## Frozen post-S carve

`scripts/calibration/configs/score-v3-search-go-evidence-pit-post-s.json` freezes the #175 stage 3 go_evidence search carve. In-sample decision sessions run from 2026-10-09 through 2026-11-06. Out-of-sample decision sessions run from 2026-11-09 through 2026-12-09. The measurement date is 2027-01-10, about 20 trading sessions after the out-of-sample end, so H20 returns can mature. Both windows start on 2026-10-09 or later. Run the config only when readiness finds at least 20 H20-complete pick days in each window. Do not retune the weights and then score this same window again.
