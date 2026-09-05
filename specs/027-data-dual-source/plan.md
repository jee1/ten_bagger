# Implementation Plan: Data dual-source (prices / Stooq)

**Branch**: `027-data-dual-source` | **Date**: 2026-09-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/027-data-dual-source/spec.md` (Issue #71)

## Summary

Document ADR 0005 for dual-source posture; extend `get_ticker_history` cascade
to `yfinance → retry → stale yf cache → Stooq → raise` with provider-keyed
cache and offline pytest coverage. Fundamentals/`get_ticker_info` unchanged
except docs. KR DART deferred in ADR. No Score freeze break.

## Technical Context

**Language/Version**: Python 3.11+ (existing `scripts/`); Markdown ADRs
**Primary Dependencies**: Existing `yfinance`, `pandas`; Stooq via stdlib
`urllib` CSV (no new paid deps)
**Storage**: Disk cache under existing `CACHE_DIR` with provider-keyed names
**Testing**: `npm run test:python` (pytest); offline mocks only for CI
**Target Platform**: Local + GitHub Actions daily / regenerate jobs
**Project Type**: Data-fetch resilience inside Astro+Python monorepo
**Performance Goals**: Secondary only on primary miss; no extra Stooq calls on
fresh yfinance hit
**Constraints**: Constitution I–V; FR-006 Score freeze; no secrets for Stooq;
FR-008 no paid vendor migration

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Git-Content Source of Truth | PASS | No content JSON semantics change |
| II. Point-in-Time Measurement | PASS | Price secondary still session bars; ADR 0002 caveats in 0005 |
| III. Additive Performance Artifacts | PASS | Cache only; no ledger rewrite |
| IV. Score Freeze Until Merge Gate | PASS | No WEIGHT_*/THRESHOLD/SCORE_VERSION |
| V. Schema Contracts | PASS | No schema/codegen |

**Result**: All PASS.

## Project Structure

### Documentation

```text
specs/027-data-dual-source/
├── spec.md
├── plan.md          # this file
├── research.md
├── tasks.md
├── progress.yml
└── checklist-review.md
docs/architecture/
├── README.md        # link ADR 0005
└── adr/0005-data-dual-source.md
```

### Source

```text
scripts/
├── yf_cache.py          # cascade into Stooq after stale miss
├── stooq_prices.py      # NEW: symbol map + CSV fetch + normalize OHLCV
└── tests/
    ├── test_yf_cache.py     # extend cascade tests
    └── test_stooq_prices.py # NEW: mapper + parse + offline
```

**Structure Decision**: Thin Stooq module; wire only in `get_ticker_history`.
Keep `get_ticker_info` path untouched (FR-013).

## Execution Strategy

### TDD Requirements

- [x] Stooq CSV parse + symbol mapping
- [x] History cascade: secondary success / all-miss raise / empty primary = miss
- [x] Stale-before-secondary order preserved (#38)

### Parallel Execution Opportunities

- [x] ADR/README docs stream ∥ Stooq adapter + tests (different files)
- [x] After adapter green: architecture index link + ADR 0003 follow-up note

### Human Checkpoints

Canonical Speckit: auto-advance phase gates; no commit/push unless asked.

## Complexity Tracking

None.
