# Implementation Plan: Point-in-Time Walk-Forward Harness

**Branch**: `feature/performance-point-in-time-walk-forward-harness` | **Date**: 2026-09-01 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/022-walk-forward-harness/spec.md`

## Summary

Build an offline Python CLI that evaluates frozen screening candidates with **rolling walk-forward folds**, enforces **point-in-time (no look-ahead)** selection at each decision date `t`, and emits a **deterministic JSON OOS report** (`runIntent`, `measurementSource`, H20/H60 vs KR-KOSPI/US-SPX, coverage flags). `go_evidence` runs consume **#63 ledger facts**; smoke/dev may use **fixture-recompute** only. Anchored mode is documented and deferred.

## Technical Context

**Language/Version**: Python 3.11+ (existing `scripts/` stack)
**Primary Dependencies**: pytest, jsonschema, pandas (via performance/), existing `screening/`, `performance/`, `scoring/`
**Storage**: Git JSON — `content/walk-forward/*.json` (additive); reads `content/ledger/`, `content/performance/`
**Testing**: pytest (`npm run test:python`); dedicated smoke (`npm run walk-forward:smoke`)
**Target Platform**: Linux/macOS CLI (maintainer/reviewer workflows)
**Project Type**: Python CLI + JSON schema contracts (Astro site unchanged)
**Performance Goals**: v1 single-threaded; ≤5 candidates; ≤3yr smoke calendar (FR-032)
**Constraints**: No live broker; no Optuna; no Score v2 live changes; rolling-only runnable; canonical JSON determinism

## Constitution Check

*GATE: Must pass before proceeding. Re-checked after design — all PASS.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Git-Content Source of Truth | PASS | Reports under `content/walk-forward/`; no runtime DB; daily picks untouched |
| II. Point-in-Time Measurement | PASS | PIT provider at fold `t`; ledger/ADR 0002 for outcomes; smoke catches contamination |
| III. Additive Performance Artifacts | PASS | New schema + directory; ledger-first for GO; no pick rewrite |
| IV. Score Freeze Until Merge Gate | PASS | Analysis-only candidates; frozen v2 baseline + manual grid max 4 |
| V. Schema Contracts and Validation | PASS | `walk-forward-report.schema.json`; validate:content + gen:types registration |

## Project Structure

### Documentation (this feature)

```text
specs/022-walk-forward-harness/
├── spec.md
├── plan.md              # this file
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── walk-forward-report.schema.json
│   └── cli-contract.md
└── tasks.md
```

### Source Code (repository root)

```text
scripts/
├── walk_forward.py                 # CLI entry
├── walk_forward/
│   ├── __init__.py
│   ├── config.py                   # RunConfig, validation, config hash
│   ├── folds.py                    # Rolling fold calendar generation
│   ├── pit_screen.py               # PIT-wrapped screening at t
│   ├── ledger_loader.py            # Load ledger/performance facts
│   ├── aggregate.py                # Hit-rate, excess return, coverage
│   └── report.py                   # Report builder + canonical JSON
├── schema/
│   └── walk-forward-report.schema.json  # copy/sync from spec contracts
├── tests/
│   ├── test_walk_forward.py
│   ├── test_walk_forward_smoke.py
│   └── fixtures/walk_forward/
docs/architecture/
└── pit-walk-forward-assumptions.md
```

**Structure Decision**: New `walk_forward/` package parallel to `performance/` keeps fold/report logic isolated. CLI at `scripts/walk_forward.py` matches `regenerate_ledger.py` / `backtest_screen.py`. Schema lives in `scripts/schema/` as source of truth; spec `contracts/` is design reference (keep in sync on implementation).

## Execution Strategy

### TDD Requirements

- [x] **`walk_forward/folds.py`**: Fold calendar edge cases (min 2 folds, train/OOS disjoint dates)
- [x] **`walk_forward/aggregate.py`**: Metrics math (no_pick exclusion, insufficient_coverage, H20/H60)
- [x] **`walk_forward/report.py`**: Canonical JSON determinism
- [x] **`walk_forward/pit_screen.py`**: Contamination fixture proves no post-`t` data used
- [x] **Smoke suite**: End-to-end offline path + look-ahead rejection

### Parallel Execution Opportunities

- [x] Schema registration (`validate_content.py`, `gen_types.mjs`, `config.py` paths) parallel to package scaffold
- [x] PIT docs (`pit-walk-forward-assumptions.md`) parallel after fold/report interfaces stable
- [x] Fixture files parallel to unit tests

### Human Checkpoints

1. After Phase 2 (foundational) — verify fold calendar + schema validate on sample JSON
2. After US1+US2 — PIT fold run + report artifact on fixtures
3. After US5 smoke — CI smoke green offline
4. Before merge — full `npm run test:python` + `validate:content`

### Review Gates

- [x] **Report schema + CLI contract**: Review before aggregate/report consumers
- [x] **PIT screening provider**: Review before fold integration (look-ahead surface)
- [x] **Ledger loader**: Review before `go_evidence` path

## Complexity Tracking

> No constitution violations requiring justification.

## Phase 0 Output

See [research.md](./research.md) — all technical unknowns resolved.

## Phase 1 Output

- [data-model.md](./data-model.md)
- [contracts/](./contracts/)
- [quickstart.md](./quickstart.md)

## Post-Design Constitution Re-check

All principles remain PASS. Design adds only additive artifacts and reuses existing measurement/screening modules with explicit PIT boundaries.
