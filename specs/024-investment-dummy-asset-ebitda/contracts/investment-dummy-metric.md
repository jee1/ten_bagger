# Contract: InvestmentDummyMetric

**Feature**: `024-investment-dummy-asset-ebitda` · Issue #68  
**Producer**: `scripts/scoring/investment_dummy.py` → `compute_investment_dummy_metric`  
**Consumers**: candidate adjustment, unit tests, optional analysis/reasoning

## Units

| Field | Unit |
|-------|------|
| `asset_growth_pct` | percent (%) |
| `ebitda_growth_pct` | percent (%) |
| `spread_pct` | percentage points (pp) = asset − ebitda |

## Growth formula

When inputs are valid for `status=available`:

```text
growth_pct = (current - prior) / abs(prior) * 100
```

## Fields

| Name | Type | Semantics |
|------|------|-----------|
| `status` | `"available"` \| `"unavailable"` | Valid comparison possible? |
| `asset_growth_pct` | number \| null | YoY total assets growth % |
| `ebitda_growth_pct` | number \| null | YoY EBITDA growth % |
| `spread_pct` | number \| null | `asset_growth_pct - ebitda_growth_pct` |
| `investment_dummy` | boolean \| null | `true` iff available and `asset_growth_pct > ebitda_growth_pct` |
| `reason` | string \| null | Optional unavailable code |

## Availability gate

`available` only if all hold:

1. `prior_total_assets` and `current_total_assets` are finite numbers
2. `prior_total_assets != 0`
3. `prior_ebitda` and `current_ebitda` are finite numbers
4. `prior_ebitda > 0` and `current_ebitda > 0`

Otherwise `status=unavailable` — **neutral**: no soft penalty, no
`investment_dummy` label.

## Boolean rule

- Strict inequality only: equal growth → `investment_dummy=false`
- Both-negative growth still compared numerically when available

## Determinism

Identical numeric inputs → identical outputs (stable rounding: recommend
`round(..., 6)` or leave full float and compare with `pytest.approx` in tests).

## Non-goals

- Sector carve-outs
- Hard universe exclude
- Silent null→0 growth coercion
