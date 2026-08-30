# Data Model: Pick Forward-Return Ledger

**Feature**: `019-pick-forward-return-ledger`  
**Date**: 2026-08-30  
**Schemas**: `scripts/schema/ledger.schema.json`, `scripts/schema/performance-bundle.schema.json` (promoted/extended from drafts — see plan)

## Entity overview

```text
DailyPickRecord (content/daily/*.json) ──read-only──► LedgerSnapshot
        │                                                    │
        │                                                    ├── entries[] (pick | no_pick)
        │                                                    │
        └── pick rows only ──► PerformanceMeasurement[] ─────┘
                                    (per horizonId)
PriceObservation (OHLCV ≤ asOfDate) ──► entry/exit/benchmark
RunMeta ──► attached to performance bundle root
```

---

## DailyPickRecord (input, immutable for this feature)

| Field | Type | Notes |
|-------|------|-------|
| `date` | `YYYY-MM-DD` | Treated as `pickDate` |
| `market` | `KR` \| `US` | |
| `status` | `pick` \| `no_pick` | |
| `stock.symbol` | string | Present when `pick`; measurement identity |
| `scores.version` | number | Copied to ledger as `scoreVersion` string (e.g. `"2"`) |

**Validation**: Existing `daily-entry.schema.json` via current `validate:content`. Corrupt file → whole regenerate fails (FR-018).

**Eligibility**: Include only if `date ≤ asOfDate`. Exclude `date > asOfDate` (FR-027).

---

## LedgerSnapshot

**Persistence**: `content/ledger/{market}.json`

| Field | Type | Required | Rules |
|-------|------|----------|-------|
| `schemaVersion` | string | yes | Const after promote (e.g. `"0.1.0"`) |
| `market` | `KR` \| `US` | yes | Must match filename market |
| `asOfDate` | `YYYY-MM-DD` | yes | Explicit regenerate arg |
| `entries` | `LedgerEntry[]` | yes | May be `[]` |

### LedgerEntry

| Field | Type | Required | Rules |
|-------|------|----------|-------|
| `pickDate` | `YYYY-MM-DD` | yes | From daily `date` |
| `symbol` | string | yes if `pick` | Empty/absent policy: for `no_pick` use `""` or omit — **prefer** required string with `""` for `no_pick` for schema simplicity |
| `status` | `pick` \| `no_pick` | yes | |
| `scoreVersion` | string | no | From daily scores.version |
| `notes` | string | no | Optional |

**State**: No lifecycle beyond replace-on-success. `no_pick` rows never spawn performance measurements (FR-014).

---

## PerformanceBundle

**Persistence**: `content/performance/{market}.json`

| Field | Type | Required | Rules |
|-------|------|----------|-------|
| `schemaVersion` | string | yes | Const |
| `market` | `KR` \| `US` | yes | |
| `asOfDate` | `YYYY-MM-DD` | yes | Same cut as ledger |
| `runMeta` | object | yes | See below |
| `measurements` | `PerformanceMeasurement[]` | yes | May be `[]` |

### RunMeta

| Field | Type | Required | Rules |
|-------|------|----------|-------|
| `provider` | string | yes | e.g. `"yfinance"` |
| `priceAdjustment` | string | yes | e.g. `"adjusted_preferred"` \| `"unadjusted_fallback"` |
| `generatedAt` | string (ISO-8601) | yes | Metadata only; not used for PIT cut |
| `asOfDate` | `YYYY-MM-DD` | yes | Echo of snapshot cut |

**Forbidden**: secrets, tokens, raw auth (FR-020).

### PerformanceMeasurement

| Field | Type | Required | Rules |
|-------|------|----------|-------|
| `market` | `KR` \| `US` | yes | |
| `pickDate` | `YYYY-MM-DD` | yes | |
| `symbol` | string | yes | Exact daily pick symbol (FR-026) |
| `horizonId` | enum | yes | `H20`\|`H60`\|`1M`\|`3M`\|`6M`\|`1Y`\|`3Y`\|`5Y` |
| `horizonDays` | integer | no | Session count for H20/H60 (`20`/`60`); omit or null for calendar |
| `benchmarkId` | string | yes | `KR-KOSPI` or `US-SPX` |
| `completionStatus` | enum | yes | `complete` \| `incomplete` |
| `incompleteReason` | string | when incomplete | Machine-readable code (see below) |
| `entryPrice` | number | when complete | Finite, `> 0` |
| `exitPrice` | number | when complete | Finite |
| `forwardReturn` | number | when complete | `(exit-entry)/entry`, no display rounding |
| `benchmarkReturn` | number | no | Present when benchmark complete |
| `benchmarkCompletionStatus` | enum | yes | `complete` \| `incomplete` |
| `benchmarkIncompleteReason` | string | when bench incomplete | |
| `survivorshipFlag` | enum | yes | `listed` \| `delisted` \| `unknown` |
| `asOfDate` | `YYYY-MM-DD` | yes | |

**Cardinality**: For each eligible `pick` day, emit **all eight** horizon rows (complete or incomplete). Never omit a horizon quietly (SC-002).

### incompleteReason codes (canonical)

| Code | Meaning |
|------|---------|
| `missing_entry` | No usable entry session/print |
| `invalid_entry` | Non-positive / non-finite entry |
| `missing_exit` | Horizon end not available ≤ `asOfDate` |
| `horizon_beyond_asof` | Required exit session after `asOfDate` |
| `insufficient_history` | Halt / IPO / thin series |
| `series_break` | Vendor gap / rename without map |

### benchmarkIncompleteReason codes

| Code | Meaning |
|------|---------|
| `missing_benchmark_series` | Index history unavailable |
| `missing_benchmark_exit` | Horizon not measurable for index |
| `horizon_beyond_asof` | Same PIT cut |

---

## Horizon

| `horizonId` | Kind | Exit rule |
|-------------|------|-----------|
| `H20` | session | 20th trading session after entry session |
| `H60` | session | 60th trading session after entry session |
| `1M` … `5Y` | calendar | Last usable session on/before `pickDate + span`, and ≤ `asOfDate` |

**Trading session**: Calendar day with usable regular-session reference for that symbol/market series (Q5).

---

## PriceObservation (ephemeral)

Not persisted as system of record. Fields used in compute: `sessionDate`, `open`, `close`, `adjOpen?`, `adjClose?`. Eligible iff `sessionDate ≤ asOfDate` and session is completed.

---

## State transitions

```text
[idle] --regenerate(asOfDate)--> [load dailies]
       --ok--> [compute all markets]
       --ok--> [write temps] --validate--> [atomic replace] --> [done]
       --fail anywhere--> [abort; prior artifacts unchanged]
```

No partial publish of a subset of markets on failure: either all intended outputs replace, or none (default: both KR and US).

## Relationships

- 1 DailyPickRecord (`pick`) → 1 LedgerEntry + 8 PerformanceMeasurements
- 1 DailyPickRecord (`no_pick`) → 1 LedgerEntry + 0 PerformanceMeasurements
- 1 LedgerSnapshot ↔ 1 PerformanceBundle share `market` + `asOfDate`
