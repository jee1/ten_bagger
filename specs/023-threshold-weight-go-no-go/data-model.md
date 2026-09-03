# Data Model: Threshold·Weight GO/NO-GO Recalibration

**Date**: 2026-09-03  
**Spec**: [spec.md](./spec.md)  
**Schema**: [contracts/calibration-report.schema.json](./contracts/calibration-report.schema.json)

## Entities

### CalibrationRunConfig

Runtime input (CLI + JSON). Not the live selection SoT.

| Field | Type | Rules |
|-------|------|-------|
| `packageIntent` | `"exploratory"` \| `"go_evidence"` | Required (FR-032) |
| `mode` | `"search"` \| `"baseline-only"` | Required (FR-025) |
| `candidates` | CandidateSpec[] | `search`: 1–10; `baseline-only`: empty or single baseline id |
| `isFoldSpec` | FoldSpec | Rolling; used only for IS ranking (`search`) |
| `oosFoldSpec` | FoldSpec | Rolling; disjoint decision dates from IS (FR-002) |
| `markets` | `("KR"\|"US")[]` | Subset of calendar |
| `promoteTopN` | int | Default 1; how many IS winners get OOS GO eval in `search` |
| `measurementSourceIs` | `"ledger"` \| `"fixture-recompute"` | IS may use fixture for smoke |
| `measurementSourceOos` | `"ledger"` \| `"fixture-recompute"` | `go_evidence` package → OOS **must** be `ledger` |
| `ledgerDir` / `performanceDir` | path | Defaults from config |
| `outputDir` | path | Default `content/calibration` |
| `walkForwardOutputDir` | path | Default `content/walk-forward` |

**Validation**:
- `len(candidates) ≤ 10` (FR-024) else fail before evaluation  
- `baseline-only` forbids non-empty search grid that implies selection  
- IS vs OOS decision-date sets must be disjoint for GO packages  
- Each CandidateSpec validated (FR-012, FR-021)

### CandidateSpec

| Field | Type | Rules |
|-------|------|-------|
| `candidateId` | string | Unique within run |
| `threshold` | number \| null | null → live `COMPOSITE_THRESHOLD` |
| `weights` | WeightVector \| null | null → live top-level WEIGHT_* |
| `notes` | string? | Optional human label |

### WeightVector

Top-level COMPOSITE factors only (FR-020):

| Key | Type | Rules |
|-----|------|-------|
| `WEIGHT_SIZE` | number | Required if weights present |
| `WEIGHT_VALUATION` | number | Required |
| `WEIGHT_GROWTH` | number | Required |
| `WEIGHT_QUALITY` | number | Required |
| `WEIGHT_ENTRY` | number | Required |
| `WEIGHT_MOMENTUM` | number | Required |

**Validation**: sum within `1.0 ± 1e-6`; each finite; nested keys FORBIDDEN.

### IsRankingEntry

| Field | Type | Rules |
|-------|------|-------|
| `candidateId` | string | |
| `rank` | int | 1 = best |
| `isMetricH20ExcessMean` | float \| null | Primary sort key |
| `isPickDays` | int | Tie-break |
| `walkForwardReportPath` | string | Relative path to IS WF report |
| `walkForwardConfigHash` | string | No secrets |
| `status` | enum | `ranked` \| `rejected_invalid` \| `failed` |

### OosEvaluationEntry

| Field | Type | Rules |
|-------|------|-------|
| `candidateId` | string | |
| `walkForwardReportPath` | string | OOS WF report |
| `walkForwardConfigHash` | string | |
| `oosPickDays` | int | |
| `noPickRatio` | float | Informational |
| `h20ExcessReturnMean` | float \| null | |
| `h60ExcessReturnMean` | float \| null | Reported |
| `insufficientCoverage` | bool | |
| `contaminationFindings` | string[] | Empty if clean |
| `verdict` | `"GO"` \| `"NO-GO"` | Per candidate |
| `failedBullets` | string[] | Named on NO-GO |

### CalibrationReport (persisted)

`content/calibration/{runId}.json`

| Field | Type | Rules |
|-------|------|-------|
| `schemaVersion` | string | `"0.1.0"` |
| `runId` | string | Deterministic hash prefix or UUID policy per research |
| `packageIntent` | enum | FR-032 |
| `mode` | enum | |
| `configHash` | string | SHA-256 canonical config; no secrets (FR-027) |
| `generatedAt` | ISO datetime | UTC; stable under same inputs if derived from config hash only — prefer omit wall-clock from hashed payload; store but exclude from determinism of sibling fields like 022 |
| `liveConstantsSnapshot` | object | Frozen threshold + weights at run time (read-only echo) |
| `isRanking` | IsRankingEntry[] | Empty in `baseline-only` |
| `selectionRationale` | string | How winners chosen (IS metric + ties) |
| `oosEvaluations` | OosEvaluationEntry[] | |
| `overallVerdict` | `"GO"` \| `"NO-GO"` \| `"N/A"` | `N/A` for exploratory without GO claim |
| `failedBullets` | string[] | Overall |
| `mergeCriteriaRef` | string | Doc path |

### LiveSelectionConstants (read-only echo)

| Field | Source |
|-------|--------|
| `compositeThreshold` | `config.COMPOSITE_THRESHOLD` |
| `weights` | current WEIGHT_* |

**Never written back by calibration tooling.**

## State transitions

```text
validate config
  → [search] evaluate IS per candidate → rank → select top-N
  → [baseline-only] skip IS
  → evaluate OOS (go_evidence rules if packageIntent requires)
  → compute verdicts
  → write calibration report (+ child WF reports)
  → exit (no config.py mutation)
```

## Relationships

- CalibrationReport **references** Walk-Forward OOSReport paths (022 schema)  
- CandidateSpec **does not** mutate LiveSelectionConstants  
- Merge criteria doc is external; report stores `mergeCriteriaRef`
