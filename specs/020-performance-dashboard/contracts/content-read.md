# Contract: content read paths (performance UI)

**Feature**: `020-performance-dashboard`

## Paths (read-only)

| Path | Schema | Writer | Reader (this feature) |
|------|--------|--------|------------------------|
| `content/performance/KR.json` | `performance-bundle.schema.json` | `regenerate_ledger.py` (#63) only | `performanceLoad` / `/performance?market=KR` |
| `content/performance/US.json` | same | same | `/performance?market=US` |
| `content/ledger/**` | ledger schema | #63 only | **Not required** for MVP page |
| `content/daily/**` | daily schema | daily job | **Must not change** |

## Invariants

1. UI / build MUST NOT create, update, or delete ledger/performance/daily files.
2. Missing performance file ⇒ `null` load ⇒ market empty state; build succeeds.
3. Present file MUST already pass `validate:content` in CI before merge of
   content changes; UI still fail-closes on unexpected shape.
4. Display aggregation is ephemeral (view model only); never commit derived
   aggregates as new SoT files in this feature.

## Types

Consume `PerformanceBundle` / related types from
`src/lib/content-types.generated.ts` (codegen). Do not hand-edit generated
types; schema changes belong to #63 follow-ups if needed.
