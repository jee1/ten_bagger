# Contract: ReadinessReport (Issue #91)

Informal contract for search `go_evidence` eligibility (may stay unschematized until validate:content wires it).

## Fields

| Field | Type | Notes |
|-------|------|-------|
| asOfDate | string (YYYY-MM-DD) | Measurement cut |
| markets | string[] | e.g. `["KR","US"]` |
| status | `"ready"` \| `"not_ready"` | |
| h20CompletePickDays | int | Count of H20-complete ledger pick days in scope |
| h20CompleteAlignedPickDays | int | Ledger pick days that fall on walk-forward decision sessions |
| proposedIs | `{startDate,endDate}` \| null | |
| proposedOos | `{startDate,endDate}` \| null | Disjoint from IS |
| projectedOosPickDays | int \| null | Disjoint OOS decision sessions projected from `oosFoldSpec` on the carve |
| reasons | string[] | Why not_ready / notes |
| generatedAt | string | Deterministic preferred |

## Invariants

- `ready` ⇒ proposed IS/OOS disjoint and `projectedOosPickDays >= 20`
- `not_ready` ⇒ MUST NOT authorize live Score v3 merge
- Identical inputs ⇒ identical report (modulo documented clock fields if any — prefer clock-free)
