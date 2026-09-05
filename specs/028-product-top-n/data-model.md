# Data Model: Product Top-N

## Entities

### DailyEntry (extended)

Existing daily publication document.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| …existing… | | | unchanged |
| `topCandidates` | `TopNCandidate[]` | optional | Omit when zero eligible scored; max length 5 |

### TopNCandidate

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `rank` | integer | yes | 1..k contiguous; k ≤ 5 |
| `symbol` | string | yes | Unique within list |
| `name` | LocalizedText | yes | `{ko, en}` |
| `exchange` | string | yes | Same as pick stock when available |
| `currency` | `KRW` \| `USD` | yes | Match universe meta |
| `scores` | TopNScores | yes | Axis set for day’s score version |

### TopNScores

Subset of daily pick scores **without** requiring `threshold` on each row
(threshold remains on day-level `scores` for pick/no_pick).

| Field | Type | Required |
|-------|------|----------|
| `composite` | number | yes |
| `size` | number | yes (v2+) |
| `growth` | number | yes |
| `valuation` | number | yes |
| `entry` | number | yes (v2+) |
| `momentum` | number | yes |
| `quality` | number | yes |
| `version` | integer | optional | Prefer day-level; may omit if identical |

## Validation Rules

1. If `topCandidates` present: `1 ≤ length ≤ 5`
2. Ranks equal `1..length` exactly (permutation of contiguous ints)
3. Symbols unique
4. Ordered by rank ascending in file (rank i at index i-1)
5. Sort integrity (producer): composite desc, symbol asc; validator MAY check
   adjacent composites are non-increasing
6. If `status === "pick"` and `topCandidates` present:
   `topCandidates[0].rank === 1` and `topCandidates[0].symbol === stock.symbol`
7. Historical entries without `topCandidates` remain valid

## Relationships

- Rank 1 on pick days **is** the published pick (same symbol)
- Day-level `scores` / `reasoning` remain pick-only (or zeroed no_pick scores)
- Top-N rows do **not** carry reasoning prose (v1)

## State / lifecycle

```text
screen all eligible → sort → select_pick(threshold)?
  ├─ pick + topCandidates[:5]
  ├─ no_pick + topCandidates[:5]  (if any scored)
  └─ no_pick, omit topCandidates  (zero scored)
```
