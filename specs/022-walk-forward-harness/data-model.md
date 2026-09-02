# Data Model: Walk-Forward Harness

**Date**: 2026-09-01  
**Spec**: [spec.md](./spec.md)  
**Schema**: [contracts/walk-forward-report.schema.json](./contracts/walk-forward-report.schema.json)

## Entities

### WalkForwardRunConfig

Runtime input (CLI flags + JSON config file). Not persisted as content artifact.

| Field | Type | Rules |
|-------|------|-------|
| `runIntent` | `"exploratory"` \| `"go_evidence"` | Required |
| `measurementSource` | `"ledger"` \| `"fixture-recompute"` | `go_evidence` → must be `ledger` |
| `candidateIds` | string[] | 1–4 entries |
| `foldSpec` | FoldSpec | Rolling only in v1 |
| `markets` | `("KR"\|"US")[]` | Subset of calendar |
| `ledgerDir` | path | Default `content/ledger` |
| `performanceDir` | path | Default `content/performance` |
| `outputDir` | path | Default `content/walk-forward` |

### FoldSpec (rolling v1)

| Field | Type | Rules |
|-------|------|-------|
| `mode` | `"rolling"` | v1 const |
| `trainSessions` | int | ≥ 1 |
| `oosSessions` | int | ≥ 1 |
| `stepSessions` | int | ≥ 1 |
| `startDate` | ISO date | Inclusive |
| `endDate` | ISO date | Inclusive |

**Validation**: Generated folds ≥ 2 (FR-023). For each fold, train and OOS decision-date sets disjoint (FR-027).

### WalkForwardFold (report)

| Field | Type | Rules |
|-------|------|-------|
| `foldIndex` | int | 0-based |
| `trainRange` | DateRange | Per market when applicable |
| `oosRange` | DateRange | Strictly after train |
| `status` | enum | `complete`, `incomplete_horizon`, `skipped_empty_train` |
| `pickDays` | int | Scored picks in OOS |
| `noPickDays` | int | OOS days without pick |
| `horizons` | HorizonMetrics[] | H20 required when complete picks exist |

### ScreeningCandidate

| Field | Type | Rules |
|-------|------|-------|
| `candidateId` | string | Unique in run |
| `scoreVersion` | int | Default 2 |
| `weightOverrides` | object? | Optional manual grid entry |

Not a live weight merge — analysis only (Principle IV).

### OOSReport (persisted artifact)

Top-level JSON written to `content/walk-forward/{runId}.json`.

| Field | Type | Rules |
|-------|------|-------|
| `schemaVersion` | string | `"0.1.0"` |
| `runId` | string | UUID or deterministic hash prefix |
| `runIntent` | enum | FR-021 |
| `measurementSource` | enum | FR-022 |
| `configHash` | string | SHA-256 of canonical config; no secrets |
| `generatedAt` | ISO datetime | UTC |
| `candidateId` | string | Single candidate per run (v1) |
| `folds` | WalkForwardFold[] | |
| `aggregate` | AggregateMetrics | Cross-fold rollup |
| `coverage` | CoverageBlock | Includes `insufficientCoverage` flag |

### CoverageBlock

| Field | Type | Rules |
|-------|------|-------|
| `oosPickDays` | int | Aggregate scored pick days |
| `noPickDays` | int | |
| `noPickRatio` | float | |
| `insufficientCoverage` | bool | true when `go_evidence` and `oosPickDays` < 20 |

### HorizonMetrics (per fold / aggregate)

| Field | Type | Rules |
|-------|------|-------|
| `horizonId` | `"H20"` \| `"H60"` | ADR 0003 |
| `benchmarkId` | `"KR-KOSPI"` \| `"US-SPX"` | When market present |
| `pickReturnMean` | float? | Excludes `no_pick` days |
| `hitRate` | float? | Fraction positive pick returns |
| `excessReturnMean` | float? | Pick minus benchmark |
| `status` | `"complete"` \| `"incomplete"` | |

### PITAssumptionsRecord (documentation)

Human-readable doc, not machine report. Covers:

- Decision cut at `t` (features/prices ≤ `t`)
- Entry/exit basis (ADR 0002 reference)
- H20/H60 session definition
- Rolling vs anchored (anchored deferred)
- Distinction from `backtest_screen`

## State transitions (fold status)

```text
pending → skipped_empty_train   (zero train picks)
pending → incomplete_horizon    (OOS extends past asOfDate or H20/H60 incomplete)
pending → complete              (metrics computed)
```

## Relationships

```text
WalkForwardRunConfig 1──* WalkForwardFold
WalkForwardFold *──1 ScreeningCandidate (evaluated picks per OOS day)
WalkForwardFold *──* LedgerMeasurement (via pickDate+symbol lookup when measurementSource=ledger)
OOSReport 1──1 WalkForwardRunConfig (via configHash)
```
