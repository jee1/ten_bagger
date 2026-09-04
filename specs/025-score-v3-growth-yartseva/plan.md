# Implementation Plan: Score v3 Growth Weight Reallocation (Yartseva)

**Branch**: `feature/score-v3-growth-yartseva` | **Date**: 2026-09-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/025-score-v3-growth-yartseva/spec.md`
**Related**: Issue #69; Epic #74 Phase 2; ADR 0004; constitution v1.2.0;
`023-threshold-weight-go-no-go`; `022-walk-forward-harness`; `024-investment-dummy`

> **For agentic workers:** Prefer `/speckit.superspec.tasks` then
> `/speckit.superspec.execute` (TDD + subagents). Do **not** change live
> `WEIGHT_*`, `COMPOSITE_THRESHOLD`, or `SCORE_VERSION` in this feature’s
> mergeable analysis PR. Measurement-gated until ADR 0004 GO + explicit
> config PR (`SCORE_VERSION=3` + approved weights).

## Summary

Deliver an Issue #69 **growth-shrink candidate package** on top of existing
#67 calibration + #66 walk-forward tooling: (1) committed default grid of four
named candidates that reduce `WEIGHT_GROWTH` and redistribute to
Valuation/Quality/Size, (2) hard validation (growth &lt; live 0.20, floor ≥0.05,
no Entry/Momentum redistribution, sum `1.0±1e-6`), (3) **side-by-side** live
baseline OOS comparison in one calibration report via
`compareToLiveBaseline`, (4) freeze tests + Methodology gated-candidate copy.
No live Score merge in this delivery.

## Technical Context

**Language/Version**: Python 3.11+ (`scripts/`); Astro Methodology only
**Primary Dependencies**: Existing `calibration/*`, `walk_forward/*`, pytest,
`config.py` live constants (read-only)
**Storage**: Additive calibration JSON under existing calibration output paths;
fixtures under `scripts/tests/fixtures/calibration/`; **no** `content/daily`
rewrite
**Testing**: `npm run test:python` — new `test_growth_yartseva_*.py` + fixture
config; offline, no network
**Target Platform**: Maintainer CLI / CI
**Project Type**: Calibration study config + validation module + Methodology
**Performance Goals**: Same as #67 (≤10 candidates; fixture smoke)
**Constraints**: Constitution IV freeze; reuse #67/#66 contracts; Growth floor
0.05; Entry/Momentum redistribution forbidden on default grid; orthogonal to
#68 investment-dummy

## Constitution Check

*GATE: Must pass before proceeding. Re-checked after design — all PASS.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Git-Content Source of Truth | PASS | No runtime DB; daily JSON untouched |
| II. Point-in-Time Measurement | PASS | Reuses #66 PIT folds; no new look-ahead path |
| III. Additive Performance Artifacts | PASS | Calibration reports additive; no daily rewrite |
| IV. Score Freeze Until Merge Gate | PASS | Analysis-only; live `WEIGHT_*` / `SCORE_VERSION` frozen; GO hint requires explicit PR |
| V. Schema Contracts and Validation | PASS | Extend calibration config schema only if `compareToLiveBaseline` added; `test:python` + validate |

## Project Structure

### Documentation (this feature)

```text
specs/025-score-v3-growth-yartseva/
├── spec.md
├── plan.md              # this file
├── tasks.md
└── progress.yml
```

### Source Code (repository root)

```text
scripts/
├── config.py                      # UNCHANGED live WEIGHT_* / SCORE_VERSION
├── calibration/
│   ├── growth_yartseva.py         # NEW: default grid + Issue #69 validators
│   ├── candidates.py              # optional hook: call growth validators when profile set
│   ├── config.py                  # ADD optional compareToLiveBaseline: bool
│   ├── runner.py                  # ADD baseline OOS row when compareToLiveBaseline
│   ├── report.py                  # optional: note compareToLiveBaseline in report
│   └── configs/
│       └── growth-yartseva-issue69.json   # NEW committed search grid
├── schema/                        # UPDATE calibration config schema if needed
└── tests/
    ├── test_growth_yartseva_grid.py       # NEW [TDD]
    ├── test_growth_yartseva_baseline_compare.py  # NEW [TDD]
    ├── test_growth_yartseva_freeze.py     # NEW live freeze snapshot
    └── fixtures/calibration/
        └── growth-yartseva-smoke-config.json
src/pages/
└── methodology.astro              # ADD growth-weight reallocation gated candidate (KR/EN)
docs/architecture/
└── threshold-weight-merge-criteria.md  # SHORT addendum: #69 SCORE_VERSION=3 on GO
```

**Structure Decision**: Prefer a **thin** `growth_yartseva.py` module owning the
Issue #69 grid constants and validators; wire baseline comparison through one
boolean on the existing calibration config rather than a parallel CLI.

## Execution Strategy

| Concern | Approach |
|---------|----------|
| TDD | Grid validation, baseline-compare report shape, freeze tests |
| Parallel `[P]` | Methodology copy ∥ freeze test ∥ grid module after foundational schema |
| Subagents | US1 grid+tests; US2 runner baseline compare; US3 Methodology+docs |
| Human checkpoint | User pre-approved auto-advance all phases for this pipeline |
| Live config | Never edit live weights/version in execute; only GO hint text |

## Complexity Tracking

| Simplification | Why acceptable | Upgrade path |
|----------------|----------------|--------------|
| No new CLI command | Reuse `calibrate` + committed JSON config | Add `npm run calibrate:growth` wrapper later |
| `compareToLiveBaseline` boolean only | Spec needs side-by-side in one report | Richer multi-baseline later if needed |
| No full live ledger OOS in CI | Fixture smoke proves wiring; real GO is maintainer run | Document offline GO procedure in quickstart comment / Methodology |

## Research Notes

- Live weights confirmed in `scripts/config.py`: V 0.25, G 0.20, Q 0.20, S 0.15, E/M 0.10.
- #67 already validates weight sum and ≤10 candidates.
- Methodology already has a Score v3 candidates section (#68); extend it for #69 growth reallocation.
- GO path already prints PR hint; extend message for growth study to mention `SCORE_VERSION=3`.
