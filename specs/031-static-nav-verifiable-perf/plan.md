# Implementation Plan: Fix Static Navigation and Publish Verifiable Performance

**Branch**: `feature/fix-static-navigation-and-publish-verifiable-per` (SPECIFY_FEATURE=`031-static-nav-verifiable-perf`) | **Date**: 2026-09-06 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/031-static-nav-verifiable-perf/spec.md` (Issue #94)

## Summary

Restore reliable static-site navigation for language, archive month, and
performance market (query-driven controls currently bake at build time), ensure
ledger/performance commits deploy to GitHub Pages, and make performance
presentation honest about price-basis validation and aggregate labeling.

**Approach**: Keep existing `?lang=` / `?year=&month=` / `?market=` URL contract.
Embed all needed variants at build time; apply selection with a small client
script after load. Extend `ledger.yml` with Pages deploy. Surface
`runMeta.priceAdjustment` + incomplete validation for `002780.KS`. Relabel
cumulative series as modeled per-pick chain (not multi-position portfolio). Fix
archive calendar CSS at 390px.

## Technical Context

**Language/Version**: TypeScript (Astro 5 site), Python 3.12 (ledger scripts), YAML workflows
**Primary Dependencies**: Astro static site, existing `performanceLoad` /
`performanceAggregate`, GitHub Actions `deploy-pages`
**Storage**: Git JSON under `content/performance/`, `content/ledger/`
**Testing**: Node assert tests / existing site tests; pytest for ledger (unchanged
unless validation helper added); manual static-build smoke for query hydrate
**Target Platform**: GitHub Pages (`base: /ten_bagger/`)
**Project Type**: Static content site + CI
**Performance Goals**: Client hydrate applies lang/month/market without full
reload; no layout overflow at 390px archive
**Constraints**: `output: 'static'`; no Score live changes; no Top-N/RSS rebuild;
no commit/push unless asked

## Constitution Check

*GATE: Must pass before proceeding. Re-check after design phase.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Git-Content Source of Truth | PASS | Still git JSON → static build → Pages; ledger deploy closes publish gap |
| II. Point-in-Time Measurement (No Look-Ahead) | PASS | Surfaces priceAdjustment honesty; no look-ahead change |
| III. Additive Performance Artifacts | PASS | No rewrite of daily pick semantics; additive UI/docs only |
| IV. Score Freeze Until Merge Gate | PASS | Explicitly out of scope (FR-011) |
| V. Schema Contracts and Validation Discipline | PASS | Reuses existing performance schema; may add docs + UI fields only |

## Project Structure

### Documentation (this feature)

```text
specs/031-static-nav-verifiable-perf/
├── spec.md
├── plan.md              # This file
├── research.md
├── data-model.md
├── quickstart.md
├── tasks.md
├── progress.yml
└── checklists/
```

### Source Code (repository root)

```text
src/pages/*.astro              # embed variant data; mount hydrate
src/layouts/Layout.astro       # lang toggle + hydrate hook
src/components/Calendar.astro  # month links; overflow-safe markup
src/components/Performance*.astro
src/lib/performanceAggregate.ts  # labeling helpers / runMeta passthrough
src/lib/staticNav.ts             # NEW: parse query + apply view helpers
src/styles/global.css            # calendar 390px fix
docs/architecture/ or docs/      # price-basis validation note (incomplete→complete)
.github/workflows/ledger.yml     # Pages deploy after content push
.github/workflows/daily.yml      # reference for deploy steps (reuse)
```

**Structure Decision**: Prefer thin client hydrate over new `[lang]` route tree to
preserve bookmarks (Q1–Q2). Deploy fix is workflow-only (Q3).

## Execution Strategy

### TDD Requirements

- [x] `staticNav` query parsing / view selection helpers: pure functions — [TDD]
- [x] `performanceAggregate` / view model: runMeta + labeling fields — [TDD]
- [ ] Astro markup / CSS: smoke via build + checklist (optional unit)

### Parallel Execution Opportunities

- [x] US1 static nav hydrate (pages/layout/css) ∥ US2 ledger Pages deploy (workflow)
- [x] US3 price-basis docs+UI labeling can follow after view model exposes runMeta

### Phase Checkpoints

- [ ] After Foundational: hydrate helper tests green
- [ ] After US1: static `astro build` + file:// or preview proves lang/month switch
- [ ] After US2: ledger workflow contains deploy job (YAML review)
- [ ] After US3: UI shows priceAdjustment + incomplete validation; aggregate copy updated
- [ ] Before review: SC checklist + constitution re-check

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Client hydrate instead of path routes | Preserves production query bookmarks; smaller diff | Full `/en/...` route tree is larger migration + breaks bookmarks without redirects |

## Phase 0 / Phase 1 artifacts

See `research.md`, `data-model.md`, `quickstart.md` in this directory.
