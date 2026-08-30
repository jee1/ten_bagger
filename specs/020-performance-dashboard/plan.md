# Implementation Plan: Performance Dashboard Page

**Branch**: `020-performance-dashboard` | **Date**: 2026-08-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/020-performance-dashboard/spec.md`

## Summary

Issue #64 / Epic #74 Phase 0: add a bilingual public `/performance` page that
**reads** published `content/performance/{KR,US}.json` bundles, derives
display-only equal-weight cumulative series and horizon summaries (1M/3M/6M/1Y;
H20/H60 secondary), shows empty states and disclaimer, and links from primary
nav. No ledger regenerate changes, no Score weight changes, no source JSON
rewrites.

## Technical Context

**Language/Version**: TypeScript (Astro 7 site); Node ≥22.12
**Primary Dependencies**: Existing Astro + `@astrojs/check` + generated
`PerformanceBundle` types — **no new runtime chart/DB dependency**
**Storage**: Read-only Git JSON `content/performance/{KR|US}.json` (from #63);
optional absence → empty state
**Testing**: `node --test` (or `--experimental-strip-types --test`) for pure
aggregate helpers; `npm run check` (`gen:types:check` + `astro check`);
`npm run build` smoke with/without performance files
**Target Platform**: Static GitHub Pages (existing hosting)
**Project Type**: Public static pages within Astro + Git-as-DB monorepo
**Performance Goals**: Build-time load of two market bundles; page usable on
mobile; cumulative + four horizon cards render without interactive backend
**Constraints**: Display-only derivation (FR-010/023); Score freeze (FR-014);
PIT as-of per market (FR-020); fail-closed empty (FR-005/006/022); bilingual
(FR-007); escape content strings (FR-024); constitution I–V

## Constitution Check

*GATE: Must pass before proceeding. Re-check after design phase.*

### Pre-Design Gate

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Git-Content Source of Truth | PASS | Page consumes committed performance JSON; no runtime DB |
| II. Point-in-Time Measurement (No Look-Ahead) | PASS | Display published `asOfDate` per market; no new price fetch |
| III. Additive Performance Artifacts | PASS | Read-only; never mutates daily or performance source files |
| IV. Score Freeze Until Merge Gate | PASS | No scoring / generate_daily / weight changes |
| V. Schema Contracts and Validation Discipline | PASS | Reuse enforced `performance-bundle.schema.json` + generated types; no schema rewrite required for MVP |

### Post-Design Gate (after Phase 1)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Git-Content Source of Truth | PASS | `contracts/content-read.md` + research R1 lock read-only paths |
| II. Point-in-Time Measurement | PASS | View model carries per-market `asOfDate`; incomplete/bench gaps explicit |
| III. Additive Performance Artifacts | PASS | Aggregation is display-only (R2); writers remain #63 CLI only |
| IV. Score Freeze Until Merge Gate | PASS | Structure excludes `scripts/` scoring modules |
| V. Schema Contracts and Validation Discipline | PASS | Types from existing codegen; UI contract documents labels/states |

**Result**: All five PASS. Complexity Tracking empty.

## Project Structure

### Documentation (this feature)

```text
specs/020-performance-dashboard/
├── spec.md
├── plan.md              # This file
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   ├── content-read.md
│   └── page-ui.md
├── checklists/
└── tasks.md             # /speckit.superspec.tasks (not this command)
```

### Source Code (repository root)

```text
content/performance/{KR|US}.json   # INPUT (read-only; may be absent)

src/
├── pages/performance.astro        # NEW — ?lang=&market=
├── layouts/Layout.astro           # EXTEND — nav link “Performance”
├── components/
│   ├── Disclaimer.astro           # REUSE
│   ├── PerformanceSummary.astro   # NEW — cumulative + caveat
│   ├── HorizonCards.astro         # NEW — 1M/3M/6M/1Y (+ optional H20/H60)
│   └── PerformanceEmpty.astro     # NEW — empty / unavailable copy
└── lib/
    ├── i18n.ts                    # EXTEND — performance labels
    ├── content-types.generated.ts # REUSE (PerformanceBundle)
    ├── performanceLoad.ts         # NEW — safe load bundle or null
    └── performanceAggregate.ts    # NEW — equal-weight cumulative + horizon stats

# Optional fixture for empty/build smoke (do not commit fake returns as “live”):
# content/performance/ may stay absent in this worktree until regenerate
```

**Structure Decision**: Keep measurement writers in `scripts/` (#63). This
feature is Astro presentation + pure TS aggregation only. Match existing
`?lang=` query pattern; add `market=KR|US` (default KR). Prefer table +
accessible text (and optional inline SVG) over a chart library (YAGNI).

## Execution Strategy

### TDD Requirements

- [x] **`src/lib/performanceAggregate.ts`**: REQUIRED [TDD] — compounding,
  horizon means, incomplete-bench / zero-complete / survivorship caveat
  branches (many edge cases from brainstorm)
- [x] **`src/lib/performanceLoad.ts`**: REQUIRED [TDD] or thin wrapper with
  fixture tests — missing file → null; valid bundle → typed object
- [ ] **Astro pages/components**: OPTIONAL TDD — covered by `astro check` +
  manual/build smoke; keep presentational

### Parallel Execution Opportunities

- [x] i18n label strings + `Layout` nav link can proceed in parallel with
  aggregate helper implementation (no shared logic files)
- [x] `HorizonCards` vs `PerformanceSummary` markup after aggregate API stabilizes
- [ ] Do **not** parallelize aggregate API design with first consumer without a
  short contract freeze (see Review Gates)

### Human Checkpoints

1. After aggregate helper + tests green — confirm FR-015/021 numbers on a fixture
2. After first `/performance` render with real or fixture bundle — visual/i18n check
3. Before merge — `npm run check` + `npm run build`; confirm Score/daily untouched

### Review Gates

- [x] **Aggregate API + UI contract** (`contracts/page-ui.md`): [REVIEW] before
  polishing components
- [x] **Copy (disclaimer / non-fund / bench caveat)**: [REVIEW] bilingual strings
- [ ] Schema changes: not expected; if needed, escalate as separate concern

## Complexity Tracking

> No constitution violations. Empty.
