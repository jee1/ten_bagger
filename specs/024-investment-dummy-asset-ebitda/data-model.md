# Data Model: 024 Investment Dummy

**Spec**: [spec.md](./spec.md) · **Contracts**: [contracts/](./contracts/)

In-memory / test entities only for v1 (no new content JSON schema required).

---

## InvestmentDummyMetric

Machine-readable YoY comparison for one symbol at one decision point.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | `"available"` \| `"unavailable"` | yes | Availability of a valid growth comparison |
| `asset_growth_pct` | `float` \| `null` | when available | YoY total assets growth in **percent** |
| `ebitda_growth_pct` | `float` \| `null` | when available | YoY EBITDA growth in **percent** |
| `spread_pct` | `float` \| `null` | when available | `asset_growth_pct − ebitda_growth_pct` (**percentage points**) |
| `investment_dummy` | `bool` \| `null` | when available | `true` iff `asset_growth_pct > ebitda_growth_pct`; else `false` when available; `null` when unavailable |
| `prior_total_assets` | `float` \| `null` | optional audit | Echo inputs when useful for tests |
| `current_total_assets` | `float` \| `null` | optional audit | |
| `prior_ebitda` | `float` \| `null` | optional audit | |
| `current_ebitda` | `float` \| `null` | optional audit | |
| `reason` | `str` \| `null` | optional | Short unavailable reason (`missing_assets`, `zero_prior_assets`, `non_positive_ebitda`, …) |

### Validation / computation rules

1. Growth formula when computing available metrics:
   `(current − prior) / abs(prior) * 100`.
2. `status=unavailable` if any of: missing prior/current assets; prior assets
   `== 0`; missing either EBITDA; either EBITDA `≤ 0`; non-finite inputs.
3. When unavailable: `investment_dummy` must not drive penalty/label; prefer
   `investment_dummy=null` (or `false` with `status=unavailable` — contract
   mandates **no penalty/label**; tests should assert status first).
4. When available: `investment_dummy = (asset_growth_pct > ebitda_growth_pct)`
   strict; equal → `false`.
5. Deterministic: same inputs → identical outputs.

### State

```text
[inputs] → available | unavailable
available + asset > ebitda → investment_dummy=true
available + asset ≤ ebitda → investment_dummy=false
```

---

## CandidateAdjustment

Result of applying the investment-dummy factor on the **candidate** path.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `enabled` | `bool` | yes | Whether candidate module was enabled for this call |
| `applied` | `bool` | yes | `true` only when enabled ∧ available ∧ dummy true |
| `soft_penalty` | `float` | yes | Points subtracted; `INVESTMENT_DUMMY_SOFT_PENALTY` when applied, else `0` |
| `label` | `str` \| `null` | yes | `"investment_dummy"` when applied, else `null` |
| `composite_before` | `float` | yes | Composite entering adjustment |
| `composite_after` | `float` | yes | After soft penalty (when applied) |
| `metric` | InvestmentDummyMetric | yes | Underlying metric snapshot |

### Rules

1. `applied` implies `soft_penalty >= 15` and `label == "investment_dummy"`.
2. Flag OFF → `applied=false`, zero penalty, no label — even if metric would hit.
3. Additive with other signals: does not clear existing hard red-flag outcomes
   on the live path; does not modify `passes_red_flags`.
4. Metrics dict on `ScoreResult` (when wired) SHOULD include at least:
   `investment_dummy_status`, `asset_growth_pct`, `ebitda_growth_pct`,
   `spread_pct`, `investment_dummy`, and `red_flag_labels` containing
   `"investment_dummy"` when applied.

---

## Live Score Freeze Boundary (reference entity)

Not a mutable runtime object — documentation boundary for tests:

| Constant / surface | Expected after this feature |
|--------------------|-----------------------------|
| `COMPOSITE_THRESHOLD` | Unchanged (`70.0`) |
| `WEIGHT_SIZE` … `WEIGHT_MOMENTUM` | Unchanged |
| `passes_red_flags` | Same inputs → same bool; no investment-dummy branch |
| `ENABLE_INVESTMENT_DUMMY_CANDIDATE` | Default `False` |
| `INVESTMENT_DUMMY_SOFT_PENALTY` | `15.0` (new; candidate-only) |

---

## Relationships

```text
PeriodFundamentals (caller-supplied)
        │
        ▼
InvestmentDummyMetric ──► CandidateAdjustment ──► ScoreResult.metrics / composite
                                │
                                └── gated by ENABLE_INVESTMENT_DUMMY_CANDIDATE
```
