# Data Model: Performance Dashboard (view layer)

**Feature**: `020-performance-dashboard`  
**Date**: 2026-08-30  
**Source of truth**: `content/performance/{KR|US}.json` ↔
`scripts/schema/performance-bundle.schema.json` / `PerformanceBundle`  
**This feature adds no new persisted schemas** — only in-memory view models.

## Entity overview

```text
PerformanceBundle (Git JSON, read-only)
        │
        ▼
performanceLoad → PerformanceBundle | null
        │
        ▼
performanceAggregate → MarketPerformanceView
        ├── CumulativeSeries
        ├── HorizonSummary[] (presentation + secondary)
        └── ViewFlags (empty, caveats)
```

---

## PerformanceBundle (persisted input — unchanged)

See #63 / `performance-bundle.schema.json`. Key fields consumed:

| Field | Use |
|-------|-----|
| `market` | Must match requested market |
| `asOfDate` | Display + FR-013/020 |
| `runMeta` | Optional provenance line (provider, generatedAt) |
| `measurements[]` | Aggregation input |

### PerformanceMeasurement (consumed fields)

| Field | Role in UI |
|-------|------------|
| `pickDate`, `symbol` | Series ordering / table rows |
| `horizonId` | Bucket into cumulative + cards |
| `completionStatus`, `incompleteReason` | Filter / unavailable |
| `forwardReturn` | Pick side |
| `benchmarkReturn`, `benchmarkCompletionStatus` | Bench side / FR-021 |
| `survivorshipFlag` | Caveat FR-019 |

**Validation**: CI `validate:content`; UI treats invalid/missing as empty
(fail-closed).

---

## MarketPerformanceView (derived, not persisted)

| Field | Type | Rules |
|-------|------|-------|
| `market` | `KR` \| `US` | |
| `asOfDate` | `YYYY-MM-DD` \| null | null when empty |
| `empty` | boolean | true if no bundle or no usable cumulative **and** all presentation horizons unavailable |
| `pageEmpty` | boolean | true if bundle null or `measurements.length === 0` |
| `cumulative` | `CumulativeSeries` \| null | |
| `horizons` | `HorizonSummary[]` | Always includes slots for 1M,3M,6M,1Y; may include H20,H60 |
| `hasSurvivorshipCaveat` | boolean | Any shown aggregate includes non-`listed` |
| `benchmarkGapCount` | number | Pick-complete rows with incomplete bench in cumulative horizon |

### CumulativeSeries

| Field | Type | Rules |
|-------|------|-------|
| `horizonId` | `HorizonId` | Chosen per research R2 |
| `points` | `CumulativePoint[]` | Chronological |
| `finalPortfolioReturn` | number \| null | Last point portfolio; null if empty |
| `finalBenchmarkReturn` | number \| null | Last bench point if any; may lag |
| `excessClaimAllowed` | boolean | false if any pick step lacked complete bench |

### CumulativePoint

| Field | Type | Rules |
|-------|------|-------|
| `pickDate` | `YYYY-MM-DD` | |
| `symbol` | string | Escape on render |
| `portfolioCumulative` | number | Compounded to date |
| `benchmarkCumulative` | number \| null | null if this step skipped for bench |
| `pickReturn` | number | Period return |
| `benchmarkReturn` | number \| null | |
| `survivorshipFlag` | SurvivorshipFlag | |

### HorizonSummary

| Field | Type | Rules |
|-------|------|-------|
| `horizonId` | `HorizonId` | |
| `tier` | `presentation` \| `secondary` | presentation = 1M/3M/6M/1Y |
| `available` | boolean | `nComplete > 0` |
| `nComplete` | number | |
| `avgPickReturn` | number \| null | |
| `avgBenchReturn` | number \| null | |
| `excessClaimAllowed` | boolean | |
| `survivorshipCaveat` | boolean | |

---

## State transitions (UI)

```text
bundle missing/empty → pageEmpty
  → PerformanceEmpty (market-scoped)

bundle with data → aggregate
  → cumulative null + all presentation unavailable → soft empty messaging
  → else render Summary + HorizonCards (+ secondary)
```

No write transitions. No Score/daily mutations.

---

## Relationships

| From | To | Cardinality |
|------|----|-------------|
| PerformanceBundle | MarketPerformanceView | 0..1 derived per market request |
| MarketPerformanceView | HorizonSummary | 4 presentation + 0..2 secondary |
| CumulativeSeries | CumulativePoint | 0..N |
