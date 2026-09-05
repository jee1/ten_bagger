# Implementation Plan: Product Top-N Candidates + Score Breakdown Archive

**Branch**: `feature/product-top-n` | **Date**: 2026-09-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/028-product-top-n/spec.md` (Issue #72 / Epic #74 Phase 4)

## Summary

Keep the daily one-pick rule, but persist an optional additive `topCandidates`
(N=5) on each new daily JSON with identity + composite + axis scores. Change
screening to retain **all eligible scored** results (not only above-threshold),
select the published pick as the first result with `composite >= threshold`,
and attach Top-N for both `pick` and `no_pick` when any scored candidates exist.
Sync schema + types; expand UI on the day page only (`DailyCard`); archive list
unchanged. No Score weight/threshold/version live changes. No historical
backfill.

## Technical Context

**Language/Version**: Python 3.11+ (`scripts/`); TypeScript + Astro 7 (`src/`)
**Primary Dependencies**: Existing jsonschema content validation, `gen:types`
codegen, Astro components — **no new runtime deps**
**Storage**: Additive optional field on `content/daily/*.json` (Git-as-DB)
**Testing**: `npm run test:python` (pytest); `npm run validate:content`;
`npm run gen:types` / `gen:types:check`; `npm run check`; optional `astro build`
**Target Platform**: Static GitHub Pages + GH Actions daily generate
**Project Type**: Content schema + screening pipeline + public day UI
**Performance Goals**: Negligible JSON growth (≤5 candidates); UI expand below
fold; screening already scores full universe — keep all scored in memory for
sort/slice only
**Constraints**: Constitution I–V; FR-018 Score freeze; N=5; omit field if zero
eligible; archive list chrome unchanged; no #73 RSS

## Constitution Check

### Pre-Design Gate

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Git-Content Source of Truth | PASS | Top-N lives in committed daily JSON; no runtime DB |
| II. Point-in-Time Measurement | PASS | No new forward-return / look-ahead; ranking uses same session screen |
| III. Additive Performance Artifacts | PASS | Daily field is additive/optional; does not rewrite ledger/performance |
| IV. Score Freeze Until Merge Gate | PASS | No WEIGHT_*/COMPOSITE_THRESHOLD/SCORE_VERSION changes |
| V. Schema Contracts and Validation Discipline | PASS | Extend `daily-entry.schema.json` + `gen:types` + semantic checks |

### Post-Design Gate (after Phase 1)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Git-Content Source of Truth | PASS | `contracts/daily-top-n.md` locks field on daily document |
| II. Point-in-Time Measurement | PASS | No PIT surface change; walk-forward pick via `select_pick` helper |
| III. Additive Performance Artifacts | PASS | Historical dailies omit field; no backfill required |
| IV. Score Freeze Until Merge Gate | PASS | Structure excludes weight/threshold edits |
| V. Schema Contracts and Validation Discipline | PASS | Schema + semantic validate + types + UI contract |

**Result**: All PASS. Complexity Tracking empty.

## Project Structure

### Documentation (this feature)

```text
specs/028-product-top-n/
├── spec.md
├── plan.md              # this file
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   ├── daily-top-n.md
│   └── page-ui.md
├── checklists/requirements.md
├── progress.yml
└── tasks.md             # /speckit.superspec.tasks
```

### Source Code (repository root)

```text
scripts/
├── config.py                 # TOP_N = 5 (optional constant)
├── schema/daily-entry.schema.json   # + topCandidates
├── screening/core.py         # keep all scored; stable sort
├── generate_daily.py         # select_pick + attach topCandidates
├── validate_content.py       # semantic Top-N rules
├── walk_forward/pit_screen.py  # use select_pick (threshold filter)
├── backtest_screen.py        # document / filter top if needed
└── tests/
    ├── test_screen_top_n.py          # NEW or extend screen tests
    ├── test_generate_daily.py        # Top-N on pick/no_pick
    └── test_validate_top_candidates.py  # NEW semantic validation

src/
├── lib/types.ts              # TopNCandidate + DailyEntry.topCandidates?
├── lib/content-types.generated.ts  # via gen:types
├── lib/i18n.ts               # Top-N framing labels
└── components/DailyCard.astro      # <details> expand; no archive change

content/daily/*.json          # forward-only new writes; no mandatory rewrite
```

**Structure Decision**: Prefer small helpers (`select_pick`, `build_top_candidates`)
in `generate_daily.py` (or tiny `top_n.py` if tests want isolation) over new
subsystem. Schema-first, then pipeline, then UI. Archive page untouched (FR-011).

## Execution Strategy

### TDD Requirements

- [x] Screening sort + return all scored; pick selection still threshold-gated
- [x] `build_top_candidates` / generate_daily pick & no_pick attachment + omit-if-empty
- [x] Semantic validation: unique symbols, ranks 1..k contiguous, len≤5, pick≡rank1
- [x] Schema rejects malformed candidate objects (jsonschema)

### Parallel Execution Opportunities

- [x] After schema+types green: UI (`DailyCard` + i18n) ∥ pipeline tests (different files)
- [x] Docs/contracts already in this plan; no ADR required for v1

### Human Checkpoints

Canonical Speckit memory: auto-advance phase gates during execute if user
authorized; **no commit/push unless asked**. Pause before execute until user
says go (this plan command stops after design artifacts).

### Review Gates

- [x] Schema/data-model before UI consumers
- [x] Final `/speckit.superspec.review` vs FR/SC

## Complexity Tracking

None.
