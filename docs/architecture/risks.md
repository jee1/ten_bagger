# Four-axis risk check (Performance Loop)

Concise gate for Epic #74 — not a full STRIDE model.

## 1. Data contamination

| Risk | Mitigation |
|------|------------|
| Training/evaluation leakage across walk-forward folds | ADR 0003 rolling OOS; disclose any reused periods |
| Mixing adjusted/unadjusted prices silently | ADR 0002 documents adjusted preference + provider assumption |
| Rewriting historical daily picks for metrics | Forbidden by default (ADR 0001 additive) |

## 2. Look-ahead

| Risk | Mitigation |
|------|------------|
| Using prices after decision/as-of | ADR 0002 entry = next session after pickDate; asOfDate bounds |
| Universe membership known only ex-post | Prefer point-in-time listings; document gaps as `unknown` |

## 3. Overfitting

| Risk | Mitigation |
|------|------------|
| Tuning Score v3 on the same window used for GO | ADR 0004 requires OOS evidence; analysis ≠ merge |
| Horizon shopping | Fixed H20 primary / H60 secondary (ADR 0003) |

## 4. Operational failure

| Risk | Mitigation |
|------|------------|
| Silent CI/provider failure | Failure Issues mandatory; Slack optional |
| Content/history growth slowing builds | Monitor; capacity redesign out of docs phase — note only |
| Draft schema mistaken for enforced contract | `*.draft.json` + `$comment`; unwired until #63+ |

## Capacity / growth note

Daily JSON history and future ledger/performance files will grow repository and
CI artifact size. This docs phase records the pressure; redesign (compaction,
artifact store) is **out of scope** until a dedicated issue/ADR.
