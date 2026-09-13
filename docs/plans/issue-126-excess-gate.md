# Plan — Issue #126: Excess-return publication gate

- **Issue**: [#126](https://github.com/jee1/ten_bagger/issues/126) (F3 of Epic [#118](https://github.com/jee1/ten_bagger/issues/118), follows #119)
- **Role split**: planning only; worker implements + opens PR.
- **Baseline**: `origin/main` at `83d0d3e` (after #127 / zero-volume caveat).
- **Headline decision**: **KEEP** — do not publish a headline Excess % on `/performance` until all
  three gates pass on the cumulative horizon. Until then, render `—` and the existing pending copy.
  No Score freeze change.
- **Blast radius**: `src/lib/excessGate.ts` (new), `performanceAggregate.ts`, `PerformanceSummary.astro`,
  `performanceAggregate.test.ts`, methodology gate note. No bundle/schema changes.

---

## 1. Problem

`PerformanceSummary.astro` hardcodes Excess to `—`. Benchmark and portfolio cumulative returns are
shown when `excessClaimAllowed` (per-pick benchmark completeness), but there is no separate review
gate before claiming **excess return** (portfolio minus benchmark) as a public number. Issue #119
retargeted pending copy to sample/benchmark coverage; this issue adds an explicit, testable gate.

---

## 2. Gate thresholds (written before any number is published)

All three must pass on the **cumulative-series horizon** (the horizon selected by
`CUMULATIVE_FALLBACK` in `performanceAggregate.ts`):

| Gate | Threshold | Rationale |
|------|-----------|-----------|
| **G1 — Minimum sample** | `nComplete ≥ 20` pick-complete rows on that horizon | Aligns with ADR 0004 / walk-forward coverage floor (`≥20` OOS scored picks). |
| **G2 — Benchmark completeness** | `excessClaimAllowed === true` (every pick-complete row also has complete benchmark) | Same rule as FR-021 / research R3; no partial-window excess claim. |
| **G3 — Horizon tier** | Horizon id ∈ `{1M, 3M, 6M, 1Y}` (`tier === 'presentation'`) | H20/H60 are engineering/secondary (FR-016); public excess must not ride a secondary horizon. |

**Additional precondition (already enforced elsewhere):** price-basis validation
`priceBasisValidation === 'complete'` (#119). Incomplete basis → gate closed.

**Excess value when published:** `finalPortfolioReturn − finalBenchmarkReturn` on the cumulative
equal-weight chain (display-only; not a new SoT field).

---

## 3. Publish vs keep

| Question | Decision |
|----------|----------|
| Publish Excess on live KR today? | **No (KEEP).** Cumulative prefers H20 when available; H20 is secondary → G3 fails. KR also has 20× H20 but that does not satisfy G3. |
| When would Excess appear? | When cumulative fallback selects a presentation horizon **and** G1+G2+price-basis pass (e.g. future state with enough 1M/3M/6M/1Y history and no earlier H20 preference override). |
| Methodology | Document thresholds in public methodology (gate table); do not imply a live excess figure exists today. |

---

## 4. Implementation sketch

### 4.1 `src/lib/excessGate.ts`

Export `EXCESS_GATE_MIN_SAMPLE = 20`, `evaluateExcessGate(series, tier, priceBasisValidation)` →
`{ publish, excessReturn, reasons }`.

### 4.2 `performanceAggregate.ts`

After `buildCumulative`, attach `tier`, `excessPublishAllowed`, `excessReturn` on `CumulativeSeries`.

### 4.3 `PerformanceSummary.astro`

Render Excess % only when `series.excessPublishAllowed`; else `—` + `performanceExcessPending`.

### 4.4 Tests (`performanceAggregate.test.ts`)

- Fixture with 2 complete H20 rows + full bench → `excessPublishAllowed === false` (G1).
- `krSample` with bench gap → false (G2).
- Synthetic 20× H20, full bench, complete price basis → false (G3).
- Synthetic 20× 1M only (no H20), full bench → true; excess ≈ mean pick − mean bench on chain.

### 4.5 Methodology

Short subsection under performance / measurement honesty listing G1–G3 (no live number).

---

## 5. Out of scope

- Changing `CUMULATIVE_FALLBACK` order or Score v3 merge gate.
- Horizon-card excess columns (still pick/bench means only).
- New content bundle fields.
