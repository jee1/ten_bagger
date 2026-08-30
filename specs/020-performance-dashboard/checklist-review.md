# Review checklist — 020

**Date**: 2026-08-30  
**Feature**: Performance Dashboard Page (`020-performance-dashboard`, Issue #64)  
**Reviewer**: Senior Code Reviewer (read-only; working tree inspected via `git status` / `git diff HEAD` + untracked `src/`)  
**Scope**: `spec.md` FR-001–026 / SC / US1–5; `plan.md`; `research.md` R2–R3; constitution Principles I–V; implementation under `src/` + `package.json` script; superspec dimensions (compliance, edge cases, constitution, security, tests)

**Calibration**: Findings only at confidence ≥ 80. Severity: Critical > Important > Suggestion.

**Verdict**: **PASS** (see [Re-review 2026-08-30 (pass 2)](#re-review-2026-08-30-pass-2); prior pass-1 verdict was FAIL)

---

## Critical

*(none at confidence ≥ 80)*

---

## Important

### 1. SC-008 / FR-015 — equal-weight compounding not stated on-page — confidence 94

**Description**: SC-008 requires the page to label the cumulative series as hypothetical **and** state equal-weight-per-pick-day compounding in plain language (or link to methodology-equivalent wording on-page). `PerformanceSummary.astro` shows hypothetical + index-proxy notes, but neither i18n nor the summary/table states equal-weight / per-pick-day compounding, and there is no methodology link for that rule. Aggregate math in `performanceAggregate.ts` matches research R2, but the reader-facing SC is unmet.

**Files**: `src/components/PerformanceSummary.astro:46-52`, `src/lib/i18n.ts` (performance\* keys; no equal-weight copy)

**Recommendation**: Add bilingual copy (or a short on-page methodology link) adjacent to the cumulative heading stating equal weight per scored pick day, chronological compound of completed measurements only. Optionally mirror the same sentence under Horizons if space allows.

---

### 2. US1 acceptance / FR-003 — benchmark identity not shown — confidence 90

**Description**: US1 acceptance scenario 3 and FR-003 require each market to show its own benchmark identity (KOSPI for KR, S&P 500 for US / KR-KOSPI·US-SPX). The UI only labels a generic “Benchmark” / “벤치마크”; `benchmarkId` from measurements is never surfaced. Market switch separates KR/US series correctly (FR-012/018), but readers cannot tell which index proxy they are comparing against without prior knowledge.

**Files**: `src/components/PerformanceSummary.astro:56-60`, `src/components/HorizonCards.astro:42-46`, `src/pages/performance.astro:24-28`

**Recommendation**: Derive display label from market (`KR` → KOSPI / KR-KOSPI, `US` → S&P 500 / US-SPX) or from the first measurement’s `benchmarkId`, and show it next to the primary summary and (optionally) horizon cards.

---

### 3. FR-021 — final benchmark % shown while claiming unavailable — confidence 91

**Description**: When any cumulative step has incomplete benchmark (`excessClaimAllowed === false`), the summary still prints `finalBenchmarkReturn` as a percentage **and** the “benchmark unavailable” string. Example path: fixture row `CCC` (`benchmarkCompletionStatus: incomplete`) → portfolio compounds all H20 completes, bench compounds only complete steps, UI shows both a partial bench % and unavailable copy. That contradicts FR-021’s “pick + benchmark-unavailable, no excess claim” clarity and invites false pick-vs-bench comparison on misaligned windows. Horizon cards correctly swap bench avg for unavailable when `!excessClaimAllowed`; cumulative summary does not.

**Files**: `src/components/PerformanceSummary.astro:56-64`; logic `src/lib/performanceAggregate.ts:92-126,119`

**Recommendation**: When `!series.excessClaimAllowed`, render bench final as “—” / unavailable only (keep per-row table nulls as today). Do not print a partial cumulative bench % next to the unavailable caveat. Optionally still expose `benchmarkGapCount` in muted copy for transparency.

---

## Suggestions

### 4. `forwardReturn ?? 0` can fabricate a zero return — confidence 82

**Description**: `buildCumulative` uses `row.forwardReturn ?? 0` for pick-complete rows. Schema `performance-bundle.schema.json` does not `allOf`-require `forwardReturn` when `completionStatus === "complete"` (019 research says it should be present; gate may still allow omission). Treating missing as `0` violates FR-005’s “not treating missing data as a zero return” spirit.

**File**: `src/lib/performanceAggregate.ts:93`

**Recommendation**: Skip rows with non-finite/missing `forwardReturn` (or fail that row out of the series) instead of coalescing to `0`; add a unit test for complete-but-null return.

---

### 5. Thin test coverage beyond happy-path R2/R3 — confidence 80

**Description**: Aggregate tests cover null → `pageEmpty`, H20 compound `0.32`, gap → `excessClaimAllowed=false`, presentation means, secondary tiers. Missing: empty `measurements: []` vs all-incomplete soft-empty; `forwardReturn` null; load market-mismatch / invalid JSON → `null`. Load tests only missing file + valid fixture.

**Files**: `src/lib/performanceAggregate.test.ts`, `src/lib/performanceLoad.test.ts`

**Recommendation**: Add 2–3 focused cases for soft-empty, invalid load, and null return handling once behavior in finding 4 is fixed.

---

### 6. Worktree / HEAD lack `content/performance/*.json` — confidence 85

**Description**: Spec assumes #63 artifacts; this branch HEAD has no `content/performance/` (or `content/ledger/`). Runtime correctly fail-closes to `PerformanceEmpty` (FR-006/022). SC-002 / US1 independent tests still need published or fixture-backed content for a production-like visual check.

**Recommendation**: Before merge verification of SC-002, regenerate or commit sample `content/performance/{KR,US}.json`, or document that reviewers must run `regenerate:ledger` / use fixtures under a local content root.

---

## Spec / constitution checklist summary

| Area | Result | Notes |
|------|--------|-------|
| US1 cumulative + bench + hypothetical | **Partial** | Series/table/SVG + hypothetical OK; bench **identity** missing (Important #2); equal-weight wording missing (Important #1) |
| US2 horizons 1M/3M/6M/1Y + H20/H60 secondary | **Pass** | Presentation slots always; secondary demoted; unavailable copy when `nComplete===0` |
| US3 empty / thin data | **Pass** | `pageEmpty` → `PerformanceEmpty`; soft-empty when bundle present but unusable (aligned with `data-model.md`) |
| US4 i18n | **Pass** | Required chrome keys ko/en; lang toggle preserves query via Layout |
| US5 nav discovery | **Pass** | Layout nav link `performance?lang=` |
| FR-001–014 (core path, read-only, disclaimer, nav, no Score) | **Pass** (modulo FR-003 identity) | Disclaimer via Layout `Disclaimer`; no content writes; no Score/scripts changes |
| FR-015–026 (compounding, secondary, index note, gaps, XSS, a11y table) | **Partial** | R2/R3 math + FR-017 note + FR-026 table + Astro escape OK; FR-015 copy / FR-021 summary UX / FR-003 identity fail Important |
| SC-001–010 | **Partial** | SC-008 fail; SC-002 needs real/fixture content in tree (Suggestion #6) |
| Edge: one-market empty, short history, survivorship, incomplete bench, divergent as-of | **Pass** with caveats | Survivorship caveat wired; incomplete bench flagged; as-of per market; Important #3 on how bench gap is *displayed* |
| Research R2 cumulative | **Pass** (code) | H20-prefer fallback, chronological equal-weight compound, bench step omit on gap |
| Research R3 horizon cards | **Pass** | Means, `excessClaimAllowed`, `survivorshipCaveat`, secondary below |
| Constitution I Git-content SoT | **Pass** | Read `content/performance/{market}.json` via cwd; no runtime DB |
| Constitution II PIT / survivorship | **Pass** | Per-market `asOfDate`; non-`listed` → caveat; no quiet drop |
| Constitution III Additive artifacts | **Pass** | Display-only derivation; no write-back |
| Constitution IV Score freeze | **Pass** | No selection/weight changes |
| Constitution V Schema / validation | **Pass** | Generated `PerformanceBundle` types; `npm run check` 0 errors; `test:performance-ui` 7/7 pass |
| Security (FR-024) | **Pass** | Public static; Astro text interpolation escapes; no secrets in client path |
| Code quality | **Pass** | Small surface; cwd-based load documented; no new deps |

---

## Test evidence (reviewer ran)

- `npm run test:performance-ui` → 7 pass  
- `npm run check` → 0 errors / 0 warnings  

---

## Final verdict

**FAIL** *(pass 1, superseded)* — three Important findings (SC-008 equal-weight copy; FR-003/US1 benchmark identity; FR-021 contradictory bench % + unavailable). No Critical. Address Important #1–#3 before merge from a review perspective; Suggestions may follow.

---

## Re-review 2026-08-30 (pass 2)

**Date**: 2026-08-30  
**Reviewer**: Senior Code Reviewer (read-only re-check after Important fixes)  
**Scope**: Prior Important #1–#3 + Suggestion #4 (`forwardReturn`); FR-003 / FR-015 / FR-021 / SC-008; `PerformanceSummary.astro`, `i18n.ts`, `performanceAggregate.ts`  
**Calibration**: Findings only at confidence ≥ 80.

**Verdict**: **PASS**

### Prior Important — re-check

| # | Prior finding | Status | Evidence | Confidence |
|---|---------------|--------|----------|------------|
| 1 | SC-008 / FR-015 equal-weight copy missing | **Resolved** | `performanceEqualWeight` (ko/en) in `i18n.ts`; rendered in `PerformanceSummary.astro` under hypothetical copy. States equal-weight compounding of completed pick days with `no_pick` excluded. | 93 |
| 2 | FR-003 / US1 benchmark identity missing | **Resolved** | `performanceBenchmarkIdKR` / `performanceBenchmarkIdUS` (KOSPI / KR-KOSPI, S&P 500 / US-SPX) shown by `view.market` in `PerformanceSummary.astro`. Horizon identity still optional (unchanged). | 92 |
| 3 | FR-021 final bench % + unavailable | **Resolved** | Summary bench line is ternary: `excessClaimAllowed ? pct(finalBenchmarkReturn) : label('performanceBenchmarkUnavailable')` — no partial % alongside unavailable. Per-row table nulls unchanged (as previously recommended). | 95 |

### Prior Suggestion #4 — re-check

| # | Prior finding | Status | Evidence |
|---|---------------|--------|----------|
| 4 | `forwardReturn ?? 0` fabricates zero | **Resolved** | `buildCumulative` skips with `continue` when `typeof !== 'number' \|\| !Number.isFinite(forwardReturn)`. |

### Critical / Important remaining (confidence ≥ 80)

*(none)*

### Suggestions still open (non-blocking)

- **#5** Thin tests beyond happy-path R2/R3 (still no dedicated case for non-finite / null `forwardReturn` skip) — confidence 80.
- **#6** Worktree / HEAD may still lack published `content/performance/*.json` for SC-002 production-like visual check — confidence 85.

### Spec checklist delta (pass 2)

| Area | Result | Notes |
|------|--------|-------|
| US1 + FR-003 identity | **Pass** | Primary summary shows KOSPI / S&P 500 (+ KR-KOSPI / US-SPX) |
| FR-015 / SC-008 equal-weight + hypothetical + index note | **Pass** | Hypothetical + equal-weight + index-proxy note adjacent to primary summary |
| FR-021 gap display | **Pass** | Final bench unavailable-only when `!excessClaimAllowed` |
| FR-005 missing return | **Pass** (code) | Non-finite `forwardReturn` skipped, not coerced to 0 |

### Test evidence (re-reviewer ran)

- `npm run test:performance-ui` → 7 pass  

### Final verdict (pass 2)

**PASS** — prior Important #1–#3 and Suggestion #4 are fixed. No Critical or Important findings remain at confidence ≥ 80. Open Suggestions (#5 thin tests, #6 content artifacts) do not block.
