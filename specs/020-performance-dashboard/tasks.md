# Tasks: Performance Dashboard Page

**Input**: Design documents from `specs/020-performance-dashboard/`  
**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [data-model.md](./data-model.md), [research.md](./research.md), [contracts/](./contracts/)  
**Constitution**: `.specify/memory/constitution.md` (I–V) — Score freeze; read-only performance JSON; no daily rewrite

> **For agentic workers:** Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans`. Checkboxes track progress. TDD tasks: RED → GREEN → REFACTOR.

**Goal:** Bilingual public `/performance` page showing hypothetical pick portfolio vs market bench from published `#63` bundles (#64).

**Architecture:** Astro page + pure TS load/aggregate helpers; table (+ optional SVG); no new chart/DB deps; display-only derivation.

**Tech stack:** Astro 7, TypeScript, Node ≥22.12, existing `PerformanceBundle` types, `node --experimental-strip-types --test`.

**Spec:** [spec.md](./spec.md)

**Global constraints (every task):**
- Do not modify Score v2 weights, `generate_daily`, or `content/daily/*.json` semantics
- Do not write/update/delete `content/ledger/**` or `content/performance/**` from UI/build
- No new runtime chart libraries or databases
- Escape content-derived strings (symbols, etc.)
- Preserve site disclaimer; no fund/ETF implication
- KR and US never blended

## Task Format

```
[ID] [markers] [Story] Description
```

**Markers**: `[P]` parallel · `[TDD]` RED-GREEN-REFACTOR · `[REVIEW]` human gate · `[SUBAGENT]` subagent-ok  
**Stories**: `[US1]` cumulative vs bench · `[US2]` horizon cards · `[US3]` empty/thin · `[US4]` i18n · `[US5]` nav

## File map

| Path | Role |
|------|------|
| `src/lib/performanceLoad.ts` | Read `content/performance/{KR\|US}.json` → bundle \| null |
| `src/lib/performanceAggregate.ts` | Bundle → `MarketPerformanceView` (R2/R3) |
| `src/lib/performanceAggregate.test.ts` | Node test runner fixtures |
| `src/lib/performanceLoad.test.ts` | Missing/valid load cases |
| `src/lib/i18n.ts` | Performance labels (ko/en) |
| `src/pages/performance.astro` | `?lang=&market=` page |
| `src/components/PerformanceSummary.astro` | Cumulative + caveats + table/SVG |
| `src/components/HorizonCards.astro` | 1M/3M/6M/1Y + secondary H20/H60 |
| `src/components/PerformanceEmpty.astro` | Empty / unavailable |
| `src/layouts/Layout.astro` | Nav link |
| `package.json` | `test:performance-ui` script |

## Locked interfaces (implementers)

```typescript
// src/lib/performanceLoad.ts
import type { PerformanceBundle } from './content-types.generated';
export type Market = 'KR' | 'US';
export function loadPerformanceBundle(market: Market): PerformanceBundle | null;

// src/lib/performanceAggregate.ts
import type { HorizonId, PerformanceBundle, SurvivorshipFlag } from './content-types.generated';

export type HorizonTier = 'presentation' | 'secondary';

export interface CumulativePoint {
  pickDate: string;
  symbol: string;
  portfolioCumulative: number;
  benchmarkCumulative: number | null;
  pickReturn: number;
  benchmarkReturn: number | null;
  survivorshipFlag: SurvivorshipFlag;
}

export interface CumulativeSeries {
  horizonId: HorizonId;
  points: CumulativePoint[];
  finalPortfolioReturn: number | null;
  finalBenchmarkReturn: number | null;
  excessClaimAllowed: boolean;
}

export interface HorizonSummary {
  horizonId: HorizonId;
  tier: HorizonTier;
  available: boolean;
  nComplete: number;
  avgPickReturn: number | null;
  avgBenchReturn: number | null;
  excessClaimAllowed: boolean;
  survivorshipCaveat: boolean;
}

export interface MarketPerformanceView {
  market: Market;
  asOfDate: string | null;
  empty: boolean;
  pageEmpty: boolean;
  cumulative: CumulativeSeries | null;
  horizons: HorizonSummary[];
  hasSurvivorshipCaveat: boolean;
  benchmarkGapCount: number;
}

export function aggregateMarket(bundle: PerformanceBundle | null, market: Market): MarketPerformanceView;
```

Aggregation rules: [research.md](./research.md) R2–R3 · view fields: [data-model.md](./data-model.md)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Test script + fixture dir — no UI logic yet

- [x] T001 Add npm script `test:performance-ui` → `node --experimental-strip-types --test src/lib/performanceAggregate.test.ts src/lib/performanceLoad.test.ts` in `package.json`
- [x] T002 [P] Create `src/lib/fixtures/performance/` with minimal valid `KR.sample.json` / `US.sample.json` **for tests only** (do not treat as live SoT; do not commit fake “production” under `content/performance/` unless regenerate produced them)

**Execution notes**: No TDD. Confirm script runs (may fail until tests exist — exit non-zero OK until T005/T007).

**Checkpoint**: Script + fixture paths exist. Proceed to Foundational.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Load + aggregate API — **BLOCKS** all user stories

**CRITICAL**: No Astro page work until T008 review passes.

- [x] T003 [P] [TDD] [SUBAGENT] RED: `src/lib/performanceLoad.test.ts` — missing file → `null`; valid sample → typed bundle with expected `market`/`asOfDate`
- [x] T004 [TDD] Implement `src/lib/performanceLoad.ts` until T003 green (path resolve from repo `content/performance/{market}.json`; never write)
- [x] T005 [P] [TDD] [SUBAGENT] RED: `src/lib/performanceAggregate.test.ts` — empty/null → `pageEmpty`; equal-weight H20 cumulative compound; incomplete bench → `excessClaimAllowed=false` + gap count; presentation horizon means; H20/H60 `tier=secondary`
- [x] T006 [TDD] Implement `src/lib/performanceAggregate.ts` (`aggregateMarket`) per locked interfaces + research R2/R3 until T005 green
- [x] T007 Run `npm run test:performance-ui` — all green; fix any flake
- [x] T008 [REVIEW] Aggregate + load API freeze — human confirms FR-015/021 numbers on fixture before components consume API

**Execution notes**: T003∥T005 as subagents (different test files). T004 after T003 RED. T006 after T005 RED. Pause at T008.

**Checkpoint**: Unit tests green. Human approval before Phase 3.

---

## Phase 3: User Story 1 — Cumulative portfolio vs market (Priority: P1) MVP

**Goal**: Visitor sees hypothetical cumulative portfolio vs bench for one market with as-of, caveats, disclaimer, non-visual table  
**Independent Test**: With sample/live KR bundle, open `/performance?lang=ko&market=KR` — cumulative + bench + disclaimer + table

### Implementation for User Story 1

- [x] T009 [P] [SUBAGENT] [US1] Add i18n keys needed for US1 in `src/lib/i18n.ts` (performance title, cumulative heading, as-of, hypothetical/non-fund, index proxy note, benchmark unavailable) — ko+en
- [x] T010 [US1] Create `src/components/PerformanceSummary.astro` — cumulative finals, chart-adjacent notes, **table** of points (FR-026), optional SVG polyline; escape `symbol`
- [x] T011 [US1] Create `src/pages/performance.astro` — parse `lang`/`market` (defaults ko/KR); `loadPerformanceBundle` → `aggregateMarket`; render Summary when not `pageEmpty`; include `Disclaimer`
- [x] T012 [US1] Market switcher links on page preserving `lang` (KR/US separate — FR-012)
- [x] T013 [US1] [REVIEW] Visual/i18n smoke for cumulative block + SC-002/006/008

**Checkpoint**: US1 demonstrable without horizon cards. Human approval before US2.

---

## Phase 4: User Story 2 — Horizon summaries (Priority: P1)

**Goal**: 1M/3M/6M/1Y cards with unavailable states; H20/H60 secondary below  
**Independent Test**: Same page shows four presentation slots + demoted secondary when data exists

### Implementation for User Story 2

- [x] T014 [P] [SUBAGENT] [US2] Extend `src/lib/i18n.ts` with horizon labels + unavailable horizon copy (ko/en)
- [x] T015 [US2] Create `src/components/HorizonCards.astro` — render `horizons` filtered/ordered: presentation first, then secondary; no silent omit of required ids when bundle present
- [x] T016 [US2] Wire `HorizonCards` into `performance.astro` below Summary
- [x] T017 [US2] Verify unavailable card when `nComplete===0` (no fabricated 0% return claim)

**Checkpoint**: US1+US2 together. Proceed to US3 (can be same session if green).

---

## Phase 5: User Story 3 — Empty and thin-data states (Priority: P2)

**Goal**: Fail-closed empty when bundle missing/empty; site still builds; other market OK  
**Independent Test**: Remove/rename performance files → empty state; `npm run build` succeeds; other market with data still works

### Implementation for User Story 3

- [x] T018 [P] [SUBAGENT] [US3] Extend i18n empty title/body (ko/en)
- [x] T019 [US3] Create `src/components/PerformanceEmpty.astro` and render when `pageEmpty` (replace Summary/Cards; keep title/switcher/disclaimer)
- [x] T020 [US3] Soft messaging when bundle exists but cumulative null and all presentation unavailable
- [x] T021 [US3] Smoke: `npm run build` with performance files absent (or moved aside) — must succeed (FR-006 / SC-004)

**Checkpoint**: Empty path verified. Proceed to US4.

---

## Phase 6: User Story 4 — Full bilingual chrome (Priority: P2)

**Goal**: All required performance strings localized; locale switch preserves market facts  
**Independent Test**: Checklist of required keys present in ko and en; switch `lang` keeps same `market` outcomes

### Implementation for User Story 4

- [x] T022 [US4] Audit `performance.astro` + components for hardcoded strings — move leftovers into `i18n.ts`
- [x] T023 [P] [US4] Ensure lang toggle URLs on performance page preserve `market`
- [x] T024 [US4] [REVIEW] Bilingual copy review (disclaimer, non-fund, index note, empty) — SC-005/006/008

**Checkpoint**: i18n complete. Proceed to US5.

---

## Phase 7: User Story 5 — Discoverability (Priority: P3)

**Goal**: Primary nav links to performance in both locales  
**Independent Test**: From home/layout, click Performance → localized `/performance`

### Implementation for User Story 5

- [x] T025 [US5] Add Performance nav link in `src/layouts/Layout.astro` (`{base}performance?lang={lang}`)
- [x] T026 [P] [US5] Add nav label keys in `i18n.ts` if not already from T009

**Checkpoint**: Nav discoverable. Proceed to Polish.

---

## Phase 8: Polish & Cross-Cutting

**Purpose**: Checks, constitution regression, docs touch

- [x] T027 [P] Run `npm run check` and `npm run test:performance-ui` — fix failures
- [x] T028 [P] Run `npm run build` with and without `content/performance/*.json` present
- [x] T029 Confirm `git diff` shows no unintended changes under `content/daily/`, `scripts/` scoring, or Score weights
- [x] T030 [P] [SUBAGENT] Update issue/PR notes or `specs/020-performance-dashboard/quickstart.md` if commands drifted
- [x] T031 [REVIEW] Final constitution + spec acceptance sweep (FR-001–026 / SC-001–010); approve merge readiness

**Execution notes**: T027∥T028∥T030. Pause at T031.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (1)**: start immediately
- **Foundational (2)**: depends on Setup — **BLOCKS** all US phases
- **US1 (3)**: after T008 approval — MVP
- **US2 (4)**: after US1 page shell exists (needs `performance.astro`)
- **US3 (5)**: after US1 (empty component swap)
- **US4 (6)**: after US1–US3 copy surfaces exist
- **US5 (7)**: after i18n nav label available (can parallel late US4)
- **Polish (8)**: after desired stories complete

### Within stories

1. [TDD] tests fail before implementation
2. Aggregate API before Astro consumers
3. [REVIEW] gates pause for human
4. Prefer sequential US1 → US2 → US3; US4/US5 lighter

### Parallel Opportunities

| Parallel set | Tasks |
|--------------|-------|
| Setup | T002 ∥ (T001 sequential if editing same `package.json`) |
| Foundation tests | T003 ∥ T005 |
| US1 i18n vs later | T009 can start after T008 beside T010 |
| US2/US3 i18n | T014 ∥ T018 (different keys) |
| Polish checks | T027 ∥ T028 ∥ T030 |

---

## Superpowers Execution

### Execution Discipline by Marker

- **[TDD]**: RED → GREEN → REFACTOR; use `test-driven-development` skill if available
- **[SUBAGENT]**: Dispatch via Task tool when marked; else sequential
- **[REVIEW]**: Pause; present diff/summary; wait for explicit approval
- **[P]**: Parallelize only when file sets do not conflict

### Checkpoint Protocol

At every phase boundary:
1. Summarize completed tasks
2. Run `npm run test:performance-ui` (and `npm run check` from Phase 3+)
3. Ask: "Phase [N] complete. Proceed to Phase [N+1]?"
4. Continue only after explicit user approval

---

## Notes

- Live `content/performance/` may be absent in this worktree — rely on test fixtures + empty-state path
- Optional SVG must not replace table as a11y source of truth
- Commit after each task or logical group when user requests commits
- Stop at T008 / T013 / T024 / T031 review gates
