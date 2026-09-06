# Data Model: 031-static-nav-verifiable-perf

## StaticNavState

| Field | Type | Notes |
|-------|------|-------|
| lang | `'ko' \| 'en'` | from `?lang=`; default `ko` |
| year | number | archive only; default KST now |
| month | number 1–12 | archive only |
| market | `'KR' \| 'US'` | performance only; default `KR` |

Parsed only in browser (and in unit tests). Build embeds data for all needed
values.

## MarketPerformanceView (extensions)

Additive fields (no schema change required for v1):

| Field | Type | Notes |
|-------|------|-------|
| priceAdjustment | string \| null | from `runMeta.priceAdjustment` |
| priceBasisValidation | `'complete' \| 'incomplete'` | v1 constant/`incomplete` until docs gate |
| cumulativeLabelKind | `'modeled_pick_chain'` | drives copy |
| perPickStatsLabel | boolean | ensure averages labeled per-pick |

## PriceBasisValidationNote

Markdown doc artifact (not content JSON):

- Symbol / pickDate / horizons covered
- Observed prices and `priceAdjustment`
- Conclusion: incomplete | complete
- Link from Methodology or architecture index

## Workflow artifact

`ledger.yml` gains deploy job consuming built `dist/` after content push —
no new content entity.
