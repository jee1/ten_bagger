# Research: Performance Dashboard Page (#64)

**Feature**: `020-performance-dashboard`  
**Date**: 2026-08-30  
**Input**: Brainstormed `spec.md` (Q1–Q8 Resolved); constitution I–V; ADR 0001–0003;
existing Astro `?lang=` pages; `PerformanceBundle` types from #63

## R1 — Content loading (missing files allowed)

**Decision**: Build-time read of `content/performance/KR.json` and
`content/performance/US.json` via a small loader (`performanceLoad.ts`).

- File missing or unreadable → `null` for that market (page-level empty for that
  market only — FR-018).
- File present → parse as `PerformanceBundle` (trust `validate:content` in CI;
  defensive type narrow at boundary).
- Loader MUST NOT write or transform files on disk.

**Rationale**: Spec empty-state + constitution I; this worktree may lack
performance files until regenerate; site must still build (FR-006).

**Alternatives considered**:

- Astro content collection for performance → extra config; YAGNI vs direct JSON.
- Fail entire build if missing → violates FR-006 / SC-004.
- Runtime fetch → not static GitHub Pages model.

## R2 — Cumulative series algorithm (FR-015)

**Decision**:

1. Select **series horizon** for the primary cumulative chart:
   - Prefer **`H20`** when ≥1 completed pick measurement exists (ADR 0003
     primary).
   - Else first of `1M`, `3M`, `6M`, `1Y` with ≥1 completed pick measurement.
   - Else no cumulative series → empty cumulative region.
2. Take measurements for that horizon with `completionStatus === "complete"`,
   sort by `pickDate` ascending (tie-break `symbol`).
3. Compound equal-weight:  
   `portfolioFactor *= (1 + forwardReturn)` per row;  
   series point after each pick day = `portfolioFactor - 1`.
4. Parallel benchmark compound using the same rows’ `benchmarkReturn` **only
   when** `benchmarkCompletionStatus === "complete"` for that row.
5. If a row has complete pick but incomplete benchmark → include pick in
   portfolio compound; **omit** that step from benchmark compound **and** flag
   the series/window as “benchmark incomplete for N picks” (no excess-return
   claim for those steps — FR-021).
6. Exclude all incomplete pick rows and all `no_pick` (they never appear in
   measurements per #63).

**Rationale**: Matches brainstorm Q1; H20 aligns merge-gate metric without
replacing presentation horizon cards (Q2 / FR-016).

**Alternatives considered**:

- Compound 1M only for cumulative → weaker ADR alignment; overlapping calendar
  windows confuse “portfolio” narrative.
- Score-capital weights → rejected in brainstorm.
- Average-only cumulative (no compound) → weaker “portfolio vs bench” story.

## R3 — Horizon summary cards (FR-004 / FR-016)

**Decision**: For each id in presentation set `{1M,3M,6M,1Y}` and secondary
`{H20,H60}`:

| Metric | Rule |
|--------|------|
| `nComplete` | Count pick-complete rows |
| `avgPickReturn` | Arithmetic mean of `forwardReturn` over pick-complete rows; null if n=0 |
| `avgBenchReturn` | Mean of `benchmarkReturn` over rows with both pick+bench complete; null if none |
| `excessClaimAllowed` | true only if every pick-complete row in the set also has bench complete **and** n≥1; else false / show caveat |
| `survivorshipCaveat` | true if any included row has `survivorshipFlag !== "listed"` |

Unavailable card when `nComplete === 0` (explicit copy, not `0%`).

Secondary H20/H60 rendered **below** presentation set, visually demoted.

**Rationale**: Spec summaries + honest excess (FR-021) + survivorship (FR-019).

**Alternatives considered**: Median instead of mean → YAGNI. Hide secondary
horizons → rejected (Q2 option 2).

## R4 — Routing and market switch

**Decision**: Single page `src/pages/performance.astro` with query params:

- `lang=ko|en` (default `ko`) — same as existing pages
- `market=KR|US` (default `KR`)

Market switcher links preserve `lang`. Nav in `Layout.astro` adds Performance
link with current `lang`.

**Rationale**: Matches site i18n pattern; FR-001/009/012.

**Alternatives considered**: `/ko/performance` path i18n → larger routing change.
Separate `performance/kr.astro` files → duplication.

## R5 — Visualization without new dependencies

**Decision**:

- Primary: **numeric summary + HTML table** of cumulative points (and/or last
  cumulative %) as the **non-visual required alternative** (FR-026 / SC-010).
- Optional: inline **SVG polyline** for portfolio vs bench (same data),
  decorative; table remains source of truth for a11y.
- No Chart.js/D3/Observable Plot.

**Rationale**: Ponytail / zero new deps; package.json currently Astro-only
runtime.

**Alternatives considered**: Add chart library → dependency + XSS surface.
Canvas-only chart → fails FR-026.

## R6 — Copy / trust labeling

**Decision**: i18n keys for: nav label, page title, cumulative heading, horizon
headings, empty states, “benchmark unavailable”, survivorship caveat,
**hypothetical / not a fund**, index ≠ tradable product (chart-adjacent), reuse
`Disclaimer` component (FR-008/017/025).

**Rationale**: Brainstorm Q3/F1; constitution disclaimer.

**Alternatives considered**: Methodology-only disclaimer → too easy to miss on
this page.

## R7 — Testing strategy

**Decision**: Pure functions in `performanceAggregate.ts` (+ load helper) tested
with Node 22’s test runner and stripped types or small `.mts` fixtures under
`src/lib/` or `scripts/tests/performance_ui/` — prefer colocated
`performanceAggregate.test.ts` runnable via:

```bash
node --experimental-strip-types --test src/lib/performanceAggregate.test.ts
```

Add npm script `test:performance-ui` later in tasks. Keep `astro check` + `build`
as integration smoke.

**Rationale**: No Vitest in repo; avoid new test framework dep.

**Alternatives considered**: Vitest → new dep. pytest for TS → wrong stack.

## NEEDS CLARIFICATION

None remaining — brainstorm Q1–Q8 + research R1–R7 cover planning unknowns.
